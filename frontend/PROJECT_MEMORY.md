# Memori proyek frontend

Acuan dibaca: Arsha8Anuga/HIMTEC-2026-Hackathon main 4e61bf2da5e45a6a5400729b26776b7a2933e62a, kontrak v0.5 draf dan PRD. Jangan menyamakan README/HANDOFF lama dengan kesiapan kode engine Patch 09.

Aturan tetap: hanya frontend; API lewat VITE_API_URL; backend Go satu-satunya pintu. snake_case, tanggal lokal YYYY-MM-DD, kg/cm. Teks medis dari backend. Tidak menambah endpoint/enum. Demo offline setelah setup, tanpa CDN. Jangan mengubah folder pemilik lain.

Keputusan visual: teal #23695b, latar #f7f8f5, putih, warna tingkat dengan teks, font sistem. Desktop sidebar, mobile bottom nav dua tujuan. Vue 3 Composition API, CSS token tanpa framework tambahan, ikon Lucide, grafik ECharts dari data API. Hash routes.

Batas diketahui: KPSP questionnaire belum aktif; reference wfl_wfh belum siap; WHO 1826 vs kontrak 1856; guides kosong; login produksi di luar MVP. Patch 001 memakai mode demo tanpa OTP. Tidak mengarang status atau angka WHO.

Versi: patch 001 fondasi seluruh layar. File utama App.vue, lib/api.ts, components/GrowthChart.vue, style.css. API error mempertahankan pesan/fields backend, abort 12 detik, tidak retry POST. Dokumen ini memori berkas lokal, bukan klaim memori permanen asisten.

Paket ZIP diekstrak dari akar monorepo dan berisi frontend/. Patch berikutnya hanya mengemas berkas berubah; tambahkan nomor, daftar berkas, hasil uji, dan instruksi rollback. Jangan memasukkan .env, node_modules, data pasien atau token. Cadangkan berkas yang ditimpa sebelum ekstraksi.
