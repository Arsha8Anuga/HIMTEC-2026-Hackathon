package service

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/llm"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/DATA-DOG/go-sqlmock"
)

func TestUnknownNumbers(t *testing.T) {
	allowed := `{"berat_kg":8.2,"tanggal":"2026-11-07","umur_bulan":11}`
	if bad := unknownNumbers("Berat 8,2 kg pada 7 November 2026, umur 11 bulan.", allowed); len(bad) != 0 {
		t.Fatalf("angka dari data ditolak: %v", bad)
	}
	if bad := unknownNumbers("Beri 3 butir telur dan 500 ml susu.", allowed); len(bad) != 2 {
		t.Fatalf("angka karangan lolos: %v", bad)
	}
	// Dates must not whitelist small numbers (bug found end to end: "3 butir telur" passed).
	withDates := `{"tanggal":"2026-03-07","lahir":"2025-12-07"}`
	if bad := unknownNumbers("Beri 3 butir telur.", withDates); len(bad) != 1 {
		t.Fatalf("angka dari pecahan tanggal lolos: %v", bad)
	}
	if bad := unknownNumbers("Diukur 2026-03-07, lahir 7 Desember 2025.", withDates); len(bad) != 0 {
		t.Fatalf("tanggal dari data ditolak: %v", bad)
	}
	if bad := unknownNumbers("Ukur lagi 2026-04-07.", withDates); len(bad) != 1 {
		t.Fatalf("tanggal karangan lolos: %v", bad)
	}
}

// Synthetic protocol fixtures, not clinical values.
func assistantService(t *testing.T, reply string, status int) (*Service, *string) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { db.Close() })
	mock.ExpectQuery("SELECT .* FROM measurements").WillReturnRows(
		sqlmock.NewRows([]string{"id", "child_id", "measured_at", "weight_kg", "length_height_cm", "position", "head_circumference_cm", "source", "note", "created_at"}).
			AddRow("11111111-2222-4333-8444-555555555555", "child", "2026-11-01", 8.2, 72.0, "recumbent", nil, "posyandu", nil, time.Now()))
	mock.ExpectQuery("SELECT .* FROM kpsp_results").WillReturnRows(sqlmock.NewRows([]string{"id"}))
	mock.ExpectQuery("SELECT .* FROM food_recalls").WillReturnRows(sqlmock.NewRows([]string{"id"}))
	mock.ExpectQuery("SELECT .* FROM kpsp_results").WillReturnRows(sqlmock.NewRows([]string{"id"}))
	eng := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"data":{"per_measurement":[],"level":"yellow","reasons":[{"code":"WEIGHT_NOT_GAINING","level":"yellow","evidence":{}}],"next_kpsp":{"questionnaire_age_months":9,"due":true},"diet":null},"error":null}`))
	}))
	t.Cleanup(eng.Close)
	var sent string
	ol := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Messages []llm.Message `json:"messages"`
			Stream   bool          `json:"stream"`
		}
		_ = json.NewDecoder(r.Body).Decode(&body)
		if r.URL.Path != "/api/chat" || body.Stream || len(body.Messages) < 2 {
			t.Errorf("permintaan ollama tidak sesuai: %s %+v", r.URL.Path, body)
		}
		sent = body.Messages[0].Content
		w.WriteHeader(status)
		_ = json.NewEncoder(w).Encode(map[string]any{"message": map[string]string{"role": "assistant", "content": reply}})
	}))
	t.Cleanup(ol.Close)
	s := &Service{Store: &repository.Store{DB: db}, Engine: engineclient.New(eng.URL), LLM: llm.New(ol.URL, "uji", 5*time.Second),
		Messages: map[string]Text{"WEIGHT_NOT_GAINING": {Title: "Berat tidak naik", Message: "Timbang {{name}} lagi bulan depan."}}}
	return s, &sent
}

func TestAssistantGroundedReply(t *testing.T) {
	s, sent := assistantService(t, "<think>rahasia</think>Berat Anisa 8,2 kg dan belum naik.", 200)
	reply, grounded, err := s.Assistant(context.Background(), model.Child{ID: "child", Name: "Anisa", Sex: "female", BirthDate: "2025-12-07"}, "Bagaimana berat anak saya?", nil)
	if err != nil || !grounded || reply != "Berat Anisa 8,2 kg dan belum naik." {
		t.Fatalf("got %q %v %v", reply, grounded, err)
	}
	if !strings.Contains(*sent, "Timbang Anisa lagi bulan depan.") || strings.Contains(*sent, "11111111") {
		t.Fatalf("konteks salah atau membocorkan id: %s", *sent)
	}
}

func TestAssistantRejectsInventedNumbers(t *testing.T) {
	s, _ := assistantService(t, "Beri 3 butir telur per hari.", 200)
	reply, grounded, err := s.Assistant(context.Background(), model.Child{ID: "child", Name: "Anisa", Sex: "female", BirthDate: "2025-12-07"}, "Makan apa?", nil)
	if err != nil || grounded || reply != Rejected {
		t.Fatalf("got %q %v %v", reply, grounded, err)
	}
}

func TestAssistantOllamaFailure(t *testing.T) {
	s, _ := assistantService(t, "", 500)
	_, _, err := s.Assistant(context.Background(), model.Child{ID: "child", Name: "Anisa", Sex: "female", BirthDate: "2025-12-07"}, "Halo", nil)
	if !errors.Is(err, ErrAssistantDown) {
		t.Fatalf("got %v", err)
	}
	if _, _, err := (&Service{}).Assistant(context.Background(), model.Child{}, "Halo", nil); !errors.Is(err, ErrAssistantOff) {
		t.Fatalf("got %v", err)
	}
}
