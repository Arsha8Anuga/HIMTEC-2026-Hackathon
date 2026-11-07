# Frontend — Patch 001

Vue 3 + TypeScript + Vite, Vue Router, ECharts, Lucide. CSS lokal dengan token warna, font sistem; tanpa CDN saat runtime.

## Pasang
Ekstrak isi ZIP di akar monorepo HIMTEC-2026-Hackathon. ZIP berisi folder frontend/. Hanya berkas frontend ditimpa. Simpan .env lokal yang sudah ada.

Dari frontend/:
1. npm install
2. Salin .env.example menjadi .env, isi VITE_API_URL sesuai alamat backend Go (termasuk /api/v1).
3. npm run dev
4. npm run build untuk verifikasi produksi. npm run preview untuk melihat hasil build.

Gunakan alamat IP laptop frontend dan port 5173 dari ponsel pada jaringan yang sama. VITE_API_URL harus memakai IP backend yang dapat diakses ponsel; localhost pada ponsel mengarah ke ponsel sendiri. Backend perlu mengizinkan origin frontend lewat CORS_ORIGIN. Build ulang sesudah mengubah variabel untuk hasil produksi.

## Cakupan
Beranda, profil anak, pengukuran, status, kurva, riwayat/hapus dengan konfirmasi, KPSP 10 langkah bila API menyediakannya, catatan makan, panduan backend, laporan A4 lewat cetak browser/simpan PDF. Navigasi memakai hash agar dapat di-host statis tanpa pengaturan rewrite.

Menggunakan mode demo backend tanpa login sesuai MVP PRD. AUTH_MODE=otp_dummy membutuhkan frontend autentikasi pada patch terpisah; jangan gunakan patch ini dengan mode OTP. Tidak ada data kesehatan tiruan atau fallback status normal.

## Batas API
- Kuesioner KPSP belum didaftarkan engine: tampilkan pesan layanan, jangan mengarang pertanyaan.
- Referensi wfl_wfh dan rentang WHO di luar domain masih dapat gagal; pesan backend ditampilkan.
- Panduan masih kosong: tampilkan keadaan kosong.
- Daftar anak tidak menyediakan ringkasan: status diminta per anak, kegagalan tidak menggagalkan daftar.
- POST pengukuran/makan dapat menyimpan lalu gagal evaluasi. Baca riwayat sebelum kirim ulang; tidak ada retry POST otomatis.
- Frontend tidak menyusun penjelasan medis dan tidak menghitung klasifikasi.

## Verifikasi manual integrasi
Gunakan backend demo dan database uji. Tambah anak → catat pengukuran → status → kurva → laporan. Periksa validasi 422; hentikan engine dan pastikan riwayat tetap terbaca setelah POST 503. Hapus pengukuran dengan konfirmasi. Uji tanggal makan duplikat dan umur di luar cakupan. KPSP hanya diuji dengan bank API resmi ketika siap. Periksa lebar 360/768/1440, navigasi keyboard, zoom 200%, dan cetak A4.

Patch berisi sumber, bukan node_modules atau dist. Tidak mengubah backend, engine, kontrak, atau dokumen milik tim. Catatan serah terima frontend disimpan di frontend/README.md dan frontend/PROJECT_MEMORY.md karena workspace hanya mengizinkan perubahan frontend.

## Patch 002 — perbaikan integrasi dan uji browser

Terapkan setelah Patch 001 dengan mengekstrak ZIP di akar monorepo. Jalankan npm install karena dependensi pengujian ditambahkan. Perintah menjalankan aplikasi tetap sama. Tidak perlu mengubah .env atau database.

Perubahan: normalisasi angka/null pada formulir; pertahankan input ketika simpan gagal; abaikan respons halaman lama; laporan tetap memuat riwayat dan kurva PB/U ketika status gagal; kurva SVG untuk cetak; konfirmasi sebelum cetak tanpa kurva; filter panduan berdasarkan kategori/umur dan kartu terkait related_codes; perbaikan fokus dan format kode.

Verifikasi: 10 uji browser Chrome lokal lulus, termasuk viewport 360/768/1440. Semua API pada tes disimulasikan untuk memeriksa frontend, bukan validasi medis atau bukti integrasi layanan nyata. TypeScript dan build produksi lulus.

Jalankan npm test untuk mengulang tes. Tes memakai Chrome lokal dan server khusus port 5175; tidak menyentuh backend/database. Windows default mendeteksi Chrome di C:/Program Files/Google/Chrome/Application/chrome.exe. Jika berbeda, set CHROME_PATH ke executable Chrome/Chromium milikmu sebelum npm test. Screenshot uji tersimpan di test-results/ dan tidak disertakan dalam patch.
