package service

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net/url"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/engineclient"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/repository"
)

type Text struct {
	Title   string `json:"title"`
	Message string `json:"message"`
}
type Guide struct {
	ID            string   `json:"id"`
	Category      string   `json:"category"`
	AgeFromMonths int      `json:"age_from_months"`
	AgeToMonths   int      `json:"age_to_months"`
	Aspect        *string  `json:"aspect"`
	Title         string   `json:"title"`
	Body          string   `json:"body"`
	Source        string   `json:"source"`
	RelatedCodes  []string `json:"related_codes"`
}
type Service struct {
	Store    *repository.Store
	Engine   *engineclient.Client
	Messages map[string]Text
	Guides   []Guide
}

func New(s *repository.Store, e *engineclient.Client, dir string) (*Service, error) {
	mb, err := os.ReadFile(dir + "/messages.id.json")
	if err != nil {
		return nil, err
	}
	gb, err := os.ReadFile(dir + "/guides.id.json")
	if err != nil {
		return nil, err
	}
	x := &Service{Store: s, Engine: e}
	if err = json.Unmarshal(mb, &x.Messages); err != nil {
		return nil, err
	}
	if err = json.Unmarshal(gb, &x.Guides); err != nil {
		return nil, err
	}
	return x, nil
}
func Today() string { return time.Now().Local().Format("2006-01-02") }
func ParseDate(v string) (time.Time, error) {
	if len(v) != 10 {
		return time.Time{}, errors.New("tanggal harus YYYY-MM-DD")
	}
	t, err := time.Parse("2006-01-02", v)
	if err != nil || t.Format("2006-01-02") != v {
		return time.Time{}, errors.New("tanggal harus YYYY-MM-DD")
	}
	return t, nil
}
func AgeDays(birth, asOf string) (int, error) {
	b, e := ParseDate(birth)
	if e != nil {
		return 0, e
	}
	a, e := ParseDate(asOf)
	if e != nil {
		return 0, e
	}
	return int(a.Sub(b).Hours() / 24), nil
}
func (s *Service) Evaluate(ctx context.Context, ch model.Child) (model.Evaluation, []model.Measurement, error) {
	measurements, err := s.Store.Measurements(ctx, ch.ID)
	if err != nil {
		return model.Evaluation{}, nil, err
	}
	kpsp, err := s.Store.Kpsp(ctx, ch.ID)
	if err != nil {
		return model.Evaluation{}, nil, err
	}
	foods, err := s.Store.Foods(ctx, ch.ID)
	if err != nil {
		return model.Evaluation{}, nil, err
	}
	items := make([]model.EngineMeasurement, 0, len(measurements))
	for _, m := range measurements {
		items = append(items, model.EngineMeasurement{ID: m.ID, MeasuredAt: m.MeasuredAt, WeightKg: m.WeightKg, LengthHeightCm: m.LengthHeightCm, Position: m.Position, HeadCircumferenceCm: m.HeadCircumferenceCm, Source: m.Source})
	}
	kr := make([]model.EngineKpsp, 0, len(kpsp))
	for _, k := range kpsp {
		kr = append(kr, model.EngineKpsp{QuestionnaireAgeMonths: k.QuestionnaireAgeMonths, AnsweredAt: k.AnsweredAt, Result: k.Result})
	}
	fr := make([]model.EngineFoodRecall, 0, len(foods))
	for _, f := range foods {
		fr = append(fr, model.EngineFoodRecall{RecallDate: f.RecallDate, Breastfed: f.Breastfed, FoodGroups: f.FoodGroups, MealCount: f.MealCount, MilkFeedCount: f.MilkFeedCount})
	}
	payload := map[string]any{"as_of": Today(), "child": map[string]any{"sex": ch.Sex, "birth_date": ch.BirthDate}, "measurements": items, "kpsp_results": kr, "food_recalls": fr}
	var out model.Evaluation
	err = s.Engine.Post(ctx, "/growth/evaluate", payload, &out)
	return out, measurements, err
}
func levelLabel(level string) (string, error) {
	switch level {
	case "green":
		return "Aman", nil
	case "yellow":
		return "Perlu perhatian", nil
	case "red":
		return "Segera periksakan", nil
	default:
		return "", fmt.Errorf("level engine tidak dikenal: %s", level)
	}
}
func (s *Service) Status(ctx context.Context, ch model.Child) (model.Status, model.Evaluation, []model.Measurement, error) {
	eval, ms, err := s.Evaluate(ctx, ch)
	if err != nil {
		return model.Status{}, eval, ms, err
	}
	label, err := levelLabel(eval.Level)
	if err != nil {
		return model.Status{}, eval, ms, invalidEngineResponse(err)
	}
	age, err := AgeDays(ch.BirthDate, Today())
	if err != nil {
		return model.Status{}, eval, ms, err
	}
	out := model.Status{ChildID: ch.ID, AsOf: Today(), AgeDays: age, AgeMonths: math.Round(float64(age)/30.4375*10) / 10, Level: eval.Level, LevelLabel: label, Latest: nil, Reasons: make([]model.Reason, 0), NextKpsp: eval.NextKpsp, Diet: eval.Diet}
	// Peringatan dan bukti berasal dari engine; Go hanya melokalkan judul/pesan.
	for _, r := range eval.Reasons {
		text, ok := s.Messages[r.Code]
		if !ok {
			return model.Status{}, eval, ms, invalidEngineResponse(fmt.Errorf("kode alasan tidak terdaftar pada messages.id.json: %s", r.Code))
		}
		r.Title = text.Title
		r.Message = strings.ReplaceAll(text.Message, "{{name}}", ch.Name)
		out.Reasons = append(out.Reasons, r)
	}
	if len(ms) > 0 {
		m := ms[0]
		latest := map[string]any{"measurement_id": m.ID, "measured_at": m.MeasuredAt, "weight_kg": m.WeightKg, "length_height_cm": m.LengthHeightCm, "position": m.Position, "z": nil, "classification": nil}
		for _, p := range eval.PerMeasurement {
			if p.ID == m.ID {
				latest["z"] = p.Z
				latest["classification"] = p.Classification
				break
			}
		}
		out.Latest = latest
	}
	return out, eval, ms, nil
}
func (s *Service) Growth(ctx context.Context, ch model.Child, indicator string) (map[string]any, error) {
	eval, ms, err := s.Evaluate(ctx, ch)
	if err != nil {
		return nil, err
	}
	points := make([]map[string]any, 0, len(ms))
	byID := make(map[string]model.EvaluatedPoint, len(eval.PerMeasurement))
	for _, p := range eval.PerMeasurement {
		byID[p.ID] = p
	}
	from, to := 0, 1826 // domain umur dalam hari (kontrak v0.6); referensi dibatasi sampai umur anak + 6 bulan.
	age, _ := AgeDays(ch.BirthDate, Today())
	to = age + 183
	if to > 1826 {
		to = 1826
	}
	if indicator == "wfl_wfh" {
		from = 40
		to = 130
	} // rentang panjang/tinggi yang diizinkan kontrak.
	for _, m := range ms {
		p, ok := byID[m.ID]
		if !ok {
			continue
		}
		var x any = p.AgeDays
		var val any
		switch indicator {
		case "wfa":
			val = m.WeightKg
		case "lhfa":
			if p.CorrectedLengthCm == nil {
				continue
			}
			val = p.CorrectedLengthCm
		case "hcfa":
			if m.HeadCircumferenceCm == nil {
				continue
			}
			val = m.HeadCircumferenceCm
		case "wfl_wfh":
			if p.CorrectedLengthCm == nil {
				continue
			}
			x = p.CorrectedLengthCm
			val = m.WeightKg
		}
		z := p.Z[indicator]
		if val == nil || x == nil {
			continue
		}
		points = append(points, map[string]any{"measurement_id": m.ID, "measured_at": m.MeasuredAt, "x": x, "value": val, "z": z, "flagged": len(p.Flags) > 0})
	}
	// Titik kurva dikirim dari kiri ke kanan (sumbu x menaik).
	sort.SliceStable(points, func(i, j int) bool {
		toNumber := func(v any) float64 {
			switch n := v.(type) {
			case int:
				return float64(n)
			case *float64:
				if n != nil {
					return *n
				}
			}
			return 0
		}
		return toNumber(points[i]["x"]) < toNumber(points[j]["x"])
	})
	var reference json.RawMessage
	err = s.Engine.Get(ctx, engineclient.ReferencePath(indicator, ch.Sex, from, to), &reference)
	if err != nil {
		return nil, err
	}
	xunit := "days"
	if indicator == "wfl_wfh" {
		xunit = "cm"
	}
	return map[string]any{"indicator": indicator, "sex": ch.Sex, "x_unit": xunit, "points": points, "reference": reference}, nil
}
func (s *Service) NextKpsp(ctx context.Context, ch model.Child) (map[string]any, error) {
	eval, _, err := s.Evaluate(ctx, ch)
	if err != nil {
		return nil, err
	}
	var next struct {
		QuestionnaireAgeMonths int  `json:"questionnaire_age_months"`
		Due                    bool `json:"due"`
	}
	if err = json.Unmarshal(eval.NextKpsp, &next); err != nil {
		return nil, invalidEngineResponse(fmt.Errorf("engine tidak mengembalikan jadwal KPSP: %w", err))
	}
	if !validQuestionnaireAge(next.QuestionnaireAgeMonths) {
		return nil, invalidEngineResponse(errors.New("engine tidak mengembalikan umur jadwal KPSP yang valid"))
	}
	var questionnaire struct {
		Items json.RawMessage `json:"items"`
	}
	path := "/kpsp/questionnaire?" + url.Values{"age_months": {fmt.Sprint(next.QuestionnaireAgeMonths)}}.Encode()
	if err = s.Engine.Get(ctx, path, &questionnaire); err != nil {
		return nil, err
	}
	var items []json.RawMessage
	if err = json.Unmarshal(questionnaire.Items, &items); err != nil || len(items) != 10 {
		return nil, invalidEngineResponse(errors.New("engine tidak mengembalikan 10 butir KPSP"))
	}
	return map[string]any{"questionnaire_age_months": next.QuestionnaireAgeMonths, "due": next.Due, "items": questionnaire.Items}, nil
}
func (s *Service) ScoreKpsp(ctx context.Context, input model.KpspInput) (int, string, error) {
	var score struct {
		YesCount *int   `json:"yes_count"`
		Result   string `json:"result"`
	}
	if err := s.Engine.Post(ctx, "/kpsp/score", map[string]any{"questionnaire_age_months": input.QuestionnaireAgeMonths, "answers": input.Answers}, &score); err != nil {
		return 0, "", err
	}
	if score.YesCount == nil || *score.YesCount < 0 || *score.YesCount > 10 {
		return 0, "", invalidEngineResponse(errors.New("skor engine hilang atau di luar rentang"))
	}
	if score.Result != "sesuai" && score.Result != "meragukan" && score.Result != "penyimpangan" {
		return 0, "", invalidEngineResponse(errors.New("hasil KPSP engine tidak dikenal"))
	}
	return *score.YesCount, score.Result, nil
}

func invalidEngineResponse(err error) error {
	return &engineclient.Failure{Operation: "validasi response", Err: err}
}

func validQuestionnaireAge(age int) bool {
	switch age {
	case 3, 6, 9, 12, 15, 18, 21, 24, 30, 36, 42, 48, 54, 60:
		return true
	default:
		return false
	}
}
func (s *Service) FilterGuides(category string, age *int, aspect string) []Guide {
	out := make([]Guide, 0)
	for _, g := range s.Guides {
		if category != "" && g.Category != category {
			continue
		}
		if age != nil && (*age < g.AgeFromMonths || *age > g.AgeToMonths) {
			continue
		}
		if aspect != "" && (g.Aspect == nil || *g.Aspect != aspect) {
			continue
		}
		out = append(out, g)
	}
	return out
}
