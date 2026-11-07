# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Diperbarui:** 2026-11-07 10:47 WIB (patch ZIP 04).
- **Selesai:** Patch 01 dependensi; patch 02 FastAPI, validasi Pydantic dan `/engine/v1/health`; patch 03 loader lima tabel WHO resmi (pinned commit + Git blob checksum), skrip unduh dan 48 tes; patch 04 `app/core/growth_math.py`: rumus LMS termasuk L=0, restricted LMS (WFA/WFL/WFH), invers LMS untuk SD, koreksi posisi ukur dengan ambang 731 hari, serta interpolasi linear LMS WFL/WFH sebagai fungsi terpisah. Total **91 tes pytest lulus** (termasuk 43 tes baru), dengan kasus pembanding dari tes WHO Anthro. Tidak ada perubahan endpoint atau kontrak.
- **Sedang dikerjakan:** persiapan integrasi perhitungan dengan loader data WHO asli. Tabel resmi belum ada di sandbox; unduh di laptop tim saat setup melalui `python scripts/fetch_who_tables.py` sebelum uji integrasi klinis.
- **Belum dimulai:** klasifikasi Permenkes 2/2020; kode alasan early warning; endpoint `/growth/evaluate`, `/reference`, `/kpsp/questionnaire`, `/kpsp/score`; logika IYCF; uji lintas layanan dan 5 kasus penuh terhadap aplikasi WHO Anthro.
- **Cara menjalankan dan menguji:** `cd engine && python -m pip install -r requirements.txt && python -m pytest -q` (91 passed). Saat persiapan dengan internet: `python scripts/fetch_who_tables.py`. Jalankan server `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001`. Health `who_tables_loaded=true` hanya berarti data ada dan terverifikasi, **bukan endpoint evaluasi selesai**.
- **Masalah yang diketahui:** WHO Anthro LMS harian 0–1826 hari tetapi kontrak masih menerima sampai 1856; jangan ekstrapolasi. Tabel berat-panjang/tinggi beresolusi 0,1 cm; utilitas interpolasi tersedia berdasar WHO Anthro, tetapi kebijakan pemakaian input presisi lebih tinggi belum dikunci. WHO Anthro memberi flag khusus untuk pengukuran berdiri pada anak di bawah 9 bulan; kontrak v0.4 hanya mengatur koreksi 0,7 cm untuk umur <731 hari. Skema body `/kpsp/score` belum eksplisit; kontrak v0.4 masih draf. Periksa persyaratan lisensi WHO sebelum distribusi data. Bagian Backend muncul **dua kali** pada `HANDOFF.md` GitHub yang dicek pukul 10:47; duplikasi itu bukan perubahan Patch 04 dan sengaja tidak disentuh agar catatan anggota lain terjaga.
- **Butuh dari orang lain:** keputusan pemilik kontrak tentang batas umur, kebijakan presisi 0,1 cm, flag posisi di bawah 9 bulan, dan skema `/kpsp/score`; backend mengikuti kontrak v0.4 dan tetap mengirim `food_recalls` sebagai array (boleh kosong).
- **Langkah berikutnya:** perhitungan per pengukuran dengan lima tabel WHO asli; klasifikasi/flag mengacu sumber resmi, lalu endpoint `/growth/evaluate` dan pengujian kesetaraan hasil WHO Anthro. Semua pekerjaan diuji dengan pytest dan dikirim sebagai ZIP, tanpa push GitHub.

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
