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
			mock.ExpectQuery("SELECT .* FROM food_recalls WHERE child_id=").WithArgs("child", repository.DemoParentID).WillReturnRows(sqlmock.NewRows([]string{"id"}))
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.Header().Set("Content-Type", "application/json")
				if r.URL.Path == "/growth/evaluate" {
					_, _ = w.Write([]byte(`{"data":{"per_measurement":[{"id":"missing","age_days":31,"corrected_length_cm":null,"z":{},"flags":[]},{"id":"complete","age_days":0,"corrected_length_cm":70,"z":{"wfa":0,"lhfa":0,"hcfa":0,"wfl_wfh":0},"flags":[]}],"level":"green","reasons":[],"next_kpsp":null,"diet":null},"error":null}`))
					return
				}
				if r.URL.Path != "/reference" || r.URL.Query().Get("indicator") != indicator {
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
