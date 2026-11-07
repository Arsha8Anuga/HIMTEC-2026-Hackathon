-- PostgreSQL 13+, skema sesuai docs/CONTRACT.md v0.4.
CREATE TABLE IF NOT EXISTS children (
    id UUID PRIMARY KEY,
    name VARCHAR(60) NOT NULL CHECK (char_length(name) BETWEEN 1 AND 60),
    sex VARCHAR(6) NOT NULL CHECK (sex IN ('male','female')),
    birth_date DATE NOT NULL,
    birth_weight_kg DOUBLE PRECISION CHECK (birth_weight_kg BETWEEN 0.5 AND 6.0),
    birth_length_cm DOUBLE PRECISION CHECK (birth_length_cm BETWEEN 30 AND 60),
    is_preterm BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS measurements (
    id UUID PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    measured_at DATE NOT NULL,
    weight_kg DOUBLE PRECISION NOT NULL CHECK (weight_kg BETWEEN 0.5 AND 40),
    length_height_cm DOUBLE PRECISION CHECK (length_height_cm BETWEEN 40 AND 130),
    position VARCHAR(9) CHECK (position IN ('recumbent','standing')),
    head_circumference_cm DOUBLE PRECISION CHECK (head_circumference_cm BETWEEN 30 AND 60),
    source VARCHAR(10) NOT NULL CHECK (source IN ('posyandu','puskesmas','home')),
    note VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT measurements_position_required CHECK (length_height_cm IS NULL OR position IS NOT NULL),
    CONSTRAINT measurements_one_per_date UNIQUE(child_id,measured_at)
);
CREATE INDEX IF NOT EXISTS measurements_child_date ON measurements(child_id,measured_at DESC);
CREATE TABLE IF NOT EXISTS kpsp_results (
    id UUID PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    questionnaire_age_months INTEGER NOT NULL CHECK (questionnaire_age_months IN (3,6,9,12,15,18,21,24,30,36,42,48,54,60)),
    answered_at DATE NOT NULL,
    answers JSONB NOT NULL,
    yes_count INTEGER NOT NULL CHECK (yes_count BETWEEN 0 AND 10),
    result VARCHAR(12) NOT NULL CHECK (result IN ('sesuai','meragukan','penyimpangan')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS kpsp_results_child_date ON kpsp_results(child_id,answered_at DESC);
CREATE TABLE IF NOT EXISTS food_recalls (
    id UUID PRIMARY KEY,
    child_id UUID NOT NULL REFERENCES children(id) ON DELETE CASCADE,
    recall_date DATE NOT NULL,
    breastfed BOOLEAN NOT NULL,
    food_groups JSONB NOT NULL DEFAULT '[]'::jsonb,
    meal_count INTEGER NOT NULL CHECK (meal_count BETWEEN 0 AND 10),
    milk_feed_count INTEGER CHECK (milk_feed_count BETWEEN 0 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT food_recalls_one_per_date UNIQUE(child_id,recall_date)
);
CREATE INDEX IF NOT EXISTS food_recalls_child_date ON food_recalls(child_id,recall_date DESC);
