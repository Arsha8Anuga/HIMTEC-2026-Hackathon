package handler

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"math"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/service"
)

type Handler struct {
	Svc        *service.Service
	CORSOrigin string
}
type apiError struct {
	Code    string            `json:"code"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields,omitempty"`
}
type envelope struct {
	Data  any       `json:"data"`
	Error *apiError `json:"error"`
}

func write(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(envelope{Data: data, Error: nil})
}
func fail(w http.ResponseWriter, status int, code, msg string, fields map[string]string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(envelope{Data: nil, Error: &apiError{Code: code, Message: msg, Fields: fields}})
}
func invalid(w http.ResponseWriter, fields map[string]string) {
	fail(w, 422, "VALIDATION_ERROR", "Data yang dimasukkan tidak valid", fields)
}
func missing(w http.ResponseWriter) { fail(w, 404, "NOT_FOUND", "Data tidak ditemukan", nil) }
func unexpected(w http.ResponseWriter, err error) {
	respondError(w, err, "")
}

func respondError(w http.ResponseWriter, err error, saved string) {
	message := func(text string) string {
		if saved != "" {
			return saved + " sudah tersimpan. " + text + ". Periksa riwayat sebelum mengirim ulang."
		}
		return text
	}
	if errors.Is(err, sql.ErrNoRows) {
		missing(w)
		return
	}
	var e *engineclient.EngineError
	if errors.As(err, &e) {
		switch e.Code {
		case "VALIDATION_ERROR":
			fail(w, 422, "VALIDATION_ERROR", message(e.Message), e.Fields)
			return
		}
		fail(w, 503, "ENGINE_UNAVAILABLE", message("Perhitungan sementara tidak tersedia"), nil)
		return
	}
	var failure *engineclient.Failure
	if errors.As(err, &failure) {
		log.Printf("%v", err)
		fail(w, 503, "ENGINE_UNAVAILABLE", message("Perhitungan sementara tidak tersedia"), nil)
		return
	}
	log.Printf("backend: %v", err)
	fail(w, 500, "INTERNAL", message("Terjadi kesalahan pada server"), nil)
}
func engineFailure(w http.ResponseWriter, err error) {
	// Evaluation can also fail while reading PostgreSQL. Classify by the
	// error's source rather than treating every failure as an engine outage.
	unexpected(w, err)
}
func decode(w http.ResponseWriter, r *http.Request, v any) bool {
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20)
	d := json.NewDecoder(r.Body)
	d.DisallowUnknownFields()
	if err := d.Decode(v); err != nil {
		invalid(w, map[string]string{"body": "JSON tidak valid atau field tidak dikenal"})
		return false
	}
	var extra any
	if err := d.Decode(&extra); err != io.EOF {
		invalid(w, map[string]string{"body": "hanya satu objek JSON diperbolehkan"})
		return false
	}
	return true
}

var uuidRe = regexp.MustCompile(`^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$`)

