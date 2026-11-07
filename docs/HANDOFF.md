# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Diperbarui:** 2026-11-07 10:37 WIB (patch ZIP 03 + koreksi dokumentasi)
- **Selesai:** Patch 01: dependensi Python; patch 02: fondasi FastAPI, validasi Pydantic, amplop error dan `/engine/v1/health`; patch 03: loader kelima berkas LMS WHO asli (`weianthro`, `lenanthro`, `wflanthro`, `wfhanthro`, `hcanthro`) dari WHO Anthro official yang dipin ke commit `b776d8a12b1c97369c748b561159fd2ec4f4db58` dan checksum Git blob; deteksi data hilang, diubah, tidak lengkap; lookup eksak terpisah per sex/indikator; skrip `scripts/fetch_who_tables.py` untuk setup; panduan dan atribusi `engine/data/who/README.md`. 48 tes pytest lulus (termasuk 26 tes sebelumnya).
- **Sedang dikerjakan:** data WHO asli belum diunduh di sandbox karena jaringan tidak tersedia; skrip unduh sudah disiapkan untuk dijalankan sekali di laptop tim yang terhubung internet. Data WHO tidak dibundel ke ZIP ini.
- **Belum dimulai:** kalkulasi z-score LMS/restricted LMS, koreksi posisi, klasifikasi Permenkes, alasan peringatan, `/growth/evaluate`, `/reference`, `/kpsp/questionnaire`, `/kpsp/score`, IYCF, dan 5 kasus pembanding WHO Anthro.
- **Cara menjalankan dan menguji:** `cd engine && python -m pip install -r requirements.txt && python -m pytest -q` (hasil patch: `48 passed`). Dengan internet saat persiapan: `python scripts/fetch_who_tables.py`, lalu cek `GET /engine/v1/health`. Setelah tabel WHO lengkap dan valid terpasang, `who_tables_loaded` akan bernilai `true` (ini **bukan** tanda perhitungan medis siap). Server: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001`. Saat demo tidak memerlukan internet.
- **Masalah yang diketahui:** `/health` tetap `who_tables_loaded=false` sampai berkas resmi diunduh; tidak ada endpoint evaluasi medis pada patch ini. WHO Anthro tabel berbasis umur 0–1826 hari, sedangkan kontrak v0.4 menerima hingga 1856 hari; **jangan ekstrapolasi** sampai diputuskan pemilik kontrak. Data BB/PB atau BB/TB punya resolusi 0,1 cm sehingga kebijakan penanganan input lebih presisi perlu ditetapkan. Kontrak v0.4 masih draf, dan skema body `/kpsp/score` belum eksplisit. Lisensi GPL-3 WHO Anthro perlu ditinjau sebelum membundel/redistribusi data.
- **Butuh dari orang lain:** pemilik kontrak mengonfirmasi batas umur dan aturan presisi 0,1 cm; mengunci kontrak v1.0 dan skema `/kpsp/score`; backend mengirim `food_recalls` sebagai array (boleh kosong) sesuai v0.4. Tim menjalankan unduh tabel WHO di mesin yang memiliki akses internet pada tahap persiapan, bukan saat demo.
- **Catatan hotfix dokumentasi:** versi awal ZIP Patch 02/03 memakai snapshot dokumentasi lama dan berisiko menimpa kemajuan tim backend. ZIP hotfix ini memakai versi repository yang diverifikasi melalui SHA GitHub serta menggabungkan catatan engine tanpa mengubah bagian backend atau status integrasi. Tidak ada perubahan kode engine.
- **Langkah berikutnya:** verifikasi kelima berkas WHO asli yang diunduh beserta checksum, implementasikan rumus LMS dan restricted LMS dengan uji resmi, lalu evaluasi pertumbuhan dan referensi kurva. Pertahankan aturan ZIP + pytest tanpa push ke GitHub dan baca ulang versi terbaru `CHANGELOG.md`/`HANDOFF.md` dari repo sebelum setiap patch dokumentasi.

## Backend — tim backend

- **Diperbarui:** 7 November 2026, setelah laporan uji pukul 10:03 WIB.
- **Kontrak acuan:** `docs/CONTRACT.md` v0.4 (draf), `docs/PRD.md` v0.2. Tidak ada perubahan kontrak, port, ataupun endpoint yang diusulkan dalam pembaruan ini.
- **Selesai (implementasi kode):** Go HTTP API pada `:8080/api/v1`; 14 route publik; model input/output dan validasi; PostgreSQL via `github.com/lib/pq`; migrasi otomatis `migrations/001_init.sql` untuk 4 tabel (`children`, `measurements`, `kpsp_results`, `food_recalls`) beserta relasi/indeks; repository dan service; client HTTP Go ke engine Python via `ENGINE_URL`; CORS sesuai `CORS_ORIGIN`; `data/messages.id.json` berbahasa Indonesia; `data/guides.id.json` masih `[]` menunggu materi resmi; migrasi seed identitas fiktif opsional `migrations/002_seed_children.sql`; dokumentasi `backend/README.md` dan berkas tes dasar.
- **Sudah diamati di laptop backend:**
  1. `go run ./cmd/server` semula gagal karena checksum dependensi `github.com/lib/pq` belum tercatat; setelah penanganan dependensi, error ini tidak muncul lagi.
  2. Startup sempat menghentikan proses dengan pesan `DATABASE_URL wajib diisi; lihat ../.env.example`.
  3. Setelah konfigurasi lingkungan, server menerima `GET http://localhost:8080/api/v1/` dan mengembalikan JSON `NOT_FOUND` (HTTP 404) sesuai catch-all router. **Ini membuktikan layanan HTTP Go hidup, bukan bahwa API CRUD sudah diuji.** Pada implementasi `main.go` saat ini, listener baru dijalankan setelah `PingContext` PostgreSQL dan migrasi berhasil; karenanya startup ini juga mengindikasikan koneksi awal database/migrasi lolos, selama kode yang dijalankan adalah versi backend ini.
