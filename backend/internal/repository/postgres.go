package repository

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
	_ "github.com/lib/pq"
)

// DemoParentID is server-owned MVP context, never accepted from public JSON.
const DemoParentID = "00000000-0000-4000-8000-000000000001"

type Store struct {
	DB       *sql.DB
	ParentID string
}

func (s *Store) parentID() string {
	if s.ParentID != "" {
		return s.ParentID
	}
	return DemoParentID
}

func Open(databaseURL string) (*Store, error) {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(30 * time.Minute)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err = db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("koneksi PostgreSQL: %w", err)
	}
	return &Store{DB: db, ParentID: DemoParentID}, nil
}
func (s *Store) Migrate(ctx context.Context, directory string) error {
	// 002 is an optional demo seed, not a startup migration.
	names := []string{"001_init.sql", "003_demo_parent.sql", "004_otp_auth.sql"}
	scripts := make([][]byte, 0, len(names))
	for _, name := range names {
		b, err := os.ReadFile(filepath.Join(directory, name))
		if err != nil {
			return err
		}
		scripts = append(scripts, b)
	}
	tx, err := s.DB.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	// Serialize concurrent startup migrations within this database.
	if _, err := tx.ExecContext(ctx, `SELECT pg_advisory_xact_lock(hashtext('himtec_backend_schema'))`); err != nil {
		return err
	}
	for i, script := range scripts {
		if _, err := tx.ExecContext(ctx, string(script)); err != nil {
			return fmt.Errorf("%s: %w", names[i], err)
		}
	}
	return tx.Commit()
}
func UUID() (string, error) {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "", err
	}
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[:4], b[4:6], b[6:8], b[8:10], b[10:]), nil
}
func timestamp(t time.Time) string { return t.Local().Format(time.RFC3339) }
func ptrFloat(v sql.NullFloat64) *float64 {
	if !v.Valid {
		return nil
	}
	return &v.Float64
}
func ptrString(v sql.NullString) *string {
	if !v.Valid {
		return nil
	}
	return &v.String
}
func ptrInt(v sql.NullInt64) *int {
	if !v.Valid {
		return nil
	}
	n := int(v.Int64)
	return &n
}
func sqlBool(v *bool) bool { return v != nil && *v }

const childColumns = `id, name, sex, birth_date::text, birth_weight_kg, birth_length_cm, is_preterm, created_at`

