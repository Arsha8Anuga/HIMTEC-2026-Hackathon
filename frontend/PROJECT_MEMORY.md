# Memori proyek frontend

Acuan dibaca: Arsha8Anuga/HIMTEC-2026-Hackathon main 4e61bf2da5e45a6a5400729b26776b7a2933e62a, kontrak v0.5 draf dan PRD. Jangan menyamakan README/HANDOFF lama dengan kesiapan kode engine Patch 09.

Aturan tetap: hanya frontend; API lewat VITE_API_URL; backend Go satu-satunya pintu. snake_case, tanggal lokal YYYY-MM-DD, kg/cm. Teks medis dari backend. Tidak menambah endpoint/enum. Demo offline setelah setup, tanpa CDN. Jangan mengubah folder pemilik lain.

Keputusan visual: teal #23695b, latar #f7f8f5, putih, warna tingkat dengan teks, font sistem. Desktop sidebar, mobile bottom nav dua tujuan. Vue 3 Composition API, CSS token tanpa framework tambahan, ikon Lucide, grafik ECharts dari data API. Hash routes.

Batas diketahui: KPSP questionnaire belum aktif; reference wfl_wfh belum siap; WHO 1826 vs kontrak 1856; guides kosong; login produksi di luar MVP. Patch 001 memakai mode demo tanpa OTP. Tidak mengarang status atau angka WHO.

Versi: patch 001 fondasi seluruh layar. File utama App.vue, lib/api.ts, components/GrowthChart.vue, style.css. API error mempertahankan pesan/fields backend, abort 12 detik, tidak retry POST. Dokumen ini memori berkas lokal, bukan klaim memori permanen asisten.

Paket ZIP diekstrak dari akar monorepo dan berisi frontend/. Patch berikutnya hanya mengemas berkas berubah; tambahkan nomor, daftar berkas, hasil uji, dan instruksi rollback. Jangan memasukkan .env, node_modules, data pasien atau token. Cadangkan berkas yang ditimpa sebelum ekstraksi.

## Patch 002 (0.2.0)
- Normalisasi request ada di src/lib/forms.ts. Angka kosong opsional -> null, angka terisi -> number. Jangan memakai coercion truthy yang mengubah nol.
- Load halaman memiliki nomor versi; respons lama diabaikan. Growth memakai versi terpisah dan laporan selalu meminta lhfa.
- Status/riwayat/KPSP laporan dimuat independen via allSettled; kegagalan status tidak menghentikan kurva. Kurva SVG emit ready sebelum tombol print aktif. Jika kurva gagal, pengguna memilih eksplisit cetak tanpa kurva.
- API memeriksa envelope dan 204; field validasi dan input tetap dipertahankan saat gagal.
- Panduan: API query category/age_months, status memfilter related_codes. Tidak mengarang materi.
- npm test: 10 tes Playwright dengan Chrome lokal dan API mock; lulus pada sesi ini, viewport 360/768/1440. Bukan end-to-end dengan Go/WHO. npm run build lulus.
- OTP masih belum diimplementasikan; tetap mode demo. Tidak mengubah engine/backend/kontrak.

## Patch 003 (0.3.0)
- src/components/StatusBadge.vue: ikon + teks tingkat; tidak menentukan level klinis.
- src/lib/growth.ts: tipe GrowthData dan pemeriksaan bentuk array/nilai finite, tanpa ambang medis.
- Kurva memakai SVG dan poligon antara garis API, bukan stack numeric axis (stack dapat menggeser sumbu x). CSS ukuran ikon harus tetap pada .lucide, jangan selector svg global, karena mengecilkan grafik.
- Beranda menampilkan profil sebelum status selesai. Pengingat hanya dari next_kpsp.due/NO_RECENT_FOOD_RECALL backend. Jangan menyimpulkan jadwal dari umur sendiri.
- Mutasi menyimpan route pemilik; penyelesaian setelah navigasi tidak mengalihkan halaman pengguna. Refresh makan setelah gagal simpan juga memeriksa pemilik route.
- Grafik kosong pada laporan memerlukan konfirmasi eksplisit cetak tanpa kurva. Legend checkbox terjangkau keyboard; tabel memiliki unit/z-score. Pita tidak mempunyai arti klasifikasi tambahan.
- Verifikasi aktual: 15 tes Playwright API simulasi lulus, build/TypeScript lulus. Screenshot grafik 360px diperiksa sesudah perbaikan ukuran SVG; test menegaskan lebar SVG sama dengan wadah, supaya bug tidak lolos hanya dengan keberadaan elemen. Mode print grafik juga diperiksa.
- Batas sebelumnya tetap: OTP belum ada; guides/questionnaire/domain WHO mengikuti kesiapan API; belum integrasi Go/engine asli. Peringatan bundle grafik sekitar 504 kB; lazy loaded, bukan kegagalan build.

## Patch 004 (0.4.0)
- KpspQuestionnaire.vue menyimpan jawaban per item_no, tepat 10 nomor unik, teks pertanyaan dari API, null/duplikat ditolak. Tidak menghitung skor. Parent submit menerima answers dari komponen; POST berhasil menampilkan result/yes_count backend dan fokus hasil.
- KPSP GET history dan next memakai allSettled independen; error POST tidak menyediakan reload yang menghapus jawaban. Draft hanya memori komponen, tidak disimpan ke disk/browser storage.
- FieldError.vue menghubungkan pesan backend ke aria-describedby kontrol tambahan; angka/null tetap forms.ts.
- Laporan: identitas di awal, LK/sumber di tabel, alasan dibuka saat report, A4 CSS dan repeated table headers. displayMeasurement menggunakan status.latest atau riwayat terbaru (tanpa klasifikasi buatan).
- Verifikasi aktual: 22 tes Playwright API simulasi lulus; TypeScript/build lulus. PDF A4 test dihasilkan dan media cetak diperiksa visual, data uji bukan data medis riil. Grafik lazy bundle warning ~504kB tetap.
- Patch 005 tersisa untuk integrasi layanan asli. Tidak menyatakan seluruh kriteria penerimaan PRD terverifikasi; bank KPSP/guides/domain WHO bergantung backend. Mode demo tanpa OTP tetap.
