package handler

import (
	"errors"
	"log"
	"net/http"
	"strings"
	"unicode/utf8"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/llm"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

// Kontrak v0.8: the frontend shows the assistant only when this says enabled.
func (h *Handler) assistantInfo(w http.ResponseWriter, r *http.Request) {
	write(w, 200, map[string]bool{"enabled": h.Svc.AssistantEnabled()})
}

func (h *Handler) assistant(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	var x struct {
		Message string        `json:"message"`
		History []llm.Message `json:"history"`
	}
	if !decode(w, r, &x) {
		return
	}
	x.Message = strings.TrimSpace(x.Message)
	f := map[string]string{}
	if n := utf8.RuneCountInString(x.Message); n == 0 || n > 500 {
		f["message"] = "pertanyaan wajib diisi, paling banyak 500 karakter"
	}
	if len(x.History) > 10 {
		f["history"] = "paling banyak 10 pesan sebelumnya"
	}
	for _, m := range x.History {
		if (m.Role != "user" && m.Role != "assistant") || utf8.RuneCountInString(m.Content) > 2000 {
			f["history"] = "role harus user atau assistant, isi paling banyak 2000 karakter"
		}
	}
	if len(f) > 0 {
		invalid(w, f)
		return
	}
	reply, grounded, err := h.Svc.Assistant(r.Context(), ch, x.Message, x.History)
	switch {
	case errors.Is(err, service.ErrAssistantOff):
		fail(w, 503, "LLM_UNAVAILABLE", "Asisten belum diaktifkan", nil)
	case errors.Is(err, service.ErrAssistantDown):
		log.Printf("asisten: %v", err)
		fail(w, 503, "LLM_UNAVAILABLE", "Asisten sementara tidak tersedia", nil)
	case err != nil:
		engineFailure(w, err)
	default:
		write(w, 200, map[string]any{"reply": reply, "grounded": grounded})
	}
}
