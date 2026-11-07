# Backend Go + PostgreSQL — HIMTEC 2026

Acuan: repository `af4193a` (`Document Update`, 7 November 2026), `docs/CONTRACT.md` v0.4 dan PRD terbaru dengan kepemilikan anak. API publik tetap `:8080/api/v1`; PostgreSQL tetap `:5432`. Aplikasi adalah alat skrining, bukan diagnosis.

## Isi paket dan pemasangan

ZIP berisi folder `backend/` lengkap serta `docs/CHANGELOG.md` dan `docs/HANDOFF.md`. Ekstrak ke akar repository sehingga ada `backend/go.mod` dan `docs/HANDOFF.md`. Gabungkan pembaruan anggota lain yang dibuat setelah commit acuan sebelum menimpa berkas yang sama.

Hentikan backend lama dengan Ctrl+C. Bila database lama berisi data yang perlu dipertahankan, buat backup melalui pgAdmin sebelum menjalankan migrasi versi ini. File `.env` lokal tetap dipakai; ZIP tidak memuat password, data database, engine, frontend, atau binary.

## Menjalankan di Windows

Persyaratan: Go 1.22+, PostgreSQL 13+, database `tumbuh` sudah dibuat. Saat persiapan pertama diperlukan internet untuk mengunduh dependensi Go. Sesudah dependensi tersedia, demo dapat berjalan offline.

Buat `.env` di akar repository berdasarkan `.env.example`. Contoh nilai yang harus diganti sesuai laptop:

```dotenv
DATABASE_URL=postgres://postgres:ISI_PASSWORD@localhost:5432/tumbuh?sslmode=disable
ENGINE_URL=http://IP_LAPTOP_ENGINE:8001/engine/v1
CORS_ORIGIN=http://localhost:5173
```

Dari PowerShell di akar repository:

```powershell
cd backend
go mod download
go test ./...
go run ./cmd/server
```

Backend memeriksa ketersediaan port 8080 sebelum mengakses database. Bila port sudah dipakai, pesan menjelaskan konflik dan proses berhenti. Pesan "Backend Go siap" baru dicetak setelah port terikat, koneksi/migrasi database, dan pemuatan data statis berhasil. Gunakan PowerShell kedua untuk mencoba API.

## Database dan orang tua demo

Startup menjalankan `001_init.sql` kemudian `003_demo_parent.sql` dalam satu transaksi, dengan advisory lock agar startup bersamaan tidak menerapkan migrasi secara bersamaan. `002_seed_children.sql` adalah seed opsional dan tidak dijalankan otomatis.

Hasil akhir: lima tabel `users`, `children`, `measurements`, `kpsp_results`, `food_recalls`.

- Satu pengguna demo dibuat dengan ID tetap `00000000-0000-4000-8000-000000000001`, nama `Orang Tua Demo`, role `parent`, aktif.
- `children.parent_id` ditambahkan dan diberi FK ke `users.id`. Anak lama yang belum memiliki pemilik dihubungkan ke orang tua demo. Pemilik yang sudah ada dipertahankan. Riwayat pengukuran, KPSP dan catatan makan tidak dihapus.
- Semua query anak dan baca/tulis/hapus data turunannya memeriksa pemilik serta role `parent` dan status aktif akun. Akun admin/nonaktif tidak mendapat akses melalui repository ini.
- Pemilik dipilih oleh server. Field `parent_id` tidak ditambahkan ke JSON publik dan tidak dapat dipilih melalui body request.
- Jika database dibuat dari DDL PRD dengan `food_groups text[]`, migrasi mengubah penyimpanannya ke JSONB menggunakan `to_jsonb`, mempertahankan isi dan urutan kelompok pangan. JSON publik tetap berupa array string. PRD mengizinkan penyesuaian tipe penyimpanan.
- Akun demo yang sudah dinonaktifkan atau memiliki role berbeda tidak diaktifkan ulang oleh migrasi; startup gagal agar kondisi tersebut ditinjau secara eksplisit.

MVP tetap tanpa login dan memakai satu konteks orang tua demo. Login OTP dan pengelolaan akun admin merupakan pekerjaan setelah MVP; isolasi query ini adalah persiapannya.

Seed identitas fiktif Anisa/Bima/Citra, setelah startup migrasi selesai:

```powershell
psql -U postgres -d tumbuh -f migrations/002_seed_children.sql
```

Seed membatasi pengecekan nama berdasarkan pemilik dan dapat dijalankan berulang. Tidak ada angka pengukuran medis yang dibuat untuk seed.

## API publik

Semua path di bawah diawali `/api/v1`.

