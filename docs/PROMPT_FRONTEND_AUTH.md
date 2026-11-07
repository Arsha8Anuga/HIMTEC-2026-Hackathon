# Perintah untuk AI lain: layar login frontend (AUTH_MODE=otp_email)

Tempel seluruh blok di bawah ke sesi AI baru, bersama `AGENTS.md`, `frontend/src/App.vue`,
`frontend/src/lib/api.ts`, `frontend/src/components/AssistantChat.vue`, dan `backend/AUTH_TESTING.md`.

```text
Repo: HIMTEC-2026-Hackathon, folder frontend/ (Vue 3 + Vite + TS, tanpa pustaka UI tambahan, tanpa CDN).
Baca AGENTS.md lebih dulu dan patuhi aturannya. Jangan mengubah backend/ atau engine/.

Tujuan: frontend bisa dipakai dengan backend AUTH_MODE=otp_email (dan otp_dummy) tanpa merusak mode demo.

Backend yang sudah ada (prefix /api/v1, amplop {data, error}):
- POST /auth/register {name, email} -> 202 {challenge_id, expires_in:300}
- POST /auth/login {email} -> 202 {challenge_id, expires_in:300}
- POST /auth/verify {challenge_id, code} (code string 6 angka) -> 200 {access_token, token_type:"Bearer", expires_in:86400, user:{id,name,email,role}}
- GET /auth/me (Authorization: Bearer) -> 200 user
- POST /auth/logout (Bearer) -> 200 {logged_out:true}
- Error: 401 UNAUTHORIZED, 429 RATE_LIMITED (minta kode paling cepat 60 detik sekali, 5 per jam per email),
  422 VALIDATION_ERROR dengan fields. Semua route bisnis butuh Bearer saat mode OTP.
- Mode demo (tanpa AUTH_MODE): /auth/* tidak ada (404) dan semua route terbuka.

Kerjakan:
1. lib/api.ts: tambahkan header Authorization: Bearer <token> bila token ada. Token disimpan di
   sessionStorage (bungkus try/catch; tanpa storage tetap jalan di memori). Pada 401 dari route selain
   /auth/*, hapus token dan arahkan ke halaman masuk.
2. Deteksi mode saat aplikasi dibuka: GET /auth/me. 200 = sudah masuk; 401 = tampilkan halaman masuk;
   404 = mode demo, jangan tampilkan login sama sekali (perilaku sekarang tidak boleh berubah).
3. Halaman "Masuk" dan "Daftar" (satu alur): isian email (dan nama untuk daftar) -> tombol "Kirim kode"
   -> isian kode 6 angka (inputmode numeric, autocomplete one-time-code) -> "Masuk". Tampilkan hitung
   mundur 60 detik sebelum "Kirim ulang kode". Pesan 429 dan 401 dalam bahasa awam. Jangan pernah
   menampilkan, mencatat (console), atau menyimpan kode OTP selain di isian.
4. Header: nama pengguna dan tombol "Keluar" (POST /auth/logout, lalu hapus token, ke halaman masuk).
5. AssistantChat.vue dan semua request lain otomatis ikut membawa token lewat lib/api.ts.
6. Aksesibilitas sama dengan layar lain: label terhubung, error di bawah isian (FieldError), target
   sentuh 44 px, teks isian 16 px, fokus pindah ke judul setelah tiap langkah.
7. Tes Playwright baru di tests/auth.spec.ts dengan API tiruan (page.route), seperti tes yang sudah ada:
   (a) mode demo 404 -> tidak ada layar login, beranda tampil; (b) daftar -> kode -> masuk -> request
   berikutnya membawa Bearer; (c) 401 di tengah sesi -> kembali ke halaman masuk; (d) 429 menampilkan
   pesan; (e) keluar menghapus token. Semua 28 tes lama harus tetap lulus.
8. Jalankan: npm run build dan npm test (CHROME_PATH ke Chrome lokal). Catat di docs/CHANGELOG.md
   (area frontend) dan bagian frontend di docs/HANDOFF.md.

Jangan menambah dependensi. Jangan menebak field yang tidak tercantum di atas.
```
