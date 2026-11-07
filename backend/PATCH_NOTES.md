# Patch backend dan dokumentasi — 7 November 2026

Basis: `af4193a6da0a9019a25f25738b0e9caf9243ffac` (`Document Update`). Paket ini mencakup seluruh perbaikan backend dari ZIP sebelumnya serta penyesuaian PRD terbaru. Ekstrak ke akar repository; hasilnya `backend/` dan dua berkas pada `docs/`.

## Perubahan database dan kepemilikan

- Migrasi tambahan `003_demo_parent.sql`: tabel `users`, satu orang tua demo, `children.parent_id` NOT NULL, foreign key dan indeks.
- Upgrade data lama mempertahankan ID/riwayat dan pemilik yang sudah ditetapkan. Hanya anak tanpa pemilik yang dihubungkan ke orang tua demo.
- `food_groups text[]` dari DDL PRD dikonversi ke JSONB tanpa kehilangan nilai; JSON publik tetap sama.
- `001` dan `003` dijalankan dalam transaksi dengan advisory lock. Kegagalan satu bagian membatalkan transaksi. Seed `002` tetap opsional dan kini menyertakan pemilik.
- Seluruh query repository membatasi pemilik anak dan memeriksa akun aktif berperan parent, termasuk query data pengukuran, KPSP, catatan makan dan hapus pengukuran.
- Konteks demo dipilih server; tidak menambah field atau endpoint publik. OTP dummy parent kini tersedia sebagai opsi lokal; pengelolaan admin belum diimplementasikan.

## Validasi dan perbaikan lain

- Umur catatan makan selaras dengan engine: hari / 30,4375 pada tanggal recall, rentang [6,24), tanpa pembulatan.
- KPSP menolak tanggal sebelum lahir dan setelah hari ini.
- Error engine/DB dipisahkan. Route Python yang belum tersedia menjadi 503 ENGINE_UNAVAILABLE; validasi engine 422 mempertahankan fields; kegagalan database menjadi 500 INTERNAL; data lokal/anak milik akun lain tetap 404.
- Pesan setelah POST menjelaskan data sudah tersimpan jika evaluasi gagal; ID disimpan di log agar dapat ditelusuri. Data tidak di-POST ulang tanpa memeriksa riwayat.
- Client menolak respons rusak/kosong/null, field error hilang, atau ukuran lebih dari 4 MiB; timeout tetap 3 detik.
- Titik grafik kosong disaring; skor KPSP hilang tidak dianggap nol; jadwal dan jumlah butir kuesioner diperiksa.
- Port 8080 diperiksa sebelum akses database. Pesan siap baru muncul setelah bind, migrasi dan pemuatan data selesai; konflik port dilaporkan secara jelas.

## Menerapkan dan menjalankan

Hentikan server Go lama dengan Ctrl+C, simpan perubahan lokal yang belum digabungkan, dan backup database lama bila perlu dipertahankan. Gabungkan berkas dari ZIP ke akar repository. Pertahankan `.env` lokal dan gunakan isi `backend/README.md` untuk konfigurasi.

```powershell
cd backend
go mod download
go test ./...
go run ./cmd/server
```

Migrasi otomatis menambahkan akun orang tua demo dan meng-upgrade tabel lama. Database `tumbuh` harus sudah dibuat. Jangan menjalankan seed `002` sebelum migrasi startup selesai. Jika port 8080 sedang dipakai, hentikan proses backend lama sebelum menjalankan ulang.

## Validasi yang telah dilakukan

- `go test -race -count=1 ./...` dengan Go 1.22.12: lulus, termasuk lima tes SQL integrasi.
- Tes SQL memakai `lib/pq` ke PGlite 0.3.2/PostgreSQL WASM melalui pglite-socket 0.0.7: database baru, migrasi legacy, idempotensi, seed, isolasi parent, akun admin/nonaktif, preservasi array PRD dan rollback lulus.
- `go vet ./...`: lulus.
- Kompilasi Linux dan Windows amd64 (`go build -buildvcs=false`): lulus. Binary tidak dimasukkan ke ZIP.
- Smoke HTTP Go yang berjalan dengan database SQL tersebut dan engine HTTP tiruan: lulus untuk startup/CRUD dasar, penyimpanan saat evaluasi gagal, baca riwayat, duplikasi dan KPSP sebelum lahir.
- Pemeriksaan konflik port: lulus; proses gagal dengan pesan yang jelas sebelum akses database.

PGlite, harness pengujian dan binary hanya dipakai saat validasi dan tidak disertakan dalam paket. Tes repository untuk PostgreSQL native disertakan dan dapat diaktifkan dengan BACKEND_TEST_DATABASE_URL pada database uji terpisah. PostgreSQL native/Windows demo dan engine Python nyata masih perlu diverifikasi.

## Batas dan pekerjaan lanjutan

Pada commit acuan, endpoint Python evaluasi/reference/KPSP belum tersedia; fitur yang membutuhkannya masih dapat membalas 503. Patch tidak menghasilkan z-score/status medis tiruan. Panduan masih kosong menunggu isi resmi. Tidak ada perubahan kontrak API, enum, port, variabel runtime wajib atau batas umur pengukuran. Riwayat medis lama tidak dibersihkan otomatis.

`docs/CHANGELOG.md` dan `docs/HANDOFF.md` menggabungkan catatan backend dengan dokumen tim pada commit acuan; bagian engine/frontend dipertahankan. Jika dokumen GitHub berubah lagi, gabungkan perubahan backend dengan versi terbaru sebelum menimpa. Tidak ada push GitHub pada pekerjaan ini.

## Tambahan OTP dummy lokal

Pendaftaran email dan login diaktifkan dengan AUTH_MODE=otp_dummy, kode hanya di terminal. Migrasi 004 menambah otp_codes/auth_sessions/audit_logs. Semua data bisnis membutuhkan bearer session dalam mode ini dan Store/Service di-scope per request ke user parent aktif. Kode HMAC sekali pakai 5 menit/5 percobaan, request minimum 60 detik/maksimal 5 per jam/email, session token acak disimpan hashed dan berlaku 24 jam, logout mencabut sesi. Default demo lama tetap tersedia. Lihat AUTH_TESTING.md untuk ekstensi API, 401/429, hasil tes dan perintah PowerShell.