func checkID(w http.ResponseWriter, id string) bool {
	if !uuidRe.MatchString(id) {
		invalid(w, map[string]string{"id": "harus UUID v4"})
		return false
	}
	return true
}
func dateFields(key, value string, fields map[string]string) (time.Time, bool) {
	t, err := service.ParseDate(value)
	if err != nil {
		fields[key] = "harus YYYY-MM-DD"
		return time.Time{}, false
	}
	return t, true
}
func checkRange(key string, v *float64, min, max float64, f map[string]string) {
	if v != nil && (math.IsNaN(*v) || math.IsInf(*v, 0) || *v < min || *v > max) {
		f[key] = fmt.Sprintf("harus antara %g dan %g", min, max)
	}
}
func intRange(key string, v *int, min, max int, f map[string]string) {
	if v != nil && (*v < min || *v > max) {
		f[key] = fmt.Sprintf("harus antara %d dan %d", min, max)
	}
}
func validChild(x model.ChildInput) map[string]string {
	f := map[string]string{}
	if utf8.RuneCountInString(x.Name) < 1 || utf8.RuneCountInString(x.Name) > 60 || strings.TrimSpace(x.Name) == "" {
		f["name"] = "panjang nama harus 1–60 karakter"
	}
	if x.Sex != "male" && x.Sex != "female" {
		f["sex"] = "harus male atau female"
	}
	b, ok := dateFields("birth_date", x.BirthDate, f)
	if ok {
		today, _ := service.ParseDate(service.Today())
		if b.After(today) {
			f["birth_date"] = "tidak boleh di masa depan"
		} else if b.AddDate(0, 60, 0).Before(today) {
			f["birth_date"] = "umur anak maksimal 60 bulan"
		}
	}
	checkRange("birth_weight_kg", x.BirthWeightKg, 0.5, 6, f)
	checkRange("birth_length_cm", x.BirthLengthCm, 30, 60, f)
	return f
}
func validMeasurement(x model.MeasurementInput, ch model.Child) map[string]string {
	f := map[string]string{}
	d, ok := dateFields("measured_at", x.MeasuredAt, f)
	if ok {
		b, _ := service.ParseDate(ch.BirthDate)
		today, _ := service.ParseDate(service.Today())
		if d.Before(b) {
			f["measured_at"] = "before_birth_date"
		}
		if d.After(today) {
			f["measured_at"] = "tanggal tidak boleh di masa depan"
		}
		if int(d.Sub(b).Hours()/24) > 1856 {
			f["measured_at"] = "umur pengukuran maksimal 1856 hari"
		}
	}
	if x.WeightKg == nil {
		f["weight_kg"] = "wajib diisi"
	} else {
		checkRange("weight_kg", x.WeightKg, 0.5, 40, f)
	}
	checkRange("length_height_cm", x.LengthHeightCm, 40, 130, f)
	checkRange("head_circumference_cm", x.HeadCircumferenceCm, 30, 60, f)
	if x.LengthHeightCm != nil && x.Position == nil {
		f["position"] = "wajib jika panjang/tinggi diisi"
	}
	if x.Position != nil && *x.Position != "recumbent" && *x.Position != "standing" {
		f["position"] = "harus recumbent atau standing"
	}
	if x.Source != "posyandu" && x.Source != "puskesmas" && x.Source != "home" {
		f["source"] = "harus posyandu, puskesmas, atau home"
	}
	if x.Note != nil && utf8.RuneCountInString(*x.Note) > 200 {
		f["note"] = "maksimal 200 karakter"
	}
	return f
}
func validKpsp(x model.KpspInput, ch model.Child) map[string]string {
	f := map[string]string{}
	allowed := map[int]bool{3: true, 6: true, 9: true, 12: true, 15: true, 18: true, 21: true, 24: true, 30: true, 36: true, 42: true, 48: true, 54: true, 60: true}
	if !allowed[x.QuestionnaireAgeMonths] {
		f["questionnaire_age_months"] = "harus salah satu umur jadwal KPSP pada kontrak"
	}
	d, ok := dateFields("answered_at", x.AnsweredAt, f)
	if ok {
		today, _ := service.ParseDate(service.Today())
		birth, _ := service.ParseDate(ch.BirthDate)
		if d.Before(birth) {
			f["answered_at"] = "tidak boleh sebelum birth_date"
		}
		if d.After(today) {
			f["answered_at"] = "tidak boleh di masa depan"
		}
	}
	if len(x.Answers) != 10 {
		f["answers"] = "harus tepat 10 jawaban"
	} else {
		seen := map[int]bool{}
		for _, a := range x.Answers {
			if a.ItemNo < 1 || a.ItemNo > 10 || seen[a.ItemNo] || a.Answer == nil {
				f["answers"] = "item_no harus unik dari 1 sampai 10"
			}
			seen[a.ItemNo] = true
		}
	}
	return f
}

var validGroups = map[string]bool{"grains_roots_tubers": true, "pulses_nuts_seeds": true, "dairy": true, "flesh_foods": true, "eggs": true, "vita_fruits_veg": true, "other_fruits_veg": true}

