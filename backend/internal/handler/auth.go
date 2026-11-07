package handler

import (
	"errors"
	"net/http"
	"strings"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/auth"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
)

func bearer(r *http.Request) string {
	parts := strings.Fields(r.Header.Get("Authorization"))
	if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
		return ""
	}
	return parts[1]
}
func authError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, auth.ErrInput):
		fail(w, 422, "VALIDATION_ERROR", "Nama atau email tidak valid", nil)
	case errors.Is(err, auth.ErrInvalid):
		fail(w, 401, "UNAUTHORIZED", "Kode atau sesi tidak valid, sudah dipakai, atau kedaluwarsa", nil)
	case errors.Is(err, auth.ErrRate):
		fail(w, 429, "RATE_LIMITED", "Tunggu 60 detik; maksimal 5 permintaan per email per jam", nil)
	default:
		unexpected(w, err)
	}
}
func (h *Handler) authRoute(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	switch {
	case r.Method == http.MethodPost && (r.URL.Path == "/api/v1/auth/register" || r.URL.Path == "/api/v1/auth/login"):
		var input struct {
			Name  string `json:"name"`
			Email string `json:"email"`
		}
		if !decode(w, r, &input) {
			return
		}
		purpose := "login"
		if r.URL.Path == "/api/v1/auth/register" {
			purpose = "register"
		}
		out, err := h.Auth.Request(r.Context(), purpose, input.Name, input.Email)
		if err != nil {
			authError(w, err)
			return
		}
		write(w, 202, out)
	case r.Method == http.MethodPost && r.URL.Path == "/api/v1/auth/verify":
		var input struct {
			ID   string `json:"challenge_id"`
			Code string `json:"code"`
		}
		if !decode(w, r, &input) {
			return
		}
		out, err := h.Auth.Verify(r.Context(), input.ID, input.Code)
		if err != nil {
			authError(w, err)
			return
		}
		write(w, 200, out)
	case r.Method == http.MethodGet && r.URL.Path == "/api/v1/auth/me":
		out, err := h.Auth.Lookup(r.Context(), bearer(r))
		if err != nil {
			authError(w, err)
			return
		}
		write(w, 200, out)
	case r.Method == http.MethodPost && r.URL.Path == "/api/v1/auth/logout":
		if err := h.Auth.Logout(r.Context(), bearer(r)); err != nil {
			authError(w, err)
			return
		}
		write(w, 200, map[string]bool{"logged_out": true})
	default:
		missing(w)
	}
}
func (h *Handler) authenticated(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	u, err := h.Auth.Lookup(r.Context(), bearer(r))
	if err != nil {
		authError(w, err)
		return
	}
	// Request-local copies: never mutate shared Store/Service or allow demo fallback.
	store := &repository.Store{DB: h.Svc.Store.DB, ParentID: u.ID}
	svc := *h.Svc
	svc.Store = store
	scoped := *h
	scoped.Svc = &svc
	scoped.Auth = nil
	scoped.Routes().ServeHTTP(w, r)
}
