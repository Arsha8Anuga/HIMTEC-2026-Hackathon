package auth_test

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/auth"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/handler"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

func setup(t *testing.T) (*repository.Store, *auth.Service, map[string]string, *time.Time) {
	t.Helper()
	dsn := os.Getenv("BACKEND_TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("set BACKEND_TEST_DATABASE_URL for SQL authentication tests")
	}
	store, err := repository.Open(dsn)
	if err != nil {
		t.Fatal(err)
	}
	store.DB.SetMaxOpenConns(1)
	id, _ := repository.UUID()
	schema := "auth_test_" + strings.ReplaceAll(id, "-", "")
	if _, err = store.DB.Exec("CREATE SCHEMA " + schema); err != nil {
		t.Fatal(err)
	}
	if _, err = store.DB.Exec("SET search_path TO " + schema); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		store.DB.Exec("DROP SCHEMA " + schema + " CASCADE")
		store.DB.Exec("SET search_path TO public")
		store.DB.Close()
	})
	if err = store.Migrate(context.Background(), filepath.Join("..", "..", "migrations")); err != nil {
		t.Fatal(err)
	}
	codes := map[string]string{}
	a, err := auth.New(store.DB, func(email, id, code string) { codes[id] = code })
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().UTC()
	a.Now = func() time.Time { return now }
	return store, a, codes, &now
}
func register(t *testing.T, a *auth.Service, codes map[string]string, email string) auth.Login {
	t.Helper()
	c, err := a.Request(context.Background(), "register", "User Uji", email)
	if err != nil {
		t.Fatal(err)
	}
	out, err := a.Verify(context.Background(), c.ID, codes[c.ID])
	if err != nil {
		t.Fatal(err)
	}
	return out
}
func call(h http.Handler, method, path, token, body string) (int, map[string]json.RawMessage) {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	var out map[string]json.RawMessage
	json.Unmarshal(rec.Body.Bytes(), &out)
	return rec.Code, out
}
func TestOTPHTTPRegisterLoginAndIsolation(t *testing.T) {
	store, a, codes, _ := setup(t)
	h := (&handler.Handler{Auth: a, Svc: &service.Service{Store: store}, CORSOrigin: "http://localhost:5173"}).Routes()
	status, body := call(h, "POST", "/api/v1/auth/register", "", `{"name":"Alice","email":" ALICE@example.test "}`)
	if status != 202 {
		t.Fatalf("register: %d %s", status, body)
	}
	var c auth.Challenge
	json.Unmarshal(body["data"], &c)
	var fields map[string]json.RawMessage
	json.Unmarshal(body["data"], &fields)
	if len(fields) != 2 || fields["challenge_id"] == nil || fields["expires_in"] == nil {
		t.Fatal("OTP leaked into response")
	}
	status, body = call(h, "POST", "/api/v1/auth/verify", "", fmt.Sprintf(`{"challenge_id":%q,"code":%q}`, c.ID, codes[c.ID]))
	if status != 200 {
		t.Fatalf("verify: %d %s", status, body)
	}
	var alice auth.Login
	json.Unmarshal(body["data"], &alice)
	if alice.User.Email != "alice@example.test" || alice.User.Role != "parent" {
		t.Fatalf("user: %+v", alice.User)
	}
	bob := register(t, a, codes, "bob@example.test")
	status, body = call(h, "POST", "/api/v1/children", alice.Token, `{"name":"Anak Alice","sex":"female","birth_date":"2026-01-07"}`)
	if status != 201 {
		t.Fatalf("create child: %d %s", status, body)
	}
	var child struct {
		ID string `json:"id"`
	}
	json.Unmarshal(body["data"], &child)
	if status, _ = call(h, "GET", "/api/v1/children", "", ""); status != 401 {
		t.Fatalf("missing token: %d", status)
	}
	if status, _ = call(h, "GET", "/api/v1/children/"+child.ID, bob.Token, ""); status != 404 {
		t.Fatalf("cross-parent detail: %d", status)
	}
	if status, _ = call(h, "POST", "/api/v1/children/"+child.ID+"/measurements", bob.Token, `{"measured_at":"2026-11-07","weight_kg":8,"source":"home"}`); status != 404 {
		t.Fatalf("cross-parent write: %d", status)
	}
	status, body = call(h, "GET", "/api/v1/children", bob.Token, "")
	if status != 200 || string(body["data"]) != "[]" {
		t.Fatalf("bob list: %d %s", status, body)
	}
	// Concurrent requests must never change a shared parent ID.
	var wg sync.WaitGroup
	for i := 0; i < 12; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			token := alice.Token
			if i%2 == 1 {
				token = bob.Token
			}
			status, body := call(h, "GET", "/api/v1/children", token, "")
			if status != 200 {
				t.Errorf("list failed: %d", status)
				return
			}
			has := strings.Contains(string(body["data"]), child.ID)
			if has != (i%2 == 0) {
				t.Error("parent context leaked")
			}
		}(i)
	}
	wg.Wait()
	status, body = call(h, "GET", "/api/v1/auth/me", alice.Token, "")
	if status != 200 {
		t.Fatalf("me: %d %s", status, body)
	}
	if status, _ = call(h, "POST", "/api/v1/auth/logout", alice.Token, ""); status != 200 {
		t.Fatalf("logout: %d", status)
	}
	if status, _ = call(h, "GET", "/api/v1/children", alice.Token, ""); status != 401 {
		t.Fatalf("revoked session accepted: %d", status)
	}
	if status, _ = call(h, "GET", "/api/v1/auth/me", bob.Token, ""); status != 200 {
		t.Fatalf("other session revoked: %d", status)
	}
}
func TestOTPLimitsExpiryAndReplay(t *testing.T) {
	_, a, codes, now := setup(t)
	ctx := context.Background()
	c, err := a.Request(ctx, "register", "Uji", "limit@example.test")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = a.Request(ctx, "register", "Uji", "limit@example.test"); !errors.Is(err, auth.ErrRate) {
		t.Fatalf("resend not limited: %v", err)
	}
	wrong := "000000"
	if codes[c.ID] == wrong {
		wrong = "111111"
	}
	for i := 0; i < 5; i++ {
		if _, err = a.Verify(ctx, c.ID, wrong); !errors.Is(err, auth.ErrInvalid) {
			t.Fatalf("wrong code: %v", err)
		}
	}
	if _, err = a.Verify(ctx, c.ID, codes[c.ID]); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("attempt lock not enforced")
	}
	*now = now.Add(time.Minute + time.Second)
	newer, err := a.Request(ctx, "register", "Uji", "limit@example.test")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = a.Verify(ctx, c.ID, codes[c.ID]); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("old code accepted")
	}
	*now = now.Add(5 * time.Minute)
	if _, err = a.Verify(ctx, newer.ID, codes[newer.ID]); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("expired code accepted")
	}
	*now = now.Add(time.Second)
	c, err = a.Request(ctx, "register", "Uji", "limit@example.test")
	if err != nil {
		t.Fatal(err)
	}
	out, err := a.Verify(ctx, c.ID, codes[c.ID])
	if err != nil {
		t.Fatal(err)
	}
	if _, err = a.Verify(ctx, c.ID, codes[c.ID]); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("code reused")
	}
	// Login is independent of the registration route; advance resend window.
	*now = now.Add(time.Minute + time.Second)
	login, err := a.Request(ctx, "login", "", "limit@example.test")
	if err != nil {
		t.Fatal(err)
	}
	if _, err = a.Verify(ctx, login.ID, codes[login.ID]); err != nil {
		t.Fatal(err)
	}
	*now = now.Add(24 * time.Hour)
	if _, err = a.Lookup(ctx, out.Token); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("expired session accepted")
	}
}
func TestOTPUnknownDisabledAndHashes(t *testing.T) {
	store, a, codes, now := setup(t)
	ctx := context.Background()
	unknown, err := a.Request(ctx, "login", "", "missing@example.test")
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := codes[unknown.ID]; ok {
		t.Fatal("unknown account delivered code")
	}
	u := register(t, a, codes, "known@example.test")
	var hash string
	if err = store.DB.QueryRow(`SELECT token_hash FROM auth_sessions WHERE user_id=$1`, u.User.ID).Scan(&hash); err != nil {
		t.Fatal(err)
	}
	if hash == u.Token || len(hash) != 64 {
		t.Fatal("plaintext session stored")
	}
	var otpHash string
	if err = store.DB.QueryRow(`SELECT code_hash FROM otp_codes WHERE email='known@example.test'`).Scan(&otpHash); err != nil {
		t.Fatal(err)
	}
	if len(otpHash) != 64 {
		t.Fatal("OTP hash invalid")
	}
	if _, err = store.DB.Exec(`UPDATE users SET is_active=false WHERE id=$1`, u.User.ID); err != nil {
		t.Fatal(err)
	}
	if _, err = a.Lookup(ctx, u.Token); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("disabled user session accepted")
	}
	*now = now.Add(time.Minute + time.Second)
	c, err := a.Request(ctx, "login", "", "known@example.test")
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := codes[c.ID]; ok {
		t.Fatal("disabled user delivered code")
	}
	var count int
	if err = store.DB.QueryRow(`SELECT count(*) FROM audit_logs`).Scan(&count); err != nil || count < 2 {
		t.Fatalf("audit missing: %d %v", count, err)
	}
}
func TestOTPConcurrentVerifyOnlyOnce(t *testing.T) {
	_, a, codes, _ := setup(t)
	c, err := a.Request(context.Background(), "register", "Uji", "race@example.test")
	if err != nil {
		t.Fatal(err)
	}
	results := make(chan error, 2)
	for i := 0; i < 2; i++ {
		go func() { _, err := a.Verify(context.Background(), c.ID, codes[c.ID]); results <- err }()
	}
	successes := 0
	for i := 0; i < 2; i++ {
		err := <-results
		if err == nil {
			successes++
		} else if !errors.Is(err, auth.ErrInvalid) {
			t.Fatal(err)
		}
	}
	if successes != 1 {
		t.Fatalf("successful verifies=%d", successes)
	}
}
func TestEmailAndMissingAuthentication(t *testing.T) {
	for _, email := range []string{"bad", "Display <x@example.test>", "a@example.test\nBcc:x@example.test"} {
		if _, err := auth.Email(email); !errors.Is(err, auth.ErrInput) {
			t.Fatalf("invalid email accepted: %q", email)
		}
	}
	h := (&handler.Handler{Auth: &auth.Service{}}).Routes()
	for _, path := range []string{"/api/v1/children", "/api/v1/guides", "/api/v1/auth/me"} {
		if status, _ := call(h, "GET", path, "", ""); status != 401 {
			t.Fatalf("%s missing token=%d", path, status)
		}
	}
}

