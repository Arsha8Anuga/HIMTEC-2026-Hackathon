package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"regexp"
	"strconv"
	"strings"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/llm"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
)

// ErrAssistantOff: LLM not configured (LLM_ENABLED is not true).
var ErrAssistantOff = errors.New("asisten tidak diaktifkan")

// ErrAssistantDown wraps any Ollama failure (down, slow, bad response).
var ErrAssistantDown = errors.New("asisten tidak tersedia")

// Rejected is the reply when the model mentions a number absent from the child's data.
const Rejected = "Asisten tidak dapat menjawab dengan aman dari data yang ada. Coba tanyakan dengan cara lain, atau tanyakan langsung ke petugas Posyandu."

const systemPrompt = `Kamu asisten di aplikasi Pantau Tumbuh Kembang Anak. Aplikasi ini alat skrining, bukan diagnosis.
Aturan:
1. Jawab HANYA dari DATA di bawah. Jangan menambah angka, diagnosis, nama obat, dosis, atau saran medis yang tidak ada di DATA.
2. Bila jawabannya tidak ada di DATA, katakan terus terang bahwa datanya tidak ada, lalu sarankan bertanya ke petugas Posyandu atau Puskesmas.
3. Bila status anak "red", selalu ulangi ajakan di pesan alasan untuk segera ke Posyandu/Puskesmas.
4. Saran makan dan stimulasi hanya boleh diambil dari bagian "panduan" beserta sumbernya.
5. Tulis dalam Bahasa Indonesia sehari-hari, paling banyak 5 kalimat, tanpa istilah z-score kecuali ditanya.
DATA (JSON):
`

func (s *Service) AssistantEnabled() bool { return s.LLM != nil }

// Assistant answers a parent's question from the same data /status, /measurements and /kpsp return.
func (s *Service) Assistant(ctx context.Context, ch model.Child, question string, history []llm.Message) (reply string, grounded bool, err error) {
	if s.LLM == nil {
		return "", false, ErrAssistantOff
	}
	st, _, ms, err := s.Status(ctx, ch)
	if err != nil {
		return "", false, err
	}
	kpsp, err := s.Store.Kpsp(ctx, ch.ID)
	if err != nil {
		return "", false, err
	}
	data, err := json.Marshal(assistantFacts(ch, st, ms, kpsp, s.relatedGuides(st)))
	if err != nil {
		return "", false, err
	}
	msgs := append([]llm.Message{{Role: "system", Content: systemPrompt + string(data)}}, history...)
	msgs = append(msgs, llm.Message{Role: "user", Content: question})
	reply, err = s.LLM.Chat(ctx, msgs)
	if err != nil {
		return "", false, fmt.Errorf("%w: %v", ErrAssistantDown, err)
	}
	allowed := string(data) + " " + question
	for _, h := range history {
		if h.Role == "user" {
			allowed += " " + h.Content
		}
	}
	if bad := unknownNumbers(reply, allowed); len(bad) > 0 {
		log.Printf("asisten: jawaban ditolak, angka di luar data: %v", bad)
		return Rejected, false, nil
	}
	return reply, true, nil
}

func (s *Service) relatedGuides(st model.Status) []map[string]any {
	age := int(st.AgeMonths)
	out := []map[string]any{}
	for _, g := range s.FilterGuides("", &age, "") {
		for _, r := range st.Reasons {
			if contains(g.RelatedCodes, r.Code) {
				out = append(out, map[string]any{"judul": g.Title, "isi": g.Body, "sumber": g.Source})
				break
			}
		}
	}
	return out
}

func contains(xs []string, x string) bool {
	for _, v := range xs {
		if v == x {
			return true
		}
	}
	return false
}

// IDs are left out on purpose: their digits would widen the number check below.
func assistantFacts(ch model.Child, st model.Status, ms []model.Measurement, kpsp []model.KpspResult, guides []map[string]any) map[string]any {
	reasons := make([]map[string]any, 0, len(st.Reasons))
	for _, r := range st.Reasons {
		reasons = append(reasons, map[string]any{"tingkat": r.Level, "judul": r.Title, "pesan": r.Message})
	}
	measurements := make([]map[string]any, 0, len(ms))
	for _, m := range ms {
		measurements = append(measurements, map[string]any{"tanggal": m.MeasuredAt, "berat_kg": m.WeightKg,
			"panjang_tinggi_cm": m.LengthHeightCm, "lingkar_kepala_cm": m.HeadCircumferenceCm, "sumber": m.Source})
	}
	screenings := make([]map[string]any, 0, len(kpsp))
	for _, k := range kpsp {
		screenings = append(screenings, map[string]any{"tanggal": k.AnsweredAt, "formulir_bulan": k.QuestionnaireAgeMonths,
			"jawaban_ya": k.YesCount, "hasil": k.Result})
	}
	var latest map[string]any
	if l, ok := st.Latest.(map[string]any); ok {
		latest = map[string]any{}
		for k, v := range l {
			if k != "measurement_id" {
				latest[k] = v
			}
		}
	}
	return map[string]any{
		"anak":               map[string]any{"nama": ch.Name, "jenis_kelamin": ch.Sex, "tanggal_lahir": ch.BirthDate, "umur_bulan": st.AgeMonths},
		"status":             map[string]any{"tanggal": st.AsOf, "tingkat": st.Level, "label": st.LevelLabel, "alasan": reasons, "pengukuran_terakhir": latest, "kpsp_berikutnya": st.NextKpsp, "catatan_makan": st.Diet},
		"riwayat_pengukuran": measurements,
		"riwayat_kpsp":       screenings,
		"panduan":            guides,
	}
}

var (
	number  = regexp.MustCompile(`\d+(?:[.,]\d+)?`)
	isoDate = regexp.MustCompile(`\b(\d{4})-(\d{2})-(\d{2})\b`)
)

// unknownNumbers lists numbers in text that never occur in allowed (8,2 and 8.20 equal 8.2).
// An ISO date counts as one value, contributing only its day and year (as in "7 November 2026");
// otherwise every date would whitelist the numbers 1-31.
func unknownNumbers(text, allowed string) []string {
	known := map[string]bool{}
	dates := map[string]bool{}
	for _, d := range isoDate.FindAllStringSubmatch(allowed, -1) {
		dates[d[0]] = true
		known[canonical(d[1])], known[canonical(d[3])] = true, true
	}
	for _, n := range number.FindAllString(isoDate.ReplaceAllString(allowed, " "), -1) {
		known[canonical(n)] = true
	}
	var bad []string
	for _, d := range isoDate.FindAllString(text, -1) {
		if !dates[d] {
			bad = append(bad, d)
		}
	}
	for _, n := range number.FindAllString(isoDate.ReplaceAllString(text, " "), -1) {
		if !known[canonical(n)] {
			bad = append(bad, n)
		}
	}
	return bad
}

func canonical(n string) string {
	f, err := strconv.ParseFloat(strings.ReplaceAll(n, ",", "."), 64)
	if err != nil {
		return n
	}
	return strconv.FormatFloat(f, 'f', -1, 64)
}
