package handler

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
	"github.com/DATA-DOG/go-sqlmock"
)

const testChildID = "9b1d0c2e-0000-4000-8000-000000000001"
const testMeasurementID = "9b1d0c2e-0000-4000-8000-000000000002"
const testFoodID = "9b1d0c2e-0000-4000-8000-000000000003"

func childRow(birth string) *sqlmock.Rows {
	return sqlmock.NewRows([]string{"id", "name", "sex", "birth_date", "birth_weight_kg", "birth_length_cm", "is_preterm", "created_at"}).
		AddRow(testChildID, "Anak Fiktif", "female", birth, nil, nil, false, time.Now())
}

func measurementRow(day string) *sqlmock.Rows {
	return sqlmock.NewRows([]string{"id", "child_id", "measured_at", "weight_kg", "length_height_cm", "position", "head_circumference_cm", "source", "note", "created_at"}).
		AddRow(testMeasurementID, testChildID, day, 8.0, nil, nil, nil, "posyandu", nil, time.Now())
}

func foodRow(day string) *sqlmock.Rows {
	return sqlmock.NewRows([]string{"id", "child_id", "recall_date", "breastfed", "food_groups", "meal_count", "milk_feed_count", "created_at"}).
		AddRow(testFoodID, testChildID, day, true, []byte(`[]`), 3, nil, time.Now())
}

