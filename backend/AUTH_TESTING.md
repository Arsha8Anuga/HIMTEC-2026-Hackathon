# Daftar dan login OTP dummy — panduan PowerShell

Fitur lokal yang diminta pengguna, di atas basis repository `1a0fe1bacb4d174e0b900931ca7feacaf4c24862`. OTP hanya ditampilkan di terminal Go; tidak ada email/SMS yang benar-benar dikirim. Tidak perlu layanan email atau dependensi Go baru.

## 1. Pasang dan jalankan Go

Hentikan Go lama dengan Ctrl+C. Backup database lokal yang perlu dipertahankan, lalu gabungkan ZIP ke akar repository. Pertahankan `.env` lokal. Dari folder `backend`:

```powershell
$env:AUTH_MODE="otp_dummy"
$env:ENGINE_URL="http://127.0.0.1:18001/engine/v1"
go mod download
go test ./...
go run ./cmd/server
```

DATABASE_URL tetap dibaca dari .env lokal. Engine/fake engine tidak dibutuhkan untuk daftar/login/CRUD anak; diperlukan saat pengujian status, pengukuran + evaluasi, kurva, KPSP dan catatan makan + evaluasi. Fake engine dapat tetap berjalan di terminal terpisah sesuai pengujian sebelumnya.

Log harus menyebut `AUTH_MODE=otp_dummy: login wajib`. Mode ini bind hanya ke 127.0.0.1:8080. Tanpa AUTH_MODE atau dengan AUTH_MODE=demo, backend tetap memakai mode demo lama tanpa login; endpoint auth tidak diaktifkan. Mode dummy bukan mode untuk deployment publik.

Migrasi startup menjalankan 001 + 003 + 004 secara transaksional. Migrasi 004 menambah `otp_codes`, `auth_sessions`, `audit_logs`, serta indeks email tanpa membedakan huruf besar/kecil. Total delapan tabel. Baris lama tidak dihapus atau dipindahkan. Bila database lama memiliki dua email yang hanya berbeda kapitalisasi, indeks akan gagal; tinjau akun tersebut secara manual, jangan menghapus data otomatis.

## 2. Minta OTP pendaftaran

Buka PowerShell kedua. Jalankan sekali dengan email uji baru:

```powershell
$base = "http://127.0.0.1:8080/api/v1"
$email = "mutia.uji@example.test"
$body = @{name="Mutia Uji"; email=$email} | ConvertTo-Json

$challenge = Invoke-RestMethod -Method POST `
    -Uri "$base/auth/register" `
    -ContentType "application/json" -Body $body

$challenge | ConvertTo-Json -Depth 5
```

Respons 202 berisi challenge_id dan expires_in=300, tanpa kode OTP. Akun belum dibuat sampai kode diverifikasi.

Di terminal Go, cari baris dengan challenge_id yang sama:

```text
[OTP DUMMY - LOKAL] email=... challenge_id=... kode=...... (berlaku 5 menit)
```

Email yang sudah terdaftar harus menggunakan /auth/login. Respons permintaan kode sengaja sama untuk akun yang tidak memenuhi syarat; kode hanya dicetak untuk pendaftaran baru atau akun parent aktif yang sudah terdaftar. Akun admin/nonaktif tidak mendapat kode login.

## 3. Masukkan kode dan aktifkan sesi

Di PowerShell kedua:

```powershell
$code = Read-Host "Masukkan 6 digit OTP dari terminal Go"
$body = @{challenge_id=$challenge.data.challenge_id; code=$code} | ConvertTo-Json

$session = Invoke-RestMethod -Method POST `
    -Uri "$base/auth/verify" `
    -ContentType "application/json" -Body $body

$headers = @{Authorization="Bearer $($session.data.access_token)"}
$session.data.user | ConvertTo-Json

Invoke-RestMethod "$base/auth/me" -Headers $headers |
    ConvertTo-Json -Depth 5
```

Kode wajib berupa string enam digit, termasuk nol di depan. Kode berlaku 5 menit, hanya sekali pakai, dan dikunci setelah 5 jawaban salah. Permintaan kode baru minimal berselang 60 detik, maksimum 5 per email per jam. Kode baru membatalkan kode lama untuk email tersebut.

OTP tersimpan sebagai HMAC, bukan teks asli. Kunci OTP acak berada di memori proses; restart Go membatalkan kode yang belum diverifikasi. Minta kode baru setelah jendela pembatasan. Sesi yang sudah dibuat tetap berlaku sampai 24 jam atau logout, kecuali akun dinonaktifkan/role berubah.

## 4. Cek dan tambah anak dengan sesi login

```powershell
Invoke-RestMethod "$base/children" -Headers $headers |
    ConvertTo-Json -Depth 10

$body = @{
    name="Anak Akun OTP"
    sex="female"
    birth_date="2026-01-07"
} | ConvertTo-Json

$anak = Invoke-RestMethod -Method POST `
    -Uri "$base/children" -Headers $headers `
    -ContentType "application/json" -Body $body

$id = $anak.data.id
Invoke-RestMethod "$base/children/$id" -Headers $headers |
    ConvertTo-Json -Depth 10
```