- **Sedang dikerjakan:** pengujian baca/tulis anak dan pengukuran pada PostgreSQL nyata, serta integrasi Python di jaringan hotspot.
- **Belum diverifikasi:** hasil `GET /api/v1/children`, `POST /api/v1/children`, seluruh route lain pada DB nyata, `go test ./...` di laptop demo, fungsi engine Python, koneksi frontend, serta pengujian end-to-end. Jangan menandai hal-hal ini sebagai lulus sebelum ada bukti.
- **Masalah / batasan diketahui:** `GET /api/v1/` tidak terdaftar dan memang mengembalikan 404, gunakan endpoint spesifik. Struktur ringkasan `GET /children` belum dicontohkan eksplisit dalam kontrak. Format skor KPSP dan respons reference engine perlu dicocokkan dengan implementasi Python Zena. `guides.id.json` kosong sampai isi bersumber resmi disetujui. `POST /measurements` dan `POST /food-recalls` menyimpan ke DB lebih dahulu, lalu memanggil engine; jika engine tidak aktif, API bisa membalas 503 meskipun data sudah tersimpan. Hindari mengirim POST ulang tanpa memeriksa riwayat.
- **Butuh dari orang lain:** Zena menyediakan `ENGINE_URL` yang benar (IP laptop, bind `0.0.0.0:8001`), engine berjalan, format score/reference yang cocok dengan kontrak, dan materi panduan resmi; tim frontend menyepakati contoh JSON respons daftar anak serta menggunakan URL Go pada `VITE_API_URL` (IP laptop backend jika lintas laptop).
- **Cara menjalankan:**

  Dari akar repository, buat `.env` lokal berdasar `.env.example` (jangan commit `.env`). Pastikan DB `tumbuh` dibuat di PostgreSQL port `5432`, lalu jalankan dari folder `backend/`:

  ```powershell
  go mod tidy
  go test ./...
  go run ./cmd/server
  ```

  Variabel yang diperlukan: `DATABASE_URL=postgres://postgres:<PASSWORD>@localhost:5432/tumbuh?sslmode=disable`, `ENGINE_URL=http://<IP_LAPTOP_ZENA>:8001/engine/v1`, dan `CORS_ORIGIN=http://localhost:5173`. Isi nilai sebenarnya hanya di `.env` lokal.

