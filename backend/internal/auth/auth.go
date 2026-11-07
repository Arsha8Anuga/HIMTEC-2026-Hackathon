// Package auth implements explicitly enabled, local-only OTP dummy login.
package auth

import (
	"context"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"math/big"
	"net/mail"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
)

var uuidPattern = regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
var ErrInvalid = errors.New("kode atau sesi tidak valid")
var ErrRate = errors.New("permintaan terlalu sering; coba lagi nanti")
var ErrInput = errors.New("input tidak valid")

type User struct {
	ID    string `json:"id"`
	Name  string `json:"name"`
	Email string `json:"email"`
	Role  string `json:"role"`
}
type Challenge struct {
	ID        string `json:"challenge_id"`
	ExpiresIn int    `json:"expires_in"`
}
type Login struct {
	Token     string `json:"access_token"`
	TokenType string `json:"token_type"`
	ExpiresIn int    `json:"expires_in"`
	User      User   `json:"user"`
}
type Service struct {
	DB      *sql.DB
	key     [32]byte
	Now     func() time.Time
	Deliver func(string, string, string)
}

func New(db *sql.DB, deliver func(string, string, string)) (*Service, error) {
	s := &Service{DB: db, Now: time.Now, Deliver: deliver}
	_, err := rand.Read(s.key[:])
	return s, err
}
func (s *Service) codeHash(id, code string) string {
	h := hmac.New(sha256.New, s.key[:])
	h.Write([]byte(id + ":" + code))
	return hex.EncodeToString(h.Sum(nil))
}
func tokenHash(token string) string {
	h := sha256.Sum256([]byte(token))
	return hex.EncodeToString(h[:])
}
func Email(value string) (string, error) {
	value = strings.ToLower(strings.TrimSpace(value))
	a, e := mail.ParseAddress(value)
	if e != nil || a.Address != value || len(value) > 254 || strings.ContainsAny(value, "\r\n") {
		return "", ErrInput
	}
	return value, nil
}
func audit(ctx context.Context, tx *sql.Tx, user, action string, now time.Time) error {
	id, err := repository.UUID()
	if err != nil {
		return err
	}
	var uid any
	if user != "" {
		uid = user
	}
	_, err = tx.ExecContext(ctx, `INSERT INTO audit_logs(id,user_id,action,created_at) VALUES($1,$2,$3,$4)`, id, uid, action, now)
	return err
}
func (s *Service) Request(ctx context.Context, purpose, name, email string) (Challenge, error) {
	var out Challenge
	email, err := Email(email)
	if err != nil {
		return out, err
	}
	name = strings.TrimSpace(name)
	if purpose != "login" && purpose != "register" {
		return out, ErrInput
	}
	if purpose == "register" && (utf8.RuneCountInString(name) < 1 || utf8.RuneCountInString(name) > 60) {
		return out, ErrInput
	}
	id, err := repository.UUID()
	if err != nil {
		return out, err
	}
	n, err := rand.Int(rand.Reader, big.NewInt(1000000))
	if err != nil {
		return out, err
	}
	code := fmt.Sprintf("%06d", n.Int64())
	now := s.Now().UTC().Truncate(time.Microsecond)
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	if _, err = tx.ExecContext(ctx, `SELECT pg_advisory_xact_lock(hashtext($1))`, "otp:"+email); err != nil {
		return out, err
	}
	var recent, hour int
	if err = tx.QueryRowContext(ctx, `SELECT count(*) FILTER (WHERE created_at>$2),count(*) FROM otp_codes WHERE email=$1 AND created_at>$3`, email, now.Add(-time.Minute), now.Add(-time.Hour)).Scan(&recent, &hour); err != nil {
		return out, err
	}
	if recent > 0 || hour >= 5 {
		return out, ErrRate
	}
	var uid, role string
	var active bool
	err = tx.QueryRowContext(ctx, `SELECT id,role,is_active FROM users WHERE lower(email)=$1`, email).Scan(&uid, &role, &active)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return out, err
	}
	eligible := (purpose == "register" && errors.Is(err, sql.ErrNoRows)) || (purpose == "login" && err == nil && active && role == "parent")
	if _, err = tx.ExecContext(ctx, `UPDATE otp_codes SET used_at=$2 WHERE email=$1 AND used_at IS NULL`, email, now); err != nil {
		return out, err
	}
	hash := s.codeHash(id, code)
	if !eligible {
		hash = s.codeHash(id, "unavailable")
	}
	if _, err = tx.ExecContext(ctx, `INSERT INTO otp_codes(id,email,purpose,pending_name,code_hash,expires_at,created_at) VALUES($1,$2,$3,$4,$5,$6,$7)`, id, email, purpose, name, hash, now.Add(5*time.Minute), now); err != nil {
		return out, err
	}
	if err = audit(ctx, tx, "", "otp_requested", now); err != nil {
		return out, err
	}
	if err = tx.Commit(); err != nil {
		return out, err
	}
	if eligible && s.Deliver != nil {
		s.Deliver(email, id, code)
	}
	return Challenge{ID: id, ExpiresIn: 300}, nil
}
func (s *Service) Verify(ctx context.Context, id, code string) (Login, error) {
	var out Login
	if len(code) != 6 || !uuidPattern.MatchString(id) {
		return out, ErrInvalid
	}
	for _, r := range code {
		if r < '0' || r > '9' {
			return out, ErrInvalid
		}
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return out, err
	}
	defer tx.Rollback()
	var email, purpose, name, hash string
	var attempts int
	var expires time.Time
	var used sql.NullTime
	err = tx.QueryRowContext(ctx, `SELECT email,purpose,pending_name,code_hash,attempts,expires_at,used_at FROM otp_codes WHERE id=$1 FOR UPDATE`, id).Scan(&email, &purpose, &name, &hash, &attempts, &expires, &used)
	if errors.Is(err, sql.ErrNoRows) {
		return out, ErrInvalid
	}
	if err != nil {
		return out, err
	}
	now := s.Now().UTC().Truncate(time.Microsecond)
	if used.Valid || attempts >= 5 || !now.Before(expires) {
		return out, ErrInvalid
	}
	if subtle.ConstantTimeCompare([]byte(hash), []byte(s.codeHash(id, code))) != 1 {
		if _, err = tx.ExecContext(ctx, `UPDATE otp_codes SET attempts=attempts+1 WHERE id=$1`, id); err != nil {
			return out, err
		}
		if err = audit(ctx, tx, "", "otp_rejected", now); err != nil {
			return out, err
		}
		if err = tx.Commit(); err != nil {
			return out, err
		}
		return out, ErrInvalid
	}
	var user User
	if purpose == "register" {
		uid, e := repository.UUID()
		if e != nil {
			return out, e
		}
		err = tx.QueryRowContext(ctx, `INSERT INTO users(id,name,email,role,is_active) VALUES($1,$2,$3,'parent',true) ON CONFLICT DO NOTHING RETURNING id,name,email,role`, uid, name, email).Scan(&user.ID, &user.Name, &user.Email, &user.Role)
	} else {
		err = tx.QueryRowContext(ctx, `SELECT id,name,email,role FROM users WHERE lower(email)=$1 AND role='parent' AND is_active`, email).Scan(&user.ID, &user.Name, &user.Email, &user.Role)
	}
	if errors.Is(err, sql.ErrNoRows) {
		return out, ErrInvalid
	}
	if err != nil {
		return out, err
	}
	if _, err = tx.ExecContext(ctx, `UPDATE otp_codes SET used_at=$2 WHERE id=$1`, id, now); err != nil {
		return out, err
	}
	b := make([]byte, 32)
	if _, err = rand.Read(b); err != nil {
		return out, err
	}
	token := hex.EncodeToString(b)
	if _, err = tx.ExecContext(ctx, `INSERT INTO auth_sessions(token_hash,user_id,expires_at,created_at) VALUES($1,$2,$3,$4)`, tokenHash(token), user.ID, now.Add(24*time.Hour), now); err != nil {
		return out, err
	}
	if err = audit(ctx, tx, user.ID, "login_succeeded", now); err != nil {
		return out, err
	}
	if err = tx.Commit(); err != nil {
		return out, err
	}
	return Login{Token: token, TokenType: "Bearer", ExpiresIn: 86400, User: user}, nil
}
func (s *Service) Lookup(ctx context.Context, token string) (User, error) {
	var u User
	if len(token) != 64 {
		return u, ErrInvalid
	}
	err := s.DB.QueryRowContext(ctx, `SELECT u.id,u.name,u.email,u.role FROM auth_sessions a JOIN users u ON u.id=a.user_id WHERE a.token_hash=$1 AND a.revoked_at IS NULL AND a.expires_at>$2 AND u.is_active AND u.role='parent'`, tokenHash(token), s.Now().UTC().Truncate(time.Microsecond)).Scan(&u.ID, &u.Name, &u.Email, &u.Role)
	if errors.Is(err, sql.ErrNoRows) {
		return u, ErrInvalid
	}
	return u, err
}
func (s *Service) Logout(ctx context.Context, token string) error {
	u, err := s.Lookup(ctx, token)
	if err != nil {
		return err
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	now := s.Now().UTC().Truncate(time.Microsecond)
	if _, err = tx.ExecContext(ctx, `UPDATE auth_sessions SET revoked_at=$2 WHERE token_hash=$1`, tokenHash(token), now); err != nil {
		return err
	}
	if err = audit(ctx, tx, u.ID, "logout", now); err != nil {
		return err
	}
	return tx.Commit()
}