func TestOTPHourLimitAndRestart(t *testing.T) {
	store, a, codes, now := setup(t)
	ctx := context.Background()
	var last auth.Challenge
	for i := 0; i < 5; i++ {
		var err error
		last, err = a.Request(ctx, "register", "Uji", "hour@example.test")
		if err != nil {
			t.Fatal(err)
		}
		*now = now.Add(time.Minute + time.Second)
	}
	if _, err := a.Request(ctx, "register", "Uji", "hour@example.test"); !errors.Is(err, auth.ErrRate) {
		t.Fatalf("hour cap missing: %v", err)
	}
	restarted, err := auth.New(store.DB, nil)
	if err != nil {
		t.Fatal(err)
	}
	restarted.Now = a.Now
	if _, err := restarted.Verify(ctx, last.ID, codes[last.ID]); !errors.Is(err, auth.ErrInvalid) {
		t.Fatal("OTP from previous process still accepted")
	}
}
func TestRoleInjectionAndCors(t *testing.T) {
	h := (&handler.Handler{Auth: &auth.Service{}, CORSOrigin: "http://localhost:5173"}).Routes()
	if status, _ := call(h, "POST", "/api/v1/auth/register", "", `{"name":"Admin","email":"a@example.test","role":"admin"}`); status != 422 {
		t.Fatalf("role injection accepted: %d", status)
	}
	req := httptest.NewRequest("OPTIONS", "/api/v1/children", nil)
	req.Header.Set("Origin", "http://localhost:5173")
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	if rec.Code != 204 || !strings.Contains(rec.Header().Get("Access-Control-Allow-Headers"), "Authorization") {
		t.Fatalf("preflight failed: %d %s", rec.Code, rec.Header())
	}
}