| Metode | Path | Fungsi |
| --- | --- | --- |
| GET / POST | `/children` | Daftar dan tambah anak milik orang tua demo |
| GET | `/children/{id}` | Detail anak |
| GET | `/children/{id}/status` | Status evaluasi dan teks Indonesia |
| GET / POST | `/children/{id}/measurements` | Riwayat dan input pengukuran |
| DELETE | `/children/{id}/measurements/{mid}` | Hapus pengukuran |
| GET | `/children/{id}/growth?indicator=lhfa` | Titik dan acuan WHO |
| GET | `/children/{id}/kpsp/next` | Jadwal dan kuesioner |
| GET / POST | `/children/{id}/kpsp` | Riwayat dan jawaban KPSP |
| GET | `/guides?category=mpasi&age_months=9` | Kartu panduan |
| GET / POST | `/children/{id}/food-recalls` | Catatan makan dan riwayat 14 hari |

Amplop sukses: `{ "data": ..., "error": null }`. Amplop gagal: `{ "data": null, "error": { "code": ..., "message": ... } }`.

## Kesesuaian dengan engine dan penanganan error

Pada commit acuan, Python baru mendaftarkan `/engine/v1/health`. Matematika pertumbuhan dan hotfix validasi sudah ada, tetapi `/growth/evaluate`, `/reference`, `/kpsp/questionnaire`, dan `/kpsp/score` belum tersedia sebagai endpoint HTTP. Health 200 atau `who_tables_loaded=true` belum membuktikan evaluasi siap.

- Route engine belum tersedia, koneksi gagal, timeout, dan respons engine rusak menjadi 503 `ENGINE_UNAVAILABLE`.
- HTTP 422 dengan amplop `VALIDATION_ERROR` dari engine diteruskan bersama `fields`. Error database saat evaluasi menjadi 500 `INTERNAL`. Anak/pengukuran lokal yang tidak ada atau milik orang lain menjadi 404 `NOT_FOUND`.
- POST pengukuran/catatan makan menyimpan data sebelum evaluasi. Jika evaluasi gagal, pesan menyebut **sudah tersimpan** dan log mencatat ID. Periksa GET riwayat sebelum POST ulang; tanggal yang sama tidak boleh diduplikasi.
- Umur catatan makan dihitung pada `recall_date` menggunakan hari / 30,4375 tanpa pembulatan, dengan rentang 6 sampai kurang dari 24 bulan, selaras dengan hotfix engine. Tanggal KPSP tidak boleh sebelum kelahiran atau setelah hari ini.
- Titik grafik dengan koordinat opsional kosong disaring. Respons KPSP harus memiliki skor eksplisit dan kuesioner 10 butir.

`GET /api/v1/` memang bukan endpoint terdaftar. Gunakan `GET /api/v1/children` untuk pemeriksaan API:

```powershell
Invoke-RestMethod http://localhost:8080/api/v1/children
```

## Tes dan bukti validasi

`go test ./...` menjalankan unit/HTTP test server/SQL mock. Tes SQL integrasi dilewati secara normal bila `BACKEND_TEST_DATABASE_URL` tidak diisi.

Untuk menjalankan tes SQL pada database pengujian terpisah yang sudah dibuat:

```powershell
$env:BACKEND_TEST_DATABASE_URL="postgres://postgres:ISI_PASSWORD@localhost:5432/tumbuh_test?sslmode=disable"
go test -count=1 ./internal/repository
Remove-Item Env:BACKEND_TEST_DATABASE_URL
```

Tes membuat schema unik `backend_test_*` dan menghapus schema miliknya setelah selesai. Akun database tes perlu izin membuat schema. Jangan arahkan tes ke database demo/produksi.

Validasi paket ini: suite `go test -race` lulus, termasuk lima tes SQL integrasi melalui `lib/pq` ke PGlite 0.3.2/PostgreSQL WASM dengan socket 0.0.7; `go vet` lulus; kompilasi Linux dan Windows amd64 lulus dengan `-buildvcs=false`. Smoke HTTP mencakup migrasi startup, tambah/baca anak, POST yang tersimpan saat engine membalas 404, pembacaan riwayat, penolakan duplikasi, tanggal KPSP, dan konflik port.

PGlite dipakai hanya di lingkungan pengujian dan tidak menjadi dependensi paket backend. Pengujian ini belum membuktikan runtime PostgreSQL native/Windows di laptop tim atau ketepatan medis engine Python nyata. Jalankan kembali tes integrasi pada PostgreSQL laptop demo.

## Pekerjaan integrasi yang masih terbuka

`guides.id.json` masih kosong menunggu materi resmi. Bentuk ringkasan daftar anak, body lengkap skor KPSP dan respons reference perlu dikunci bersama pemilik kontrak. Batas umur pengukuran 1856 hari tetap mengikuti kontrak; perbedaan dengan domain tabel WHO 1826 hari perlu diputuskan pemilik kontrak/engine. Riwayat KPSP lama yang sudah berisi tanggal tidak valid tidak dihapus diam-diam oleh patch.
