-- Pengukuran DEMO fiktif untuk Anisa, Bima, Citra (kontrak, bagian "Skenario demo").
-- Bukan data anak sungguhan. Angka dihitung dari tabel WHO (inverse LMS) pada z-score sasaran,
-- dibulatkan 0,1, lalu diverifikasi dengan engine asli: lihat docs/SETUP.md "Data demo".
--   Anisa: green (6-9 bln) -> yellow WEIGHT_NOT_GAINING (10 bln) -> red WEIGHT_NOT_GAINING_2X (11 bln), lhfa ~ -0,3
--   Bima : green, z ~ +0,2 sepanjang 9-13 bln
--   Citra: red STUNTED, lhfa ~ -2,5 sejak 12 bln
-- Tanggal = birth_date + umur bulan, jadi tetap konsisten dengan 002 kapan pun dijalankan.
-- Jalankan SETELAH 002 pada hari yang sama: psql -U postgres -d tumbuh -f migrations/005_seed_demo_measurements.sql
-- Aman diulang (ON CONFLICT DO NOTHING).
BEGIN;
INSERT INTO measurements (id,child_id,measured_at,weight_kg,length_height_cm,position,head_circumference_cm,source)
SELECT gen_random_uuid(), c.id, (c.birth_date + make_interval(months => v.age_m))::date,
       v.w, v.l, 'recumbent', v.hc, 'posyandu'
FROM children c
JOIN (VALUES
  ('Anisa', 6, 7.3, 65.0, 42.2), ('Anisa', 7, 7.6, 66.5, 42.8), ('Anisa', 8, 7.9, 68.0, 43.4),
  ('Anisa', 9, 8.2, 69.4, 43.8), ('Anisa', 10, 8.2, 70.7, 44.2), ('Anisa', 11, 8.2, 72.0, 44.6),
  ('Bima', 9, 9.1, 72.2, 45.0), ('Bima', 10, 9.4, 73.5, 45.4), ('Bima', 11, 9.6, 74.8, 45.8),
  ('Bima', 12, 9.9, 76.0, 46.1), ('Bima', 13, 10.1, 77.2, 46.3),
  ('Citra', 12, 7.5, 67.6, 43.8), ('Citra', 13, 7.7, 68.7, 44.1), ('Citra', 14, 7.8, 69.7, 44.3),
  ('Citra', 15, 8.0, 70.7, 44.6)
) AS v(name, age_m, w, l, hc) ON v.name = c.name
WHERE c.parent_id = '00000000-0000-4000-8000-000000000001'
  AND (c.birth_date + make_interval(months => v.age_m))::date <= CURRENT_DATE
ON CONFLICT (child_id, measured_at) DO NOTHING;
COMMIT;