func scanChild(s interface{ Scan(...any) error }) (model.Child, error) {
	var x model.Child
	var bw, bl sql.NullFloat64
	var created time.Time
	err := s.Scan(&x.ID, &x.Name, &x.Sex, &x.BirthDate, &bw, &bl, &x.IsPreterm, &created)
	x.BirthWeightKg = ptrFloat(bw)
	x.BirthLengthCm = ptrFloat(bl)
	x.CreatedAt = timestamp(created)
	return x, err
}
func (s *Store) Children(ctx context.Context) ([]model.Child, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT `+childColumns+` FROM children WHERE parent_id=$1 AND EXISTS (SELECT 1 FROM users WHERE id=$1 AND role='parent' AND is_active) ORDER BY created_at, name`, s.parentID())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]model.Child, 0)
	for rows.Next() {
		x, err := scanChild(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, x)
	}
	return out, rows.Err()
}
func (s *Store) Child(ctx context.Context, id string) (model.Child, error) {
	return scanChild(s.DB.QueryRowContext(ctx, `SELECT `+childColumns+` FROM children WHERE id=$1 AND parent_id=$2 AND EXISTS (SELECT 1 FROM users WHERE id=$2 AND role='parent' AND is_active)`, id, s.parentID()))
}
func (s *Store) AddChild(ctx context.Context, x model.ChildInput) (model.Child, error) {
	id, err := UUID()
	if err != nil {
		return model.Child{}, err
	}
	return scanChild(s.DB.QueryRowContext(ctx, `INSERT INTO children(id,name,sex,birth_date,birth_weight_kg,birth_length_cm,is_preterm,parent_id) SELECT $1,$2,$3,$4,$5,$6,$7,id FROM users WHERE id=$8 AND role='parent' AND is_active RETURNING `+childColumns,
		id, x.Name, x.Sex, x.BirthDate, x.BirthWeightKg, x.BirthLengthCm, sqlBool(x.IsPreterm), s.parentID()))
}

const measurementColumns = `id, child_id, measured_at::text, weight_kg, length_height_cm, position, head_circumference_cm, source, note, created_at`

func scanMeasurement(s interface{ Scan(...any) error }) (model.Measurement, error) {
	var m model.Measurement
	var height, head sql.NullFloat64
	var pos, note sql.NullString
	var created time.Time
	err := s.Scan(&m.ID, &m.ChildID, &m.MeasuredAt, &m.WeightKg, &height, &pos, &head, &m.Source, &note, &created)
	m.LengthHeightCm = ptrFloat(height)
	m.Position = ptrString(pos)
	m.HeadCircumferenceCm = ptrFloat(head)
	m.Note = ptrString(note)
	m.CreatedAt = timestamp(created)
	return m, err
}
func (s *Store) Measurements(ctx context.Context, childID string) ([]model.Measurement, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT `+measurementColumns+` FROM measurements WHERE child_id=$1 AND EXISTS (SELECT 1 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$1 AND c.parent_id=$2 AND u.role='parent' AND u.is_active) ORDER BY measured_at DESC,created_at DESC`, childID, s.parentID())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]model.Measurement, 0)
	for rows.Next() {
		m, err := scanMeasurement(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}
func (s *Store) AddMeasurement(ctx context.Context, childID string, x model.MeasurementInput) (model.Measurement, error) {
	id, err := UUID()
	if err != nil {
		return model.Measurement{}, err
	}
	return scanMeasurement(s.DB.QueryRowContext(ctx, `INSERT INTO measurements(id,child_id,measured_at,weight_kg,length_height_cm,position,head_circumference_cm,source,note) SELECT $1,$2,$3,$4,$5,$6,$7,$8,$9 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$2 AND c.parent_id=$10 AND u.role='parent' AND u.is_active RETURNING `+measurementColumns,
		id, childID, x.MeasuredAt, x.WeightKg, x.LengthHeightCm, x.Position, x.HeadCircumferenceCm, x.Source, x.Note, s.parentID()))
}
func (s *Store) DeleteMeasurement(ctx context.Context, childID, measurementID string) (bool, error) {
	r, err := s.DB.ExecContext(ctx, `DELETE FROM measurements WHERE id=$1 AND child_id=$2 AND EXISTS (SELECT 1 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$2 AND c.parent_id=$3 AND u.role='parent' AND u.is_active)`, measurementID, childID, s.parentID())
	if err != nil {
		return false, err
	}
	n, err := r.RowsAffected()
	return n > 0, err
}

const kpspColumns = `id, child_id, questionnaire_age_months, answered_at::text, answers, yes_count, result, created_at`

func scanKpsp(s interface{ Scan(...any) error }) (model.KpspResult, error) {
	var k model.KpspResult
	var raw []byte
	var created time.Time
	err := s.Scan(&k.ID, &k.ChildID, &k.QuestionnaireAgeMonths, &k.AnsweredAt, &raw, &k.YesCount, &k.Result, &created)
	if err == nil {
		err = json.Unmarshal(raw, &k.Answers)
	}
	k.CreatedAt = timestamp(created)
	return k, err
}
func (s *Store) Kpsp(ctx context.Context, childID string) ([]model.KpspResult, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT `+kpspColumns+` FROM kpsp_results WHERE child_id=$1 AND EXISTS (SELECT 1 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$1 AND c.parent_id=$2 AND u.role='parent' AND u.is_active) ORDER BY answered_at DESC,created_at DESC`, childID, s.parentID())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]model.KpspResult, 0)
	for rows.Next() {
		x, e := scanKpsp(rows)
		if e != nil {
			return nil, e
		}
		out = append(out, x)
	}
	return out, rows.Err()
}
func (s *Store) AddKpsp(ctx context.Context, childID string, x model.KpspInput, yesCount int, result string) (model.KpspResult, error) {
	id, err := UUID()
	if err != nil {
		return model.KpspResult{}, err
	}
	b, err := json.Marshal(x.Answers)
	if err != nil {
		return model.KpspResult{}, err
	}
	return scanKpsp(s.DB.QueryRowContext(ctx, `INSERT INTO kpsp_results(id,child_id,questionnaire_age_months,answered_at,answers,yes_count,result) SELECT $1,$2,$3,$4,$5::jsonb,$6,$7 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$2 AND c.parent_id=$8 AND u.role='parent' AND u.is_active RETURNING `+kpspColumns, id, childID, x.QuestionnaireAgeMonths, x.AnsweredAt, string(b), yesCount, result, s.parentID()))
}

const foodColumns = `id, child_id, recall_date::text, breastfed, food_groups, meal_count, milk_feed_count, created_at`

func scanFood(s interface{ Scan(...any) error }) (model.FoodRecall, error) {
	var f model.FoodRecall
	var raw []byte
	var milk sql.NullInt64
	var created time.Time
	err := s.Scan(&f.ID, &f.ChildID, &f.RecallDate, &f.Breastfed, &raw, &f.MealCount, &milk, &created)
	if err == nil {
		err = json.Unmarshal(raw, &f.FoodGroups)
	}
	f.MilkFeedCount = ptrInt(milk)
	f.CreatedAt = timestamp(created)
	return f, err
}
func (s *Store) Foods(ctx context.Context, childID string) ([]model.FoodRecall, error) {
	rows, err := s.DB.QueryContext(ctx, `SELECT `+foodColumns+` FROM food_recalls WHERE child_id=$1 AND recall_date >= CURRENT_DATE-13 AND recall_date <= CURRENT_DATE AND EXISTS (SELECT 1 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$1 AND c.parent_id=$2 AND u.role='parent' AND u.is_active) ORDER BY recall_date DESC`, childID, s.parentID())
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]model.FoodRecall, 0)
	for rows.Next() {
		x, e := scanFood(rows)
		if e != nil {
			return nil, e
		}
		out = append(out, x)
	}
	return out, rows.Err()
}
func (s *Store) AddFood(ctx context.Context, childID string, x model.FoodRecallInput) (model.FoodRecall, error) {
	id, err := UUID()
	if err != nil {
		return model.FoodRecall{}, err
	}
	b, err := json.Marshal(x.FoodGroups)
	if err != nil {
		return model.FoodRecall{}, err
	}
	return scanFood(s.DB.QueryRowContext(ctx, `INSERT INTO food_recalls(id,child_id,recall_date,breastfed,food_groups,meal_count,milk_feed_count) SELECT $1,$2,$3,$4,$5::jsonb,$6,$7 FROM children c JOIN users u ON u.id=c.parent_id WHERE c.id=$2 AND c.parent_id=$8 AND u.role='parent' AND u.is_active RETURNING `+foodColumns, id, childID, x.RecallDate, sqlBool(x.Breastfed), string(b), x.MealCount, x.MilkFeedCount, s.parentID()))
}