// Engine HTTP responses match the current Python router. SQL is mocked: this
// verifies handler/service integration, not a live PostgreSQL installation.
func TestSavedInputRemainsReadableWhenEngineRouteIsMissing(t *testing.T) {
	for _, kind := range []string{"measurements", "food-recalls"} {
		t.Run(kind, func(t *testing.T) {
			db, mock, err := sqlmock.New()
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			day := service.Today()
			now, _ := service.ParseDate(day)
			birth := now.AddDate(0, -9, 0).Format("2006-01-02")
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Method != http.MethodPost || r.URL.Path != "/engine/v1/growth/evaluate" {
					t.Errorf("unexpected engine request %s %s", r.Method, r.URL.Path)
				}
				var payload map[string]json.RawMessage
				if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
					t.Error(err)
				}
				for _, field := range []string{"measurements", "kpsp_results", "food_recalls"} {
					if len(payload[field]) == 0 || string(payload[field]) == "null" {
						t.Errorf("%s must be an array", field)
					}
				}
				w.WriteHeader(404)
				_, _ = w.Write([]byte(`{"data":null,"error":{"code":"NOT_FOUND","message":"Endpoint tidak ditemukan","fields":null}}`))
			}))
			defer srv.Close()
			h := (&Handler{Svc: &service.Service{Store: &repository.Store{DB: db}, Engine: engineclient.New(srv.URL + "/engine/v1")}}).Routes()
			mock.ExpectQuery("SELECT .* FROM children WHERE id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(childRow(birth))
			body := `{"measured_at":"` + day + `","weight_kg":8,"source":"posyandu"}`
			if kind == "measurements" {
				mock.ExpectQuery("INSERT INTO measurements").WillReturnRows(measurementRow(day))
			} else {
				body = `{"recall_date":"` + day + `","breastfed":true,"food_groups":[],"meal_count":3}`
				mock.ExpectQuery("INSERT INTO food_recalls").WillReturnRows(foodRow(day))
			}
			mock.ExpectQuery("SELECT .* FROM measurements WHERE child_id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(measurementRow(day))
			mock.ExpectQuery("SELECT .* FROM kpsp_results WHERE child_id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(sqlmock.NewRows([]string{"id"}))
			mock.ExpectQuery("SELECT .* FROM food_recalls WHERE child_id=").WithArgs(testChildID, repository.DemoParentID, service.Today()).WillReturnRows(foodRow(day))
			r := httptest.NewRecorder()
			h.ServeHTTP(r, httptest.NewRequest(http.MethodPost, "/api/v1/children/"+testChildID+"/"+kind, strings.NewReader(body)))
			var out envelope
			if err := json.Unmarshal(r.Body.Bytes(), &out); err != nil {
				t.Fatal(err)
			}
			if r.Code != 503 || out.Error == nil || out.Error.Code != "ENGINE_UNAVAILABLE" || !strings.Contains(out.Error.Message, "sudah tersimpan") {
				t.Fatalf("unexpected save response %d: %s", r.Code, r.Body.String())
			}
			if err := mock.ExpectationsWereMet(); err != nil {
				t.Fatal(err)
			}

			mock.ExpectQuery("SELECT .* FROM children WHERE id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(childRow(birth))
			id := testMeasurementID
			if kind == "measurements" {
				mock.ExpectQuery("SELECT .* FROM measurements WHERE child_id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(measurementRow(day))
			} else {
				id = testFoodID
				mock.ExpectQuery("SELECT .* FROM food_recalls WHERE child_id=").WithArgs(testChildID, repository.DemoParentID, service.Today()).WillReturnRows(foodRow(day))
			}
			r = httptest.NewRecorder()
			h.ServeHTTP(r, httptest.NewRequest(http.MethodGet, "/api/v1/children/"+testChildID+"/"+kind, nil))
			if r.Code != 200 || !strings.Contains(r.Body.String(), id) {
				t.Fatalf("history response %d: %s", r.Code, r.Body.String())
			}
			if err := mock.ExpectationsWereMet(); err != nil {
				t.Fatal(err)
			}
		})
	}
}

func TestStatusDatabaseFailureIsNotAnEngineOutage(t *testing.T) {
	db, mock, err := sqlmock.New()
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	mock.ExpectQuery("SELECT .* FROM children WHERE id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(childRow("2026-01-01"))
	mock.ExpectQuery("SELECT .* FROM measurements WHERE child_id=").WithArgs(testChildID, repository.DemoParentID).WillReturnError(sql.ErrConnDone)
	h := (&Handler{Svc: &service.Service{Store: &repository.Store{DB: db}}}).Routes()
	r := httptest.NewRecorder()
	h.ServeHTTP(r, httptest.NewRequest(http.MethodGet, "/api/v1/children/"+testChildID+"/status", nil))
	var out envelope
	if err := json.Unmarshal(r.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	if r.Code != 500 || out.Error == nil || out.Error.Code != "INTERNAL" {
		t.Fatalf("unexpected response %d: %s", r.Code, r.Body.String())
	}
	if err := mock.ExpectationsWereMet(); err != nil {
		t.Fatal(err)
	}
}

func TestOutOfDomainMeasurementRejectedBeforeInsert(t *testing.T) {
	for _, tc := range []struct {
		name     string
		days     int
		position string
		length   float64
	}{
		{"below_wfl", 100, "recumbent", 44.9},
		{"corrected_above_wfl", 730, "standing", 109.4},
		{"below_wfh", 731, "standing", 64.9},
		{"corrected_below_wfh", 731, "recumbent", 65.6},
		{"above_wfh", 1000, "standing", 120.1},
	} {
		t.Run(tc.name, func(t *testing.T) {
			db, mock, err := sqlmock.New()
			if err != nil {
				t.Fatal(err)
			}
			defer db.Close()
			today, _ := service.ParseDate(service.Today())
			birth := today.AddDate(0, 0, -tc.days).Format("2006-01-02")
			mock.ExpectQuery("SELECT .* FROM children WHERE id=").WithArgs(testChildID, repository.DemoParentID).WillReturnRows(childRow(birth))
			// No INSERT or engine request is expected for unsupported input.
			h := (&Handler{Svc: &service.Service{Store: &repository.Store{DB: db}}}).Routes()
			body, _ := json.Marshal(map[string]any{
				"measured_at": service.Today(), "weight_kg": 8,
				"length_height_cm": tc.length, "position": tc.position, "source": "posyandu",
			})
			r := httptest.NewRecorder()
			h.ServeHTTP(r, httptest.NewRequest(http.MethodPost, "/api/v1/children/"+testChildID+"/measurements", strings.NewReader(string(body))))
			var out envelope
			if err := json.Unmarshal(r.Body.Bytes(), &out); err != nil {
				t.Fatal(err)
			}
			if r.Code != 422 || out.Error == nil || out.Error.Fields["length_height_cm"] == "" {
				t.Fatalf("unexpected response %d: %s", r.Code, r.Body.String())
			}
			if err := mock.ExpectationsWereMet(); err != nil {
				t.Fatal(err)
			}
		})
	}
}
