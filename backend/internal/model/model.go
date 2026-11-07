package model

import "encoding/json"

// Model JSON publik mengikuti docs/CONTRACT.md v0.4.
type Child struct {
	ID            string   `json:"id"`
	Name          string   `json:"name"`
	Sex           string   `json:"sex"`
	BirthDate     string   `json:"birth_date"`
	BirthWeightKg *float64 `json:"birth_weight_kg"`
	BirthLengthCm *float64 `json:"birth_length_cm"`
	IsPreterm     bool     `json:"is_preterm"`
	CreatedAt     string   `json:"created_at"`
}
type ChildInput struct {
	Name          string   `json:"name"`
	Sex           string   `json:"sex"`
	BirthDate     string   `json:"birth_date"`
	BirthWeightKg *float64 `json:"birth_weight_kg"`
	BirthLengthCm *float64 `json:"birth_length_cm"`
	IsPreterm     *bool    `json:"is_preterm"`
}
type Measurement struct {
	ID                  string   `json:"id"`
	ChildID             string   `json:"child_id"`
	MeasuredAt          string   `json:"measured_at"`
	WeightKg            float64  `json:"weight_kg"`
	LengthHeightCm      *float64 `json:"length_height_cm"`
	Position            *string  `json:"position"`
	HeadCircumferenceCm *float64 `json:"head_circumference_cm"`
	Source              string   `json:"source"`
	Note                *string  `json:"note"`
	CreatedAt           string   `json:"created_at"`
}
type MeasurementInput struct {
	MeasuredAt          string   `json:"measured_at"`
	WeightKg            *float64 `json:"weight_kg"`
	LengthHeightCm      *float64 `json:"length_height_cm"`
	Position            *string  `json:"position"`
	HeadCircumferenceCm *float64 `json:"head_circumference_cm"`
	Source              string   `json:"source"`
	Note                *string  `json:"note"`
}
type Answer struct {
	ItemNo int   `json:"item_no"`
	Answer *bool `json:"answer"`
}
type KpspInput struct {
	QuestionnaireAgeMonths int      `json:"questionnaire_age_months"`
	AnsweredAt             string   `json:"answered_at"`
	Answers                []Answer `json:"answers"`
}
type KpspResult struct {
	ID                     string   `json:"id"`
	ChildID                string   `json:"child_id"`
	QuestionnaireAgeMonths int      `json:"questionnaire_age_months"`
	AnsweredAt             string   `json:"answered_at"`
	Answers                []Answer `json:"answers"`
	YesCount               int      `json:"yes_count"`
	Result                 string   `json:"result"`
	CreatedAt              string   `json:"created_at"`
}
type FoodRecallInput struct {
	RecallDate    string   `json:"recall_date"`
	Breastfed     *bool    `json:"breastfed"`
	FoodGroups    []string `json:"food_groups"`
	MealCount     *int     `json:"meal_count"`
	MilkFeedCount *int     `json:"milk_feed_count"`
}
type FoodRecall struct {
	ID            string   `json:"id"`
	ChildID       string   `json:"child_id"`
	RecallDate    string   `json:"recall_date"`
	Breastfed     bool     `json:"breastfed"`
	FoodGroups    []string `json:"food_groups"`
	MealCount     int      `json:"meal_count"`
	MilkFeedCount *int     `json:"milk_feed_count"`
	CreatedAt     string   `json:"created_at"`
}
type Reason struct {
	Code     string          `json:"code"`
	Level    string          `json:"level"`
	Title    string          `json:"title"`
	Message  string          `json:"message"`
	Evidence json.RawMessage `json:"evidence"`
}
type Evaluation struct {
	PerMeasurement []EvaluatedPoint `json:"per_measurement"`
	Level          string           `json:"level"`
	Reasons        []Reason         `json:"reasons"`
	NextKpsp       json.RawMessage  `json:"next_kpsp"`
	Diet           json.RawMessage  `json:"diet"`
}
type EvaluatedPoint struct {
	ID                string              `json:"id"`
	AgeDays           int                 `json:"age_days"`
	CorrectedLengthCm *float64            `json:"corrected_length_cm"`
	Z                 map[string]*float64 `json:"z"`
	Classification    map[string]string   `json:"classification"`
	Flags             []string            `json:"flags"`
}
type Status struct {
	ChildID    string          `json:"child_id"`
	AsOf       string          `json:"as_of"`
	AgeDays    int             `json:"age_days"`
	AgeMonths  float64         `json:"age_months"`
	Level      string          `json:"level"`
	LevelLabel string          `json:"level_label"`
	Latest     any             `json:"latest"`
	Reasons    []Reason        `json:"reasons"`
	NextKpsp   json.RawMessage `json:"next_kpsp"`
	Diet       json.RawMessage `json:"diet"`
}
type EngineMeasurement struct {
	ID                  string   `json:"id"`
	MeasuredAt          string   `json:"measured_at"`
	WeightKg            float64  `json:"weight_kg"`
	LengthHeightCm      *float64 `json:"length_height_cm"`
	Position            *string  `json:"position"`
	HeadCircumferenceCm *float64 `json:"head_circumference_cm"`
	Source              string   `json:"source"`
}
type EngineKpsp struct {
	QuestionnaireAgeMonths int    `json:"questionnaire_age_months"`
	AnsweredAt             string `json:"answered_at"`
	Result                 string `json:"result"`
}
type EngineFoodRecall struct {
	RecallDate    string   `json:"recall_date"`
	Breastfed     bool     `json:"breastfed"`
	FoodGroups    []string `json:"food_groups"`
	MealCount     int      `json:"meal_count"`
	MilkFeedCount *int     `json:"milk_feed_count"`
}
