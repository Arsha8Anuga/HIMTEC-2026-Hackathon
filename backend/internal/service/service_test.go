package service

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/DATA-DOG/go-sqlmock"
)

// The numbers below are synthetic protocol fixtures, not clinical examples.
func TestGrowthSkipsMissingOptionalMeasurements(t *testing.T) {
	for _, indicator := range []string{"wfa", "lhfa", "hcfa", "wfl_wfh"} {
		t.Run(indicator, func(t *testing.T) {
			db, mock, err := sqlmock.New()
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			mock.ExpectQuery("SELECT .* FROM measurements WHERE child_id=").WithArgs("child", repository.DemoParentID).WillReturnRows(
				sqlmock.NewRows([]string{"id", "child_id", "measured_at", "weight_kg", "length_height_cm", "position", "head_circumference_cm", "source", "note", "created_at"}).
					AddRow("missing", "child", "2026-02-01", 8.0, nil, nil, nil, "posyandu", nil, time.Now()).
					AddRow("complete", "child", "2026-01-01", 7.0, 70.0, "recumbent", 40.0, "posyandu", nil, time.Now()))
			mock.ExpectQuery("SELECT .* FROM kpsp_results WHERE child_id=").WithArgs("child", repository.DemoParentID).WillReturnRows(sqlmock.NewRows([]string{"id"}))
			mock.ExpectQuery("SELECT .* FROM food_recalls WHERE child_id=").WithArgs("child", repository.DemoParentID, Today()).WillReturnRows(sqlmock.NewRows([]string{"id"}))
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				if r.URL.Path == "/growth/evaluate" {
					_, _ = w.Write([]byte(`{"data":{"per_measurement":[{"id":"missing","age_days":31,"corrected_length_cm":null,"z":{},"flags":[]},{"id":"complete","age_days":0,"corrected_length_cm":70,"z":{"wfa":0,"lhfa":0,"hcfa":0,"wfl_wfh":0},"flags":[]}],"level":"green","reasons":[],"next_kpsp":null,"diet":null},"error":null}`))
					return
				}
				wantIndicator := map[string]string{"wfl_wfh": "wfl"}[indicator]
				if wantIndicator == "" {
					wantIndicator = indicator
				}
				if r.URL.Path != "/reference" || r.URL.Query().Get("indicator") != wantIndicator {
					t.Errorf("unexpected reference request: %s", r.URL)
				}
				_, _ = w.Write([]byte(`{"data":{"x":[],"sd_neg3":[],"sd_neg2":[],"median":[],"sd_pos2":[],"sd_pos3":[]},"error":null}`))
			}))
			defer srv.Close()
			s := &Service{Store: &repository.Store{DB: db}, Engine: engineclient.New(srv.URL)}
			growth, err := s.Growth(context.Background(), model.Child{ID: "child", Sex: "female", BirthDate: "2026-01-01"}, indicator)
			if err != nil {
				t.Fatal(err)
			}
			b, err := json.Marshal(growth)
			if err != nil {
				t.Fatal(err)
			}
			var out struct {
				Points []struct {
					ID    string   `json:"measurement_id"`
					X     *float64 `json:"x"`
					Value *float64 `json:"value"`
				} `json:"points"`
			}
			if err := json.Unmarshal(b, &out); err != nil {
				t.Fatal(err)
			}
			want := 1
			if indicator == "wfa" {
				want = 2
			}
			if len(out.Points) != want {
				t.Fatalf("expected %d points, got %s", want, b)
			}
			for _, p := range out.Points {
				if p.X == nil || p.Value == nil {
					t.Fatalf("null coordinate escaped: %s", b)
				}
			}
			if out.Points[0].ID != "complete" {
				t.Fatalf("points not sorted by x: %s", b)
			}
			if err := mock.ExpectationsWereMet(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestScoreKpspRequiresExplicitScore(t *testing.T) {
	for _, tt := range []struct {
		name, body string
		valid      bool
	}{
		{"missing", `{"data":{"result":"penyimpangan"},"error":null}`, false},
		{"null", `{"data":{"yes_count":null,"result":"penyimpangan"},"error":null}`, false},
		{"zero", `{"data":{"yes_count":0,"result":"penyimpangan"},"error":null}`, true},
	} {
		t.Run(tt.name, func(t *testing.T) {
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { _, _ = w.Write([]byte(tt.body)) }))
			defer srv.Close()
			s := &Service{Engine: engineclient.New(srv.URL)}
			_, _, err := s.ScoreKpsp(context.Background(), model.KpspInput{})
			var failure *engineclient.Failure
			if tt.valid && err != nil {
				t.Fatal(err)
			}
			if !tt.valid && !errors.As(err, &failure) {
				t.Fatalf("expected engine protocol error, got %v", err)
			}
		})
	}
}

