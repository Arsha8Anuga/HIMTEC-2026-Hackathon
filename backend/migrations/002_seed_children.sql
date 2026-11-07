-- HANYA data identitas fiktif untuk demo; pengukuran demo ada di 005 (dihitung dari tabel WHO, diverifikasi engine).
-- Jalankan opsional dengan psql -f migrations/002_seed_children.sql.
-- Jalankan startup backend sekali agar migrasi 001 + 003 selesai.
BEGIN;
INSERT INTO children (id,name,sex,birth_date,is_preterm,parent_id)
SELECT gen_random_uuid(), 'Anisa', 'female', (CURRENT_DATE - INTERVAL '11 months')::date, false, u.id
FROM users u WHERE u.id='00000000-0000-4000-8000-000000000001' AND u.role='parent' AND u.is_active
AND NOT EXISTS (SELECT 1 FROM children c WHERE c.name='Anisa' AND c.parent_id=u.id);
INSERT INTO children (id,name,sex,birth_date,is_preterm,parent_id)
SELECT gen_random_uuid(), 'Bima', 'male', (CURRENT_DATE - INTERVAL '13 months')::date, false, u.id
FROM users u WHERE u.id='00000000-0000-4000-8000-000000000001' AND u.role='parent' AND u.is_active
AND NOT EXISTS (SELECT 1 FROM children c WHERE c.name='Bima' AND c.parent_id=u.id);
INSERT INTO children (id,name,sex,birth_date,is_preterm,parent_id)
SELECT gen_random_uuid(), 'Citra', 'female', (CURRENT_DATE - INTERVAL '15 months')::date, false, u.id
FROM users u WHERE u.id='00000000-0000-4000-8000-000000000001' AND u.role='parent' AND u.is_active
AND NOT EXISTS (SELECT 1 FROM children c WHERE c.name='Citra' AND c.parent_id=u.id);
COMMIT;
