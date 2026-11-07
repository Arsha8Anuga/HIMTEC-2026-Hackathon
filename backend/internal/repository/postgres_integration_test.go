package repository

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Arsha8Anuga/HIMTEC-2026-Hackathon/backend/internal/model"
)

// Optional SQL integration suite. Each test creates its own schema and removes
// only that schema. Use a dedicated test database, never production/demo data.
func integrationStore(t *testing.T) (*Store, context.Context) {
	t.Helper()
	dsn := os.Getenv("BACKEND_TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("set BACKEND_TEST_DATABASE_URL for PostgreSQL integration tests")
	}
	u, err := url.Parse(dsn)
	if err != nil || (u.Scheme != "postgres" && u.Scheme != "postgresql") {
		t.Fatal("test DSN must be a postgres:// URL")
	}
	admin, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Fatal(err)
	}
	admin.SetMaxOpenConns(1)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	t.Cleanup(cancel)
	id, err := UUID()
	if err != nil {
		t.Fatal(err)
	}
	schema := "backend_test_" + strings.ReplaceAll(id, "-", "")
	if _, err = admin.ExecContext(ctx, "CREATE SCHEMA "+schema); err != nil {
		admin.Close()
		t.Fatal(err)
	}
	admin.Close()
	cleanup := func() {
		cleanupCtx, done := context.WithTimeout(context.Background(), 10*time.Second)
		defer done()
		connection, err := sql.Open("postgres", dsn)
		if err != nil {
			t.Errorf("schema cleanup connection: %v", err)
			return
		}
		defer connection.Close()
		if _, err = connection.ExecContext(cleanupCtx, "DROP SCHEMA "+schema+" CASCADE"); err != nil {
			t.Errorf("schema cleanup: %v", err)
		}
	}
	q := u.Query()
	q.Set("search_path", schema)
	u.RawQuery = q.Encode()
	s, err := Open(u.String())
	if err != nil {
		cleanup()
		t.Fatal(err)
	}
	s.DB.SetMaxOpenConns(1)
	// Explicit SET also supports SQL test servers that ignore startup GUCs.
	if _, err := s.DB.ExecContext(ctx, "SET search_path TO "+schema); err != nil {
		s.DB.Close()
		cleanup()
		t.Fatal(err)
	}
	var currentSchema string
	if err := s.DB.QueryRowContext(ctx, "SELECT current_schema()").Scan(&currentSchema); err != nil || currentSchema != schema {
		s.DB.Close()
		cleanup()
		t.Fatalf("schema isolation failed: %q %v", currentSchema, err)
	}
	t.Cleanup(func() {
		s.DB.Close()
		cleanup()
	})
	return s, ctx
}

func migrateTest(t *testing.T, s *Store, ctx context.Context) {
	t.Helper()
	if err := s.Migrate(ctx, filepath.Join("..", "..", "migrations")); err != nil {
		t.Fatal(err)
	}
}

func TestPostgresFreshMigrationAndSeed(t *testing.T) {
	s, ctx := integrationStore(t)
	migrateTest(t, s, ctx)
	migrateTest(t, s, ctx)
	var tables, users, children int
	if err := s.DB.QueryRowContext(ctx, `SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema() AND table_type='BASE TABLE'`).Scan(&tables); err != nil {
		t.Fatal(err)
	}
	if err := s.DB.QueryRowContext(ctx, `SELECT count(*) FROM users WHERE id=$1 AND role='parent' AND is_active`, DemoParentID).Scan(&users); err != nil {
		t.Fatal(err)
	}
	if err := s.DB.QueryRowContext(ctx, `SELECT count(*) FROM children`).Scan(&children); err != nil {
		t.Fatal(err)
	}
	if tables != 5 || users != 1 || children != 0 {
		t.Fatalf("tables=%d demo_users=%d children=%d", tables, users, children)
	}
	seed, err := os.ReadFile(filepath.Join("..", "..", "migrations", "002_seed_children.sql"))
	if err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 2; i++ {
		if _, err = s.DB.ExecContext(ctx, string(seed)); err != nil {
			t.Fatal(err)
		}
	}
	if err := s.DB.QueryRowContext(ctx, `SELECT count(*) FROM children WHERE parent_id=$1`, DemoParentID).Scan(&children); err != nil {
		t.Fatal(err)
	}
	if children != 3 {
		t.Fatalf("seed not idempotent: %d", children)
	}
}