Akun baru awalnya memiliki daftar anak kosong. Anak/data demo sebelumnya tetap milik akun demo; tidak otomatis diberikan kepada pengguna baru. Untuk status/riwayat/KPSP/catatan makan, tambahkan `-Headers $headers` pada perintah pengujian sebelumnya dan gunakan UUID anak milik akun ini.

Membuka /children lewat browser tanpa Authorization akan mendapat 401 pada mode OTP. Gunakan PowerShell dengan headers tersebut atau frontend yang memasang bearer token. Jangan menempelkan access_token ke screenshot/chat.

## 5. Logout

```powershell
Invoke-RestMethod -Method POST "$base/auth/logout" -Headers $headers |
    ConvertTo-Json
```

Sesi tersebut langsung tidak dapat dipakai lagi. Permintaan selanjutnya dengan token lama menghasilkan 401. Sesi pengguna lain tetap berlaku.

## 6. Login lagi ke akun yang sudah ada

Jika belum 60 detik sejak permintaan OTP terakhir untuk email ini, tunggu dahulu.

```powershell
$body = @{email=$email} | ConvertTo-Json
$challenge = Invoke-RestMethod -Method POST `
    -Uri "$base/auth/login" `
    -ContentType "application/json" -Body $body

$code = Read-Host "Masukkan OTP login dari terminal Go"
$body = @{challenge_id=$challenge.data.challenge_id; code=$code} | ConvertTo-Json
$session = Invoke-RestMethod -Method POST `
    -Uri "$base/auth/verify" `
    -ContentType "application/json" -Body $body
$headers = @{Authorization="Bearer $($session.data.access_token)"}
Invoke-RestMethod "$base/children" -Headers $headers | ConvertTo-Json -Depth 10
```

## Kontrak API tambahan auth-dummy v0.1

Ekstensi ini dibuat atas pilihan pengguna; kontrak medis v0.4 tidak diubah. Integrasikan spesifikasi ini ke kontrak tim bersama pemilik kontrak sebelum menggunakannya sebagai rilis bersama.

| Metode/path di bawah /api/v1 | Request | Respons sukses |
| --- | --- | --- |
| POST /auth/register | name, email | 202: challenge_id, expires_in |
| POST /auth/login | email | 202: challenge_id, expires_in |
| POST /auth/verify | challenge_id, code (string) | 200: access_token, token_type=Bearer, expires_in=86400, user |
| GET /auth/me | Authorization: Bearer ... | 200: user (id, name, email, role) |
| POST /auth/logout | Authorization: Bearer ... | 200: logged_out=true |

Amplop tetap data/error. Error tambahan: 401 UNAUTHORIZED (kode/sesi tidak valid, expired, dipakai, atau akun tidak aktif), 429 RATE_LIMITED. Input nama/email/body yang salah menggunakan 422 VALIDATION_ERROR. Kegagalan DB tetap 500 INTERNAL. Seluruh route bisnis /api/v1/ di luar auth dan redirect root memerlukan sesi parent aktif saat mode OTP aktif. Anak di luar scope menghasilkan 404. Tidak ada endpoint untuk memilih parent_id atau role melalui body.

CORS mengizinkan Authorization untuk origin yang dikonfigurasi. Token disimpan sebagai SHA-256 di auth_sessions; nilai asli hanya diberikan saat verifikasi. Logout mencabut sesi di database. Audit mencatat permintaan OTP, penolakan kode, login dan logout tanpa kode/token.

## Validasi paket

- Suite Go/race lulus, termasuk SQL auth: register/verify/login/me/logout, session expiry, OTP expiry, batas percobaan/request, replay, restart, penolakan role injection, akun nonaktif, akses lintas parent dan verifikasi bersamaan.
- SQL integrasi memakai lib/pq ke PGlite/PostgreSQL WASM; bukan runtime PostgreSQL native Windows.
- Uji server Go nyata dengan DB pengujian tersebut lulus: startup migrasi, OTP terminal, register/verify/me, tambah anak milik sesi, logout dan penolakan token lama.
- go vet serta kompilasi Linux dan Windows amd64 lulus; runtime Windows/laptop pengguna tetap perlu diperiksa.

Tes unit biasa: go test ./... (SQL suite dilewati tanpa BACKEND_TEST_DATABASE_URL). Untuk SQL suite gunakan database uji terpisah dan `go test -p 1 -race ./...` dengan BACKEND_TEST_DATABASE_URL. Tes membuat dan menghapus schema unik miliknya. Fake engine hanya fixture protokol; hasil medis belum divalidasi oleh pengujian auth.

## Kembali ke mode demo lama

Hentikan Go, jalankan `Remove-Item Env:AUTH_MODE`, lalu go run ./cmd/server. Mode demo tanpa login kembali memakai parent demo lama; akun dan sesi yang dibuat tetap tersimpan. Jangan menggunakan mode demo sebagai mode multi-pengguna.