func validFood(x model.FoodRecallInput, ch model.Child) map[string]string {
	f := map[string]string{}
	d, ok := dateFields("recall_date", x.RecallDate, f)
	if ok {
		birth, _ := service.ParseDate(ch.BirthDate)
		today, _ := service.ParseDate(service.Today())
		if d.After(today) {
			f["recall_date"] = "tidak boleh di masa depan"
		}
		ageMonths := d.Sub(birth).Hours() / 24 / 30.4375
		if ageMonths < 6 || ageMonths >= 24 {
			f["recall_date"] = "umur anak saat catatan makan harus 6–23 bulan"
		}
	}
	if x.Breastfed == nil {
		f["breastfed"] = "wajib diisi"
	}
	if x.FoodGroups == nil {
		f["food_groups"] = "wajib diisi (boleh array kosong [])"
	}
	seen := map[string]bool{}
	for _, g := range x.FoodGroups {
		if !validGroups[g] || seen[g] {
			f["food_groups"] = "kelompok makanan tidak dikenal atau duplikat"
		}
		seen[g] = true
	}
	if x.MealCount == nil {
		f["meal_count"] = "wajib diisi"
	} else {
		intRange("meal_count", x.MealCount, 0, 10, f)
	}
	intRange("milk_feed_count", x.MilkFeedCount, 0, 10, f)
	return f
}
func sqlValidation(w http.ResponseWriter, err error) bool { // PostgreSQL SQLSTATE 23505 = uniqueness, 23514 = check constraint.
	var state interface{ SQLState() string }
	if errors.As(err, &state) && (state.SQLState() == "23505" || state.SQLState() == "23514") {
		invalid(w, map[string]string{"body": "data duplikat atau melanggar aturan database"})
		return true
	}
	return false
}
func (h *Handler) child(w http.ResponseWriter, r *http.Request) (model.Child, bool) {
	id := r.PathValue("id")
	if !checkID(w, id) {
		return model.Child{}, false
	}
	ch, err := h.Svc.Store.Child(r.Context(), id)
	if err != nil {
		unexpected(w, err)
		return model.Child{}, false
	}
	return ch, true
}
func (h *Handler) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/v1/", func(w http.ResponseWriter, r *http.Request) { missing(w) })
	mux.HandleFunc("GET /api/v1/children", h.children)
	mux.HandleFunc("POST /api/v1/children", h.addChild)
	mux.HandleFunc("GET /api/v1/children/{id}", h.getChild)
	mux.HandleFunc("GET /api/v1/children/{id}/status", h.status)
	mux.HandleFunc("GET /api/v1/children/{id}/measurements", h.measurements)
	mux.HandleFunc("POST /api/v1/children/{id}/measurements", h.addMeasurement)
	mux.HandleFunc("DELETE /api/v1/children/{id}/measurements/{mid}", h.deleteMeasurement)
	mux.HandleFunc("GET /api/v1/children/{id}/growth", h.growth)
	mux.HandleFunc("GET /api/v1/children/{id}/kpsp/next", h.kpspNext)
	mux.HandleFunc("POST /api/v1/children/{id}/kpsp", h.addKpsp)
	mux.HandleFunc("GET /api/v1/children/{id}/kpsp", h.kpspList)
	mux.HandleFunc("GET /api/v1/guides", h.guides)
	mux.HandleFunc("POST /api/v1/children/{id}/food-recalls", h.addFood)
	mux.HandleFunc("GET /api/v1/children/{id}/food-recalls", h.foods)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" && origin == h.CORSOrigin {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Vary", "Origin")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		}
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		mux.ServeHTTP(w, r)
	})
}
func (h *Handler) children(w http.ResponseWriter, r *http.Request) {
	x, err := h.Svc.Store.Children(r.Context())
	if err != nil {
		unexpected(w, err)
		return
	}
	write(w, 200, x)
}
func (h *Handler) addChild(w http.ResponseWriter, r *http.Request) {
	var x model.ChildInput
	if !decode(w, r, &x) {
		return
	}
	if fields := validChild(x); len(fields) > 0 {
		invalid(w, fields)
		return
	}
	ch, err := h.Svc.Store.AddChild(r.Context(), x)
	if err != nil {
		if !sqlValidation(w, err) {
			unexpected(w, err)
		}
		return
	}
	write(w, 201, ch)
}
func (h *Handler) getChild(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if ok {
		write(w, 200, ch)
	}
}
func (h *Handler) status(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	st, _, _, err := h.Svc.Status(r.Context(), ch)
	if err != nil {
		engineFailure(w, err)
		return
	}
	write(w, 200, st)
}
func (h *Handler) measurements(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	items, err := h.Svc.Store.Measurements(r.Context(), ch.ID)
	if err != nil {
		unexpected(w, err)
		return
	}
	write(w, 200, items)
}
func (h *Handler) addMeasurement(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	var x model.MeasurementInput
	if !decode(w, r, &x) {
		return
	}
	if f := validMeasurement(x, ch); len(f) > 0 {
		invalid(w, f)
		return
	}
	m, err := h.Svc.Store.AddMeasurement(r.Context(), ch.ID, x)
	if err != nil {
		if !sqlValidation(w, err) {
			unexpected(w, err)
		}
		return
	}
	st, _, _, err := h.Svc.Status(r.Context(), ch)
	if err != nil {
		log.Printf("pengukuran %s sudah tersimpan; evaluasi gagal: %v", m.ID, err)
		respondError(w, err, "Pengukuran")
		return
	}
	write(w, 201, map[string]any{"measurement": m, "status": st})
}
func (h *Handler) deleteMeasurement(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	mid := r.PathValue("mid")
	if !checkID(w, mid) {
		return
	}
	deleted, err := h.Svc.Store.DeleteMeasurement(r.Context(), ch.ID, mid)
	if err != nil {
		unexpected(w, err)
		return
	}
	if !deleted {
		missing(w)
		return
	}
	write(w, 200, nil)
}
func (h *Handler) growth(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	indicator := r.URL.Query().Get("indicator")
	switch indicator {
	case "wfa", "lhfa", "wfl_wfh", "hcfa":
	default:
		invalid(w, map[string]string{"indicator": "harus wfa, lhfa, wfl_wfh, atau hcfa"})
		return
	}
	data, err := h.Svc.Growth(r.Context(), ch, indicator)
	if err != nil {
		engineFailure(w, err)
		return
	}
	write(w, 200, data)
}
func (h *Handler) kpspNext(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	data, err := h.Svc.NextKpsp(r.Context(), ch)
	if err != nil {
		engineFailure(w, err)
		return
	}
	write(w, 200, data)
}
func (h *Handler) addKpsp(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	var x model.KpspInput
	if !decode(w, r, &x) {
		return
	}
	if f := validKpsp(x, ch); len(f) > 0 {
		invalid(w, f)
		return
	}
	yes, result, err := h.Svc.ScoreKpsp(r.Context(), x)
	if err != nil {
		engineFailure(w, err)
		return
	}
	k, err := h.Svc.Store.AddKpsp(r.Context(), ch.ID, x, yes, result)
	if err != nil {
		unexpected(w, err)
		return
	}
	write(w, 201, k)
}
func (h *Handler) kpspList(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	data, err := h.Svc.Store.Kpsp(r.Context(), ch.ID)
	if err != nil {
		unexpected(w, err)
		return
	}
	write(w, 200, data)
}
func (h *Handler) guides(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	cat := q.Get("category")
	if cat != "" && cat != "mpasi" && cat != "stimulasi" {
		invalid(w, map[string]string{"category": "harus mpasi atau stimulasi"})
		return
	}
	aspect := q.Get("aspect")
	if aspect != "" && aspect != "gerak_kasar" && aspect != "gerak_halus" && aspect != "bicara_bahasa" && aspect != "sosialisasi_kemandirian" {
		invalid(w, map[string]string{"aspect": "aspek tidak dikenal"})
		return
	}
	var age *int
	if q.Has("age_months") {
		n, err := strconv.Atoi(q.Get("age_months"))
		if err != nil || n < 0 || n > 60 {
			invalid(w, map[string]string{"age_months": "harus angka 0–60"})
			return
		}
		age = &n
	}
	write(w, 200, h.Svc.FilterGuides(cat, age, aspect))
}
func (h *Handler) addFood(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	var x model.FoodRecallInput
	if !decode(w, r, &x) {
		return
	}
	if x.RecallDate == "" {
		yesterday, _ := service.ParseDate(service.Today())
		x.RecallDate = yesterday.AddDate(0, 0, -1).Format("2006-01-02")
	}
	if f := validFood(x, ch); len(f) > 0 {
		invalid(w, f)
		return
	}
	food, err := h.Svc.Store.AddFood(r.Context(), ch.ID, x)
	if err != nil {
		if !sqlValidation(w, err) {
			unexpected(w, err)
		}
		return
	}
	st, _, _, err := h.Svc.Status(r.Context(), ch)
	if err != nil {
		log.Printf("catatan makan %s sudah tersimpan; evaluasi gagal: %v", food.ID, err)
		respondError(w, err, "Catatan makan")
		return
	}
	write(w, 201, map[string]any{"food_recall": food, "status": st})
}
func (h *Handler) foods(w http.ResponseWriter, r *http.Request) {
	ch, ok := h.child(w, r)
	if !ok {
		return
	}
	data, err := h.Svc.Store.Foods(r.Context(), ch.ID)
	if err != nil {
		unexpected(w, err)
		return
	}
	write(w, 200, data)
}