func TestPostgresLegacyMigrationPreservesDataAndOwnership(t *testing.T) {
	s, ctx := integrationStore(t)
	legacy, err := os.ReadFile(filepath.Join("..", "..", "migrations", "001_init.sql"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = s.DB.ExecContext(ctx, string(legacy)); err != nil {
		t.Fatal(err)
	}
	const legacyChild = "11111111-1111-4111-8111-111111111111"
	if _, err = s.DB.ExecContext(ctx, `INSERT INTO children(id,name,sex,birth_date) VALUES($1,'Legacy Demo','female','2026-01-01')`, legacyChild); err != nil {
		t.Fatal(err)
	}
	if _, err = s.DB.ExecContext(ctx, `INSERT INTO measurements(id,child_id,measured_at,weight_kg,source,note) VALUES('11111111-1111-4111-8111-111111111112',$1,'2026-02-01',8,'home','synthetic legacy fixture')`, legacyChild); err != nil {
		t.Fatal(err)
	}
	migrateTest(t, s, ctx)
	child, err := s.Child(ctx, legacyChild)
	if err != nil || child.Name != "Legacy Demo" {
		t.Fatalf("legacy child lost: %+v %v", child, err)
	}
	ms, err := s.Measurements(ctx, legacyChild)
	if err != nil || len(ms) != 1 || ms[0].Note == nil || *ms[0].Note != "synthetic legacy fixture" {
		t.Fatalf("legacy measurements lost: %+v %v", ms, err)
	}
	const other = "22222222-2222-4222-8222-222222222222"
	if _, err = s.DB.ExecContext(ctx, `INSERT INTO users(id,name,role) VALUES($1,'Other Parent','parent')`, other); err != nil {
		t.Fatal(err)
	}
	if _, err = s.DB.ExecContext(ctx, `UPDATE children SET parent_id=$1 WHERE id=$2`, other, legacyChild); err != nil {
		t.Fatal(err)
	}
	migrateTest(t, s, ctx)
	var owner string
	if err := s.DB.QueryRowContext(ctx, `SELECT parent_id FROM children WHERE id=$1`, legacyChild).Scan(&owner); err != nil {
		t.Fatal(err)
	}
	if owner != other {
		t.Fatal("migration reassigned an existing owner")
	}
	if _, err := s.Child(ctx, legacyChild); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("foreign child visible: %v", err)
	}
}

func TestPostgresParentIsolationAcrossRepositories(t *testing.T) {
	s, ctx := integrationStore(t)
	migrateTest(t, s, ctx)
	const otherID = "22222222-2222-4222-8222-222222222222"
	if _, err := s.DB.ExecContext(ctx, `INSERT INTO users(id,name,role) VALUES($1,'Other Parent','parent')`, otherID); err != nil {
		t.Fatal(err)
	}
	other := &Store{DB: s.DB, ParentID: otherID}
	birth := time.Now().AddDate(0, -9, 0).Format("2006-01-02")
	today := time.Now().Format("2006-01-02")
	input := model.ChildInput{Name: "Synthetic Child", Sex: "female", BirthDate: birth}
	mine, err := s.AddChild(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	theirs, err := other.AddChild(ctx, input)
	if err != nil {
		t.Fatal(err)
	}
	list, err := s.Children(ctx)
	if err != nil || len(list) != 1 || list[0].ID != mine.ID {
		t.Fatalf("list scope: %+v %v", list, err)
	}
	if _, err := s.Child(ctx, theirs.ID); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("foreign child visible: %v", err)
	}
	b, _ := json.Marshal(mine)
	if strings.Contains(string(b), "parent_id") {
		t.Fatal("public Child JSON changed")
	}
	w := 8.0
	m := model.MeasurementInput{MeasuredAt: today, WeightKg: &w, Source: "posyandu"}
	foreignMeasurement, err := other.AddMeasurement(ctx, theirs.ID, m)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.AddMeasurement(ctx, theirs.ID, m); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("foreign measurement write allowed: %v", err)
	}
	if rows, err := s.Measurements(ctx, theirs.ID); err != nil || len(rows) != 0 {
		t.Fatalf("foreign measurement read allowed: %+v %v", rows, err)
	}
	if deleted, err := s.DeleteMeasurement(ctx, theirs.ID, foreignMeasurement.ID); err != nil || deleted {
		t.Fatalf("foreign delete allowed: %v %v", deleted, err)
	}
	if _, err := s.AddMeasurement(ctx, mine.ID, m); err != nil {
		t.Fatal(err)
	}
	yes := true
	meals := 3
	f := model.FoodRecallInput{RecallDate: today, Breastfed: &yes, FoodGroups: []string{}, MealCount: &meals}
	if _, err := s.AddFood(ctx, theirs.ID, f); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("foreign food write allowed: %v", err)
	}
	if _, err := other.AddFood(ctx, theirs.ID, f); err != nil {
		t.Fatal(err)
	}
	if rows, err := s.Foods(ctx, theirs.ID); err != nil || len(rows) != 0 {
		t.Fatalf("foreign food read allowed: %+v %v", rows, err)
	}
	if _, err := s.AddFood(ctx, mine.ID, f); err != nil {
		t.Fatal(err)
	}
	answers := make([]model.Answer, 10)
	for i := range answers {
		answers[i] = model.Answer{ItemNo: i + 1, Answer: &yes}
	}
	k := model.KpspInput{QuestionnaireAgeMonths: 9, AnsweredAt: today, Answers: answers}
	if _, err := s.AddKpsp(ctx, theirs.ID, k, 10, "sesuai"); !errors.Is(err, sql.ErrNoRows) {
		t.Fatalf("foreign KPSP write allowed: %v", err)
	}
	if _, err := other.AddKpsp(ctx, theirs.ID, k, 10, "sesuai"); err != nil {
		t.Fatal(err)
	}
	if rows, err := s.Kpsp(ctx, theirs.ID); err != nil || len(rows) != 0 {
		t.Fatalf("foreign KPSP read allowed: %+v %v", rows, err)
	}
	if _, err := s.AddKpsp(ctx, mine.ID, k, 10, "sesuai"); err != nil {
		t.Fatal(err)
	}
	for _, account := range []struct {
		role   string
		active bool
	}{{"parent", false}, {"admin", true}, {"admin", false}} {
		if _, err := s.DB.ExecContext(ctx, `UPDATE users SET role=$1,is_active=$2 WHERE id=$3`, account.role, account.active, DemoParentID); err != nil {
			t.Fatal(err)
		}
		if rows, err := s.Children(ctx); err != nil || len(rows) != 0 {
			t.Fatalf("disabled account read allowed: %+v %v", rows, err)
		}
		if _, err := s.AddChild(ctx, input); !errors.Is(err, sql.ErrNoRows) {
			t.Fatalf("disabled account write allowed: %v", err)
		}
	}
}

