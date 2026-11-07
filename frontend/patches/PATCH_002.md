# Patch 002 — 0.2.0

Prasyarat: Patch 001. Ekstrak di akar HIMTEC-2026-Hackathon, sehingga berkas menimpa frontend/. Simpan cadangan berkas yang sama untuk rollback. Tidak ada penghapusan atau migrasi.

Perubahan:
- Request formulir memakai number/null yang benar, termasuk isian opsional yang sempat diisi lalu dihapus.
- Input/validasi dipertahankan saat API gagal; riwayat catatan makan dibaca ulang tanpa mengirim POST ulang.
- Respons lama tidak mengganti profil/kurva setelah navigasi.
- Laporan memuat riwayat dan kurva PB/U secara independen; SVG siap cetak dan konfirmasi cetak tanpa kurva.
- Panduan disaring menurut umur/kategori dan related_codes backend.
- Akses keyboard, halaman tidak ditemukan, format kode, pemeriksaan respons API diperbaiki.

Berkas berubah/baru:
package.json, package-lock.json, .gitignore, README.md, PROJECT_MEMORY.md,
playwright.config.ts, tests/frontend.spec.ts, src/App.vue, src/style.css,
src/lib/api.ts, src/lib/forms.ts, src/components/GrowthChart.vue,
patches/PATCH_002.md.

Verifikasi: npm run build (TypeScript + produksi) lulus; 10 uji Playwright Chrome lokal lulus. Tes API simulasi, bukan hasil medis nyata atau bukti integrasi backend. Screenshot formulir 360/1440 diperiksa; pengujian lebar 360/768/1440 tidak menemukan overflow horizontal. Print PDF dan integrasi Go/PostgreSQL/engine asli belum diuji menyeluruh.

Sesudah ekstraksi: npm install, lalu npm run dev. Ulang tes dengan npm test (lihat README untuk CHROME_PATH).

Tidak termasuk .env, node_modules, dist, screenshot, token, atau data pasien. Tidak ada perubahan folder tim lain. Catatan untuk tim: ringkasan ini dapat disalin ke bagian frontend docs/CHANGELOG.md dan docs/HANDOFF.md oleh pemilik workspace monorepo; file di luar frontend belum diubah.
