-- PRD: MVP has one demo parent; authentication is a later feature.
-- Run after 001_init.sql. Safe for both existing and new databases.
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE,
    email TEXT UNIQUE,
    role TEXT NOT NULL CHECK (role IN ('parent', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO users (id, name, role)
VALUES ('00000000-0000-4000-8000-000000000001', 'Orang Tua Demo', 'parent')
ON CONFLICT (id) DO NOTHING;

-- Never reactivate a disabled account or reuse an admin as the demo parent.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM users
        WHERE id = '00000000-0000-4000-8000-000000000001'
          AND role = 'parent' AND is_active
    ) THEN
        RAISE EXCEPTION 'Akun orang tua demo tidak aktif atau role tidak sesuai';
    END IF;
END $$;

ALTER TABLE children ADD COLUMN IF NOT EXISTS parent_id UUID;
-- Adopt only legacy rows without an owner. Keep existing ownership intact.
UPDATE children SET parent_id = '00000000-0000-4000-8000-000000000001'
WHERE parent_id IS NULL;
ALTER TABLE children ALTER COLUMN parent_id SET NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'children'::regclass
          AND conname = 'children_parent_id_fkey'
    ) THEN
        ALTER TABLE children ADD CONSTRAINT children_parent_id_fkey
            FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS children_parent_created ON children(parent_id, created_at);

-- PRD permits adapting storage types while preserving public JSON. Existing
-- PRD-created databases may use text[]; the Go repository stores JSONB arrays.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_attribute
        WHERE attrelid = 'food_recalls'::regclass AND attname = 'food_groups'
          AND atttypid = 'text[]'::regtype AND NOT attisdropped
    ) THEN
        ALTER TABLE food_recalls ALTER COLUMN food_groups DROP DEFAULT;
        ALTER TABLE food_recalls ALTER COLUMN food_groups TYPE JSONB
            USING to_jsonb(food_groups);
        ALTER TABLE food_recalls ALTER COLUMN food_groups SET DEFAULT '[]'::jsonb;
    END IF;
END $$;