func TestPostgresPrdArrayStorageUpgradesWithoutLosingValues(t *testing.T) {
	s, ctx := integrationStore(t)
	legacy, err := os.ReadFile(filepath.Join("..", "..", "migrations", "001_init.sql"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err = s.DB.ExecContext(ctx, string(legacy)); err != nil {
		t.Fatal(err)
	}
	if _, err = s.DB.ExecContext(ctx, `ALTER TABLE food_recalls ALTER COLUMN food_groups DROP DEFAULT;
ALTER TABLE food_recalls ALTER COLUMN food_groups TYPE text[] USING ARRAY[]::text[];
ALTER TABLE food_recalls ALTER COLUMN food_groups SET DEFAULT '{}'::text[];
INSERT INTO children(id,name,sex,birth_date) VALUES('11111111-1111-4111-8111-111111111111','PRD Demo','female','2026-01-01');
INSERT INTO food_recalls(id,child_id,recall_date,breastfed,food_groups,meal_count) VALUES('11111111-1111-4111-8111-111111111112','11111111-1111-4111-8111-111111111111',CURRENT_DATE,true,ARRAY['eggs','dairy'],3)`); err != nil {
		t.Fatal(err)
	}
	migrateTest(t, s, ctx)
	migrateTest(t, s, ctx)
	rows, err := s.Foods(ctx, "11111111-1111-4111-8111-111111111111")
	if err != nil || len(rows) != 1 || strings.Join(rows[0].FoodGroups, ",") != "eggs,dairy" {
		t.Fatalf("PRD groups lost: %+v %v", rows, err)
	}
}

func TestPostgresMigrationRollsBackOnFailure(t *testing.T) {
	s, ctx := integrationStore(t)
	dir := t.TempDir()
	initial, err := os.ReadFile(filepath.Join("..", "..", "migrations", "001_init.sql"))
	if err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "001_init.sql"), initial, 0600); err != nil {
		t.Fatal(err)
	}
	if err = os.WriteFile(filepath.Join(dir, "003_demo_parent.sql"), []byte("SELECT invalid_migration_function();"), 0600); err != nil {
		t.Fatal(err)
	}
	if err = s.Migrate(ctx, dir); err == nil {
		t.Fatal("broken migration accepted")
	}
	var count int
	if err = s.DB.QueryRowContext(ctx, `SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema()`).Scan(&count); err != nil {
		t.Fatal(err)
	}
	if count != 0 {
		t.Fatalf("partial migration left %d tables", count)
	}
}
