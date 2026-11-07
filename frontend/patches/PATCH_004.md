# Patch 004 — 0.4.0

Prasyarat: Patch 001–003 diterapkan berurutan. Ekstrak di akar monorepo HIMTEC-2026-Hackathon; ZIP hanya menimpa berkas frontend yang berubah. Tidak perlu perubahan database, .env atau dependensi. Jalankan npm run dev. Rollback: pulihkan cadangan berkas yang sama sebelum ekstraksi.

Isi: package.json, package-lock.json, README.md, PROJECT_MEMORY.md, src/App.vue,
src/style.css, src/components/KpspQuestionnaire.vue, src/components/FieldError.vue,
tests/patch004.spec.ts, patches/PATCH_004.md.

Perubahan:
- KPSP sepuluh butir unik, pemeriksaan bank rusak, jawaban bertahan saat POST gagal, fokus antar-butir, dan layar hasil dari respons backend.
- Riwayat KPSP dan kuesioner dimuat independen. Bank belum siap tetap ditampilkan sebagai belum tersedia; tidak ada pertanyaan medis baru.
- Validasi API pada kontrol tambahan memakai pesan inline/aria-describedby.
- Identitas laporan di awal; tabel pengukuran dengan lingkar kepala dan sumber; alasan terbuka pada laporan dan CSS cetak A4.
- Metrik pengukuran tetap dapat dibaca dari riwayat tanpa membuat evaluasi kesehatan pengganti.

Hasil: npm run build / TypeScript lulus; 22 tes Playwright API simulasi lulus (7 tambahan). PDF A4 uji dihasilkan, tampilan media cetak diperiksa, termasuk pesan kurva gagal. Tidak menguji hasil klinis, WHO Anthro atau bank KPSP resmi. Tidak ada data uji/PDF/screenshot/credential dalam patch. Peringatan bundle grafik lazy-loaded ~504 kB tetap.

Langkah berikutnya: Patch 005 untuk integrasi backend/engine nyata dan perbaikan berdasarkan hasilnya. Frontend tetap mode demo; OTP opsional di luar MVP. File tim di luar frontend tidak diubah; ringkasan ini dapat dipindahkan ke bagian frontend docs/CHANGELOG.md dan docs/HANDOFF.md oleh tim saat penggabungan.
