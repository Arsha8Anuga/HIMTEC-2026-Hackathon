package engineclient

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestEnvelope(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/engine/v1/health" {
			t.Errorf("unexpected path: %s", r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"data":{"status":"ok","who_tables_loaded":true},"error":null}`))
	}))
	defer srv.Close()
	var result struct {
		Status string `json:"status"`
	}
	if err := New(srv.URL+"/engine/v1").Get(context.Background(), "/health", &result); err != nil {
		t.Fatal(err)
	}
	if result.Status != "ok" {
		t.Errorf("status = %q", result.Status)
	}
}
