# Backend Go + PostgreSQL — HIMTEC 2026

Acuan: repository `af4193a` (`Document Update`, 7 November 2026), `docs/CONTRACT.md` v0.5 (draf sinkronisasi) dan PRD terbaru dengan kepemilikan anak. API publik tetap `:8080/api/v1`; PostgreSQL tetap `:5432`. Aplikasi adalah alat skrining, bukan diagnosis.

## Daftar/login OTP dummy lokal

Fitur baru dipilih dengan `$env:AUTH_MODE="otp_dummy"` sebelum menjalankan Go. Baca **[AUTH_TESTING.md](AUTH_TESTING.md)** untuk pendaftaran email, OTP dari terminal, bearer token, logout dan pengujian akun berbeda. Mode ini hanya bind ke 127.0.0.1:8080; route data membutuhkan login. Default/demo tetap alur lama tanpa autentikasi. Akun baru tidak otomatis memiliki anak demo lama.

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

Startup menjalankan `001_init.sql` kemudian `003_demo_parent.sql` dan `004_otp_auth.sql` dalam satu transaksi, dengan advisory lock agar startup bersamaan tidak menerapkan migrasi secara bersamaan. `002_seed_children.sql` adalah seed opsional dan tidak dijalankan otomatis.

Lima tabel bisnis `users`, `children`, `measurements`, `kpsp_results`, `food_recalls`.

- Satu pengguna demo dibuat dengan ID tetap `00000000-0000-4000-8000-000000000001`, nama `Orang Tua Demo`, role `parent`, aktif.
- `children.parent_id` ditambahkan dan diberi FK ke `users.id`. Anak lama yang belum memiliki pemilik dihubungkan ke orang tua demo. Pemilik yang sudah ada dipertahankan. Riwayat pengukuran, KPSP dan catatan makan tidak dihapus.
- Semua query anak dan baca/tulis/hapus data turunannya memeriksa pemilik serta role `parent` dan status aktif akun. Akun admin/nonaktif tidak mendapat akses melalui repository ini.
- Pemilik dipilih oleh server. Field `parent_id` tidak ditambahkan ke JSON publik dan tidak dapat dipilih melalui body request.
- Jika database dibuat dari DDL PRD dengan `food_groups text[]`, migrasi mengubah penyimpanannya ke JSONB menggunakan `to_jsonb`, mempertahankan isi dan urutan kelompok pangan. JSON publik tetap berupa array string. PRD mengizinkan penyesuaian tipe penyimpanan.
- Akun demo yang sudah dinonaktifkan atau memiliki role berbeda tidak diaktifkan ulang oleh migrasi; startup gagal agar kondisi tersebut ditinjau secara eksplisit.

Mode demo lama memakai satu orang tua demo tanpa login. Mode otp_dummy menambahkan pendaftaran/login parent dan tiga tabel auth (total delapan tabel). Pengelolaan akun admin dan pengiriman OTP nyata tetap pekerjaan lanjutan.

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


## Diagnostik integrasi engine

Dari folder backend, jalankan `go run ./cmd/check-engine`. Perintah memakai ENGINE_URL dari environment/.env yang sama dengan server, tanpa DATABASE_URL dan tanpa mengirim data anak.

- Health tidak terhubung/invalid: periksa IP, port, proses Python dan bind.
- Health OK + missing_routes: proses hidup tetapi OpenAPI belum mendaftarkan metode/path yang dipanggil Go.
- Fake terdeteksi lewat header X-Fake-Engine: yang diuji hanya fixture; bukan hasil medis.
- OpenAPI unknown: pemeriksaan route tidak dapat disimpulkan (misalnya docs dinonaktifkan atau reverse proxy). Ini bukan bukti semua route hilang.
- Route terdaftar dan WHO true pun belum membuktikan perhitungan medis tervalidasi.

Exit code program: 0 berarti diagnostik dasar lolos atau fake terdeteksi; 1 berarti health gagal/route diketahui hilang/data WHO real false; 2 konfigurasi ENGINE_URL kosong; 3 health OK tetapi daftar route tidak diketahui. `go run` dapat mencetak exit status saat diagnostik menemukan masalah; ini hasil pemeriksaan yang perlu dibaca, bukan bukti Go gagal dikompilasi.

Server menjalankan pemeriksaan read-only terbatas 3 detik saat startup, lalu tetap melayani CRUD/login. Tidak melakukan cache permanen atau memblokir request berdasarkan OpenAPI; hasil diagnostik bisa berubah setelah Python diperbarui. Semua evaluasi tetap memanggil engine pada saat request.

Jika Python membalas 404, pesan Go menjelaskan endpoint perhitungan belum tersedia. Gangguan koneksi/respons tidak selesai menjelaskan pemeriksaan ENGINE_URL/proses Python. Kode publik tetap ENGINE_UNAVAILABLE (503), dan pesan data sudah tersimpan tetap dipertahankan setelah POST.

Draf kontrak v0.5 menambahkan mode OTP dan menjelaskan >=16 hari KPSP sesuai Patch 07B. Go tidak menghitung umur formulir/ambang KPSP sendiri. Engine asli tidak dimodifikasi dalam patch backend ini; router medis, gambar/review bank KPSP dan pengujian klinis tetap pekerjaan engine.
