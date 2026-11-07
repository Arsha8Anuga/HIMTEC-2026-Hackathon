# Patch 003 — status dan kurva (0.3.0)

Prasyarat: Patch 001 lalu Patch 002. Ekstrak ZIP di akar monorepo HIMTEC-2026-Hackathon. ZIP hanya berisi frontend/ dengan berkas baru/berubah. Tidak ada dependensi baru, migrasi, penghapusan berkas, atau perubahan .env. Jalankan npm run dev; verifikasi dengan npm run build dan npm test. Untuk rollback, pulihkan salinan berkas yang sama sebelum ekstraksi.

Perbaikan:
1. Profil beranda tampil tanpa menunggu semua evaluasi, disertai indikator memuat. Pengingat memakai data jadwal/kode backend.
2. Badge status memiliki ikon/teks dan detail z-score berasal dari API.
3. SVG kurva tidak lagi terkena ukuran ikon; pita mengikuti referensi backend dan legenda dapat digunakan lewat keyboard. Tabel tersedia dengan satuan, z-score, dan flag.
4. Array kurva tidak lengkap ditolak; grafik kosong tidak dicetak sebagai kurva tanpa konfirmasi.
5. Penyelesaian simpan/hapus setelah navigasi tidak memindahkan pengguna dari halaman baru.

Berkas: package.json, package-lock.json, README.md, PROJECT_MEMORY.md,
src/App.vue, src/style.css, src/components/StatusBadge.vue,
src/components/GrowthChart.vue, src/lib/growth.ts,
tests/frontend.spec.ts, tests/patch003.spec.ts, patches/PATCH_003.md.

Hasil: TypeScript dan build produksi lulus; 15 tes browser lulus termasuk 5 regresi baru. Grafik mobile diperiksa secara visual setelah menemukan dan memperbaiki masalah CSS SVG. Grafik memakai fixture angka simulasi untuk uji antarmuka, tidak membuktikan ketepatan medis. Media print grafik diperiksa; dokumen PDF A4 lengkap dan integrasi layanan nyata tetap perlu diuji. Peringatan ukuran bundle grafik ~504 kB (sebelum kompresi), dimuat terpisah saat halaman grafik/laporan dibuka.

Tidak mengubah backend/engine/dokumen di luar frontend. Mode backend tetap demo; OTP belum tersedia pada frontend. Salin ringkasan ini ke bagian frontend docs/CHANGELOG.md dan docs/HANDOFF.md saat penggabungan oleh tim monorepo.