- **Langkah uji selanjutnya (PowerShell kedua):**

  ```powershell
  # Route dasar /api/v1/ bukan health check; 404 di sini memang normal.
  Invoke-RestMethod http://localhost:8080/api/v1/children

  $body = @{name="Anak Demo"; sex="female"; birth_date="2026-01-07"; is_preterm=$false} | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/children -ContentType 'application/json' -Body $body

  # Setelah IP dan engine dikonfirmasi Zena:
  Invoke-RestMethod http://<IP_LAPTOP_ZENA>:8001/engine/v1/health
  ```

  Harapan bila DB kosong: `GET /children` -> `{"data":[],"error":null}`. Catat respons nyata dan ID hasil POST, lalu uji pengukuran, status, growth, KPSP, serta food recall. Jika engine belum aktif, endpoint yang memerlukannya dapat membalas `ENGINE_UNAVAILABLE` (503).
- **Git / serah terima:** pastikan `backend/go.mod` dan `backend/go.sum` ikut ter-commit setelah `go mod tidy`; **jangan commit `.env`, password, atau data anak asli**. Jalankan `git pull --rebase` sebelum push. Usulan commit: `backend: catat status implementasi dan uji awal` (bersama pembaruan `docs/CHANGELOG.md` dan `docs/HANDOFF.md`).

## Backend — tim backend

- **Diperbarui:** 7 November 2026, setelah laporan uji pukul 10:03 WIB.
- **Kontrak acuan:** `docs/CONTRACT.md` v0.4 (draf), `docs/PRD.md` v0.2. Tidak ada perubahan kontrak, port, ataupun endpoint yang diusulkan dalam pembaruan ini.
- **Selesai (implementasi kode):** Go HTTP API pada `:8080/api/v1`; 14 route publik; model input/output dan validasi; PostgreSQL via `github.com/lib/pq`; migrasi otomatis `migrations/001_init.sql` untuk 4 tabel (`children`, `measurements`, `kpsp_results`, `food_recalls`) beserta relasi/indeks; repository dan service; client HTTP Go ke engine Python via `ENGINE_URL`; CORS sesuai `CORS_ORIGIN`; `data/messages.id.json` berbahasa Indonesia; `data/guides.id.json` masih `[]` menunggu materi resmi; migrasi seed identitas fiktif opsional `migrations/002_seed_children.sql`; dokumentasi `backend/README.md` dan berkas tes dasar.
- **Sudah diamati di laptop backend:**
  1. `go run ./cmd/server` semula gagal karena checksum dependensi `github.com/lib/pq` belum tercatat; setelah penanganan dependensi, error ini tidak muncul lagi.
  2. Startup sempat menghentikan proses dengan pesan `DATABASE_URL wajib diisi; lihat ../.env.example`.
  3. Setelah konfigurasi lingkungan, server menerima `GET http://localhost:8080/api/v1/` dan mengembalikan JSON `NOT_FOUND` (HTTP 404) sesuai catch-all router. **Ini membuktikan layanan HTTP Go hidup, bukan bahwa API CRUD sudah diuji.** Pada implementasi `main.go` saat ini, listener baru dijalankan setelah `PingContext` PostgreSQL dan migrasi berhasil; karenanya startup ini juga mengindikasikan koneksi awal database/migrasi lolos, selama kode yang dijalankan adalah versi backend ini.
