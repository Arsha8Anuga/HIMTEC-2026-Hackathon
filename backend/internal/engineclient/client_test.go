package engineclient

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
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

func TestEngineResponseFailures(t *testing.T) {
	tests := []struct {
		name       string
		status     int
		body       string
		validation bool
	}{
		{"missing_route", 404, `{"data":null,"error":{"code":"NOT_FOUND","message":"Endpoint tidak ditemukan","fields":null}}`, false},
		{"input_validation", 422, `{"data":null,"error":{"code":"VALIDATION_ERROR","message":"Input tidak valid","fields":{"source":"invalid"}}}`, true},
		{"server_error", 500, `{"data":null,"error":{"code":"INTERNAL","message":"failed"}}`, false},
		{"mislabelled_server_error", 500, `{"data":null,"error":{"code":"VALIDATION_ERROR","message":"failed"}}`, false},
		{"plain_fastapi_error", 404, `{"detail":"Not Found"}`, false},
		{"html", 502, `<html>bad gateway</html>`, false},
		{"missing_data", 200, `{"error":null}`, false},
		{"null_data", 200, `{"data":null,"error":null}`, false},
		{"missing_error", 200, `{"data":{}}`, false},
		{"malformed_error", 422, `{"data":null,"error":{}}`, false},
		{"wrong_data_type", 200, `{"data":[],"error":null}`, false},
		{"oversized", 200, strings.Repeat(" ", (4<<20)+1), false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(tt.status)
				_, _ = w.Write([]byte(tt.body))
			}))
			defer srv.Close()
			var out struct {
				Level string `json:"level"`
			}
			err := New(srv.URL).Post(context.Background(), "/growth/evaluate", map[string]any{}, &out)
			var failure *Failure
			if !errors.As(err, &failure) {
				t.Fatalf("expected typed engine failure, got %v", err)
			}
			var remote *EngineError
			if errors.As(err, &remote) != tt.validation {
				t.Fatalf("validation classification: %v", err)
			}
		})
	}
}

func TestUnavailableConnectionIsEngineFailure(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	srv.Close()
	err := New(srv.URL).Get(context.Background(), "/health", nil)
	var failure *Failure
	if !errors.As(err, &failure) {
		t.Fatalf("expected typed connection error, got %v", err)
	}
}

func TestCancelledRequestIsEngineFailure(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	err := New("http://127.0.0.1:1").Get(ctx, "/health", nil)
	var failure *Failure
	if !errors.As(err, &failure) || !errors.Is(err, context.Canceled) {
		t.Fatalf("expected wrapped cancellation, got %v", err)
	}
}
