package engineclient

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
)

// Inspection is a diagnostic, not a medical-readiness guarantee or request gate.
// It never posts patient data, changes ENGINE_URL, or falls back to a fake.
type Inspection struct {
	Health          string   `json:"health"`
	Fake            bool     `json:"fake"`
	WHOTablesLoaded *bool    `json:"who_tables_loaded"`
	OpenAPI         string   `json:"openapi"`
	Missing         []string `json:"missing_routes"`
}

func (c *Client) Inspect(ctx context.Context) Inspection {
	out := Inspection{Health: "unreachable", OpenAPI: "unknown", Missing: []string{}}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+"/health", nil)
	if err != nil {
		out.Health = "invalid_url"
		return out
	}
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return out
	}
	body, err := io.ReadAll(io.LimitReader(resp.Body, (1<<20)+1))
	resp.Body.Close()
	out.Fake = resp.Header.Get("X-Fake-Engine") == "true"
	var h struct {
		Data *struct {
			Status string `json:"status"`
			Loaded *bool  `json:"who_tables_loaded"`
		} `json:"data"`
		Error json.RawMessage `json:"error"`
	}
	if err != nil || len(body) > 1<<20 || resp.StatusCode != 200 || json.Unmarshal(body, &h) != nil || h.Data == nil || h.Data.Status != "ok" || h.Data.Loaded == nil || string(h.Error) != "null" {
		out.Health = "invalid_response"
		return out
	}
	out.Health = "ok"
	out.WHOTablesLoaded = h.Data.Loaded
	if out.Fake {
		out.OpenAPI = "fake_fixture"
		return out
	}
	u, err := url.Parse(c.BaseURL)
	if err != nil {
		return out
	}
	// FastAPI's default OpenAPI route is at the origin, not /engine/v1.
	u.Path = "/openapi.json"
	u.RawQuery = ""
	u.Fragment = ""
	req, err = http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if err != nil {
		return out
	}
	resp, err = c.HTTP.Do(req)
	if err != nil {
		return out
	}
	body, err = io.ReadAll(io.LimitReader(resp.Body, (4<<20)+1))
	resp.Body.Close()
	var spec struct {
		Paths map[string]map[string]json.RawMessage `json:"paths"`
	}
	if err != nil || len(body) > 4<<20 || resp.StatusCode != 200 || json.Unmarshal(body, &spec) != nil || spec.Paths == nil {
		return out
	}
	out.OpenAPI = "available"
	for _, route := range []struct{ method, path string }{{"post", "/growth/evaluate"}, {"get", "/reference"}, {"get", "/kpsp/questionnaire"}, {"post", "/kpsp/score"}} {
		path := strings.TrimRight(reqPath(c.BaseURL), "/") + route.path
		if len(spec.Paths[path][route.method]) == 0 {
			out.Missing = append(out.Missing, strings.ToUpper(route.method)+" "+path)
		}
	}
	return out
}
func reqPath(base string) string {
	u, err := url.Parse(base)
	if err != nil {
		return ""
	}
	return u.Path
}
func (r Inspection) Summary() string {
	if r.Health != "ok" {
		return "Health engine belum dapat digunakan (" + r.Health + "). CRUD/login tetap tersedia; evaluasi dapat 503."
	}
	if r.Fake {
		return "FAKE ENGINE aktif: label/status adalah fixture; z-score/referensi bukan hasil medis."
	}
	if len(r.Missing) > 0 {
		return "Health engine OK, tetapi OpenAPI belum menyediakan: " + strings.Join(r.Missing, ", ") + ". Evaluasi terkait dapat 503."
	}
	if r.OpenAPI == "unknown" {
		return "Health engine OK; daftar route belum dapat diperiksa. Health tidak membuktikan evaluasi siap."
	}
	return fmt.Sprintf("Health dan route engine terdaftar; who_tables_loaded=%t. Hasil klinis tetap perlu validasi.", r.WHOTablesLoaded != nil && *r.WHOTablesLoaded)
}
