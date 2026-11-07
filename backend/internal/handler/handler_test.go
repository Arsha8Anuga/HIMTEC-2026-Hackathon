package handler

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

func TestValidationChild(t *testing.T) {
	good := model.ChildInput{Name: "Anak Demo", Sex: "female", BirthDate: service.Today()}
	if f := validChild(good); len(f) != 0 {
		t.Fatalf("unexpected fields: %+v", f)
	}
	good.Sex = "unknown"
	if validChild(good)["sex"] == "" {
		t.Fatal("unknown sex should be rejected")
	}
}

func TestEvaluationErrorClassification(t *testing.T) {
	tests := []struct {
		name   string
		err    error
		status int
		code   string
	}{
		{"database_failure", errors.New("database connection lost"), 500, "INTERNAL"},
		{"missing_database_row", sql.ErrNoRows, 404, "NOT_FOUND"},
		{"engine_transport", &engineclient.Failure{Operation: "POST /growth/evaluate", Err: errors.New("connection refused")}, 503, "ENGINE_UNAVAILABLE"},
		{"engine_route_missing", &engineclient.EngineError{Code: "NOT_FOUND", Message: "Endpoint tidak ditemukan"}, 503, "ENGINE_UNAVAILABLE"},
		{"engine_validation", &engineclient.Failure{Operation: "POST /growth/evaluate", Err: &engineclient.EngineError{Code: "VALIDATION_ERROR", Message: "Input tidak valid", Fields: map[string]string{"source": "invalid"}}}, 422, "VALIDATION_ERROR"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			r := httptest.NewRecorder()
			engineFailure(r, tt.err)
			var out envelope
			if err := json.Unmarshal(r.Body.Bytes(), &out); err != nil {
				t.Fatal(err)
			}
			if r.Code != tt.status || out.Error == nil || out.Error.Code != tt.code || out.Data != nil {
				t.Fatalf("unexpected response %d: %s", r.Code, r.Body.String())
			}
			if tt.code == "VALIDATION_ERROR" && out.Error.Fields["source"] != "invalid" {
				t.Fatal("validation field details lost")
			}
		})
	}
}
func TestValidationMeasurement(t *testing.T) {
	weight := 8.1
	cm := 70.2
	child := model.Child{BirthDate: "2026-01-01"}
	m := model.MeasurementInput{MeasuredAt: "2026-02-01", WeightKg: &weight, LengthHeightCm: &cm, Source: "posyandu"}
	if validMeasurement(m, child)["position"] == "" {
		t.Fatal("missing position accepted")
	}
	position := "recumbent"
	m.Position = &position
	if f := validMeasurement(m, child); len(f) != 0 {
		t.Fatalf("unexpected fields: %+v", f)
	}
	m.MeasuredAt = "2025-12-01"
	if validMeasurement(m, child)["measured_at"] == "" {
		t.Fatal("prebirth measurement accepted")
	}
}
func TestKPSPMissingAnswer(t *testing.T) {
	answers := make([]model.Answer, 10)
	for i := range answers {
		answers[i].ItemNo = i + 1
	}
	x := model.KpspInput{QuestionnaireAgeMonths: 9, AnsweredAt: service.Today(), Answers: answers}
	if validKpsp(x, model.Child{BirthDate: "2026-01-01"})["answers"] == "" {
		t.Fatal("nil answer should be rejected")
	}
}
func TestFoodRange(t *testing.T) {
	b := true
	zero := 0
	recall := time.Now().Local().AddDate(0, -1, 0).Format("2006-01-02")
	x := model.FoodRecallInput{RecallDate: recall, Breastfed: &b, FoodGroups: []string{}, MealCount: &zero}
	if validFood(x, model.Child{BirthDate: service.Today()})["recall_date"] == "" {
		t.Fatal("too young accepted")
	}
}
func TestEnvelopeJSON(t *testing.T) {
	r := httptest.NewRecorder()
	write(r, http.StatusOK, []string{})
	var out map[string]json.RawMessage
	if err := json.Unmarshal(r.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(out["data"]), "[]") {
		t.Fatal("expected []")
	}
	if string(out["error"]) != "null" {
		t.Fatal("expected error=null")
	}
}

func TestFoodAgeMatchesEngineDayBasedMonths(t *testing.T) {
	birth := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
	breastfed, meals := true, 3
	for _, tt := range []struct {
		days  int
		valid bool
	}{{182, false}, {183, true}, {730, true}, {731, false}} {
		x := model.FoodRecallInput{RecallDate: birth.AddDate(0, 0, tt.days).Format("2006-01-02"), Breastfed: &breastfed, FoodGroups: []string{}, MealCount: &meals}
		f := validFood(x, model.Child{BirthDate: birth.Format("2006-01-02")})
		if (len(f) == 0) != tt.valid {
			t.Fatalf("age %d days: valid=%v fields=%v", tt.days, tt.valid, f)
		}
	}
}

func TestKpspCannotPrecedeBirth(t *testing.T) {
	yes := true
	answers := make([]model.Answer, 10)
	for i := range answers {
		answers[i] = model.Answer{ItemNo: i + 1, Answer: &yes}
	}
	x := model.KpspInput{QuestionnaireAgeMonths: 9, AnsweredAt: "2026-01-01", Answers: answers}
	if validKpsp(x, model.Child{BirthDate: "2026-01-02"})["answered_at"] == "" {
		t.Fatal("pre-birth KPSP accepted")
	}
	x.AnsweredAt = "2026-01-02"
	if f := validKpsp(x, model.Child{BirthDate: "2026-01-02"}); len(f) != 0 {
		t.Fatalf("birth-date boundary rejected: %v", f)
	}
}

func TestParentCannotBeSelectedThroughPublicJSON(t *testing.T) {
	h := (&Handler{Svc: &service.Service{}}).Routes()
	r := httptest.NewRecorder()
	h.ServeHTTP(r, httptest.NewRequest(http.MethodPost, "/api/v1/children", strings.NewReader(`{"name":"Demo","sex":"female","birth_date":"2026-01-01","parent_id":"00000000-0000-4000-8000-000000000002"}`)))
	if r.Code != 422 {
		t.Fatalf("parent_id must be rejected: %d %s", r.Code, r.Body.String())
	}
}
