-- HANYA data identitas fiktif untuk demo; pengukuran medis jangan dikarang.
-- Jalankan opsional dengan psql -f migrations/002_seed_children.sql.
INSERT INTO children (id,name,sex,birth_date,is_preterm)
SELECT gen_random_uuid(), 'Anisa', 'female', (CURRENT_DATE - INTERVAL '11 months')::date, false
WHERE NOT EXISTS (SELECT 1 FROM children WHERE name='Anisa');
INSERT INTO children (id,name,sex,birth_date,is_preterm)
SELECT gen_random_uuid(), 'Bima', 'male', (CURRENT_DATE - INTERVAL '13 months')::date, false
WHERE NOT EXISTS (SELECT 1 FROM children WHERE name='Bima');
INSERT INTO children (id,name,sex,birth_date,is_preterm)
SELECT gen_random_uuid(), 'Citra', 'female', (CURRENT_DATE - INTERVAL '15 months')::date, false
WHERE NOT EXISTS (SELECT 1 FROM children WHERE name='Citra');
