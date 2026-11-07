package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

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
	if validKpsp(x)["answers"] == "" {
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