- **Sedang dikerjakan:** pengujian baca/tulis anak dan pengukuran pada PostgreSQL nyata, serta integrasi Python di jaringan hotspot.
- **Belum diverifikasi:** hasil `GET /api/v1/children`, `POST /api/v1/children`, seluruh route lain pada DB nyata, `go test ./...` di laptop demo, fungsi engine Python, koneksi frontend, serta pengujian end-to-end. Jangan menandai hal-hal ini sebagai lulus sebelum ada bukti.
- **Masalah / batasan diketahui:** `GET /api/v1/` tidak terdaftar dan memang mengembalikan 404, gunakan endpoint spesifik. Struktur ringkasan `GET /children` belum dicontohkan eksplisit dalam kontrak. Format skor KPSP dan respons reference engine perlu dicocokkan dengan implementasi Python Zena. `guides.id.json` kosong sampai isi bersumber resmi disetujui. `POST /measurements` dan `POST /food-recalls` menyimpan ke DB lebih dahulu, lalu memanggil engine; jika engine tidak aktif, API bisa membalas 503 meskipun data sudah tersimpan. Hindari mengirim POST ulang tanpa memeriksa riwayat.
- **Butuh dari orang lain:** Zena menyediakan `ENGINE_URL` yang benar (IP laptop, bind `0.0.0.0:8001`), engine berjalan, format score/reference yang cocok dengan kontrak, dan materi panduan resmi; tim frontend menyepakati contoh JSON respons daftar anak serta menggunakan URL Go pada `VITE_API_URL` (IP laptop backend jika lintas laptop).
- **Cara menjalankan:**

  Dari akar repository, buat `.env` lokal berdasar `.env.example` (jangan commit `.env`). Pastikan DB `tumbuh` dibuat di PostgreSQL port `5432`, lalu jalankan dari folder `backend/`:

  ```powershell
  go mod tidy
  go test ./...
  go run ./cmd/server
  ```

  Variabel yang diperlukan: `DATABASE_URL=postgres://postgres:<PASSWORD>@localhost:5432/tumbuh?sslmode=disable`, `ENGINE_URL=http://<IP_LAPTOP_ZENA>:8001/engine/v1`, dan `CORS_ORIGIN=http://localhost:5173`. Isi nilai sebenarnya hanya di `.env` lokal.

- **Langkah uji selanjutnya (PowerShell kedua):**

  ```powershell
  # Route dasar /api/v1/ bukan health check; 404 di sini memang normal.
  Invoke-RestMethod http://localhost:8080/api/v1/children

  $body = @{name="Anak Demo"; sex="female"; birth_date="2026-01-07"; is_preterm=$false} | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/children -ContentType 'application/json' -Body $body

  # Setelah IP dan engine dikonfirmasi Zena:
  Invoke-RestMethod http://<IP_LAPTOP_ZENA>:8001/engine/v1/health
  ```

  Harapan bila DB kosong: `GET /children` -> `{"data":[],"error":null}`. Catat respons nyata dan ID hasil POST, lalu uji pengukuran, status, growth, KPSP, serta food recall. Jika engine belum aktif, endpoint yang memerlukannya dapat membalas `ENGINE_UNAVAILABLE` (503).
- **Git / serah terima:** pastikan `backend/go.mod` dan `backend/go.sum` ikut ter-commit setelah `go mod tidy`; **jangan commit `.env`, password, atau data anak asli**. Jalankan `git pull --rebase` sebelum push. Usulan commit: `backend: catat status implementasi dan uji awal` (bersama pembaruan `docs/CHANGELOG.md` dan `docs/HANDOFF.md`).

## Desain + frontend — (nama)

- **Diperbarui:** HH:MM
- **Selesai:**
- **Sedang dikerjakan:**
- **Belum dimulai:**
- **Cara menjalankan dan menguji:**
- **Masalah yang diketahui:**
- **Butuh dari orang lain:**
- **Langkah berikutnya:**

---

## Status integrasi

Status pada tabel ini membedakan **route terimplementasi** dan **terbukti teruji end-to-end**. Tanda `?` berarti belum dikonfirmasi oleh pemilik komponen.

| Endpoint | Go siap (kode) | Engine siap | Frontend tersambung | Uji end-to-end |
| --- | --- | --- | --- | --- |
| `GET/POST /children` | Ya | — | ? | Belum |
| `GET /children/{id}/status` | Ya | ? | ? | Belum |
| `POST /children/{id}/measurements` | Ya | ? | ? | Belum |
| `GET /children/{id}/growth` | Ya | ? | ? | Belum |
| `GET /children/{id}/kpsp/next`, `POST /children/{id}/kpsp` | Ya | ? | ? | Belum |
| `GET /guides` | Ya, data masih kosong | — | ? | Belum |
| `GET/POST /children/{id}/food-recalls` | Ya | ? | ? | Belum |

**Temuan terkonfirmasi terakhir:** `GET /api/v1/` menghasilkan `NOT_FOUND` sesuai routing; belum ada bukti respons endpoint publik berbasis data. Tidak ada perubahan pada folder `engine/`, `frontend/`, ataupun `docs/CONTRACT.md` dalam pembaruan ini.
