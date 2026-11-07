package engineclient

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestInspectDistinguishesHealthFromRoutes(t *testing.T) {
	for _, tt := range []struct {
		name                    string
		fake, complete, unknown bool
		missing                 int
	}{{"health_only", false, false, false, 4}, {"complete_routes", false, true, false, 0}, {"fake_fixture", true, false, false, 0}, {"unknown_openapi", false, false, true, 0}} {
		t.Run(tt.name, func(t *testing.T) {
			openapiCalls := 0
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.Method != "GET" {
					t.Error("probe must not post patient data")
				}
				if r.URL.Path == "/engine/v1/health" {
					if tt.fake {
						w.Header().Set("X-Fake-Engine", "true")
					}
					w.Write([]byte(`{"data":{"status":"ok","who_tables_loaded":false},"error":null}`))
					return
				}
				openapiCalls++
				if r.URL.Path != "/openapi.json" {
					t.Errorf("wrong OpenAPI path: %s", r.URL.Path)
				}
				if tt.unknown {
					w.WriteHeader(404)
					return
				}
				if tt.complete {
					w.Write([]byte(`{"paths":{"/engine/v1/growth/evaluate":{"post":{}},"/engine/v1/reference":{"get":{}},"/engine/v1/kpsp/questionnaire":{"get":{}},"/engine/v1/kpsp/score":{"post":{}}}}`))
				} else {
					w.Write([]byte(`{"paths":{"/engine/v1/health":{"get":{}}}}`))
				}
			}))
			defer srv.Close()
			report := New(srv.URL + "/engine/v1").Inspect(context.Background())
			if report.Health != "ok" || report.Fake != tt.fake || len(report.Missing) != tt.missing || report.WHOTablesLoaded == nil || *report.WHOTablesLoaded {
				t.Fatalf("bad report %+v", report)
			}
			if tt.fake && openapiCalls != 0 {
				t.Fatal("fake must not be judged as real readiness")
			}
			if tt.unknown && report.OpenAPI != "unknown" {
				t.Fatalf("unavailable OpenAPI misclassified: %+v", report)
			}
			if tt.missing > 0 && !strings.Contains(report.Summary(), "belum menyediakan") {
				t.Fatal(report.Summary())
			}
		})
	}
}
func TestInspectRejectsInvalidHealthAndCancellation(t *testing.T) {
	for _, body := range []string{`{"status":"ok"}`, `{"data":null,"error":null}`, `{"data":{"status":"ok"},"error":null}`} {
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { w.Write([]byte(body)) }))
		out := New(srv.URL).Inspect(context.Background())
		srv.Close()
		if out.Health != "invalid_response" {
			t.Fatalf("invalid health accepted: %+v", out)
		}
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	out := New("http://127.0.0.1:1").Inspect(ctx)
	if out.Health != "unreachable" {
		t.Fatalf("cancel: %+v", out)
	}
}