// Contract v0.7: Go picks wfl (< 731 days) or wfh from today's age, over the whole WHO table domain in cm.
func TestGrowthPicksLengthOrHeightTableByAge(t *testing.T) {
	for _, tc := range []struct{ birth, indicator, from, to string }{
		{daysAgo(730), "wfl", "45", "110"},
		{daysAgo(731), "wfh", "65", "120"},
	} {
		db, mock, err := sqlmock.New()
		if err != nil {
			t.Fatal(err)
		}
		mock.ExpectQuery("SELECT .* FROM measurements").WillReturnRows(sqlmock.NewRows([]string{"id"}))
		mock.ExpectQuery("SELECT .* FROM kpsp_results").WillReturnRows(sqlmock.NewRows([]string{"id"}))
		mock.ExpectQuery("SELECT .* FROM food_recalls").WillReturnRows(sqlmock.NewRows([]string{"id"}))
		var got string
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path == "/growth/evaluate" {
				_, _ = w.Write([]byte(`{"data":{"per_measurement":[],"level":"green","reasons":[],"next_kpsp":null,"diet":null},"error":null}`))
				return
			}
			q := r.URL.Query()
			got = q.Get("indicator") + " " + q.Get("x_from") + " " + q.Get("x_to")
			_, _ = w.Write([]byte(`{"data":{"x":[],"sd_neg3":[],"sd_neg2":[],"median":[],"sd_pos2":[],"sd_pos3":[]},"error":null}`))
		}))
		s := &Service{Store: &repository.Store{DB: db}, Engine: engineclient.New(srv.URL)}
		out, err := s.Growth(context.Background(), model.Child{ID: "child", Sex: "male", BirthDate: tc.birth}, "wfl_wfh")
		srv.Close()
		db.Close()
		if err != nil {
			t.Fatal(err)
		}
		if want := tc.indicator + " " + tc.from + " " + tc.to; got != want {
			t.Fatalf("birth %s: reference %q, want %q", tc.birth, got, want)
		}
		if out["indicator"] != "wfl_wfh" || out["x_unit"] != "cm" {
			t.Fatalf("public shape changed: %v", out)
		}
	}
}

func TestNextKpspReviewStatus(t *testing.T) {
	ten := `[{"item_no":1},{"item_no":2},{"item_no":3},{"item_no":4},{"item_no":5},{"item_no":6},{"item_no":7},{"item_no":8},{"item_no":9},{"item_no":10}]`
	for _, tc := range []struct {
		name, body string
		ok         bool
	}{
		{"labelled", `{"questionnaire_age_months":15,"review_status":"transcription_unreviewed","items":` + ten + `}`, true},
		{"unavailable", `{"questionnaire_age_months":9,"review_status":"unavailable","items":[]}`, true},
		{"unknown status", `{"questionnaire_age_months":15,"review_status":"verified","items":` + ten + `}`, false},
		{"labelled without items", `{"questionnaire_age_months":15,"review_status":"transcription_unreviewed","items":[]}`, false},
		{"unavailable with items", `{"questionnaire_age_months":9,"review_status":"unavailable","items":` + ten + `}`, false},
		{"short form", `{"questionnaire_age_months":15,"review_status":"transcription_unreviewed","items":[{"item_no":1}]}`, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			db, mock, err := sqlmock.New()
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			mock.ExpectQuery("SELECT .* FROM measurements").WillReturnRows(sqlmock.NewRows([]string{"id"}))
			mock.ExpectQuery("SELECT .* FROM kpsp_results").WillReturnRows(sqlmock.NewRows([]string{"id"}))
			mock.ExpectQuery("SELECT .* FROM food_recalls").WillReturnRows(sqlmock.NewRows([]string{"id"}))
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/growth/evaluate" {
					_, _ = w.Write([]byte(`{"data":{"per_measurement":[],"level":"green","reasons":[],"next_kpsp":{"questionnaire_age_months":15,"due":true},"diet":null},"error":null}`))
					return
				}
				_, _ = w.Write([]byte(`{"data":` + tc.body + `,"error":null}`))
			}))
			defer srv.Close()
			s := &Service{Store: &repository.Store{DB: db}, Engine: engineclient.New(srv.URL)}
			out, err := s.NextKpsp(context.Background(), model.Child{ID: "child", Sex: "male", BirthDate: "2025-08-01"})
			if !tc.ok {
				if err == nil {
					t.Fatalf("accepted %s", tc.body)
				}
				return
			}
			if err != nil {
				t.Fatal(err)
			}
			if label, _ := out["review_label"].(string); label == "" || out["review_status"] == nil {
				t.Fatalf("missing review label: %v", out)
			}
		})
	}
}

func daysAgo(n int) string {
	t, _ := ParseDate(Today())
	return t.AddDate(0, 0, -n).Format("2006-01-02")
}
