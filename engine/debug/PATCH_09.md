# Patch 09 — endpoint evaluasi, skor KPSP dan referensi umur

Terapkan setelah Patch 08 beserta hotfix dokumentasinya. Basis main yang
dibaca: `b10184d4c4ee861c6c0aac0cc60a235ce3e8952b`.
Tidak ada push GitHub, perubahan Go/frontend/kontrak/dependensi atau tabel WHO
yang dibundel. Semua definisi klinis tetap dari data/core patch sebelumnya.

## Yang dapat digunakan

| Endpoint | Hasil |
| --- | --- |
| GET `/engine/v1/health` | Status keberadaan kelima tabel WHO autentik |
| POST `/engine/v1/growth/evaluate` | `per_measurement`, `level`, `reasons`, `next_kpsp`, `diet` |
| POST `/engine/v1/kpsp/score` | `yes_count`, `result`; tidak memerlukan WHO/bank pertanyaan |
| GET `/engine/v1/reference` | `wfa`, `lhfa`, `hcfa`; lima garis SD per hari |

Evaluasi menggunakan core Patch 05–08 dan jadwal 07B tanpa mengubah ambang.
Klasifikasi, flag, tren dan tingkat dihitung sebelum z-score keluaran serta
`from_z`/`to_z` dibulatkan ke dua desimal. Nilai seperti -1,9999 dapat tampil
-2,00 tetapi klasifikasinya mengikuti angka penuh. Referensi memakai invers
LMS yang sudah tersedia; nilai ukuran pada kurva tidak dibulatkan seperti z.

Referensi berisi langsung `x`, `sd_neg3`, `sd_neg2`, `median`, `sd_pos2`,
`sd_pos3` di dalam `data`, cocok dengan pembungkus reference pada Go.
Rentang inklusif; `x_from=10&x_to=12` memberi hari 10, 11, 12.

## Batas yang masih nyata

- GET `/kpsp/questionnaire` tetap belum didaftarkan (404), sesuai penegasan
  kontrak, sampai gambar/rubrik dan review klinis lengkap. Tidak ada bypass
  `for_review=True` dari HTTP. Karena itu route KPSP next pada Go masih dapat
  gagal walaupun `next_kpsp` sudah ada dalam evaluasi.
- `indicator=wfl_wfh` pada `/reference` menghasilkan 503. Kontrak request hanya
  berisi indikator, sex dan rentang x; tidak ada umur/posisi untuk memilih dua
  tabel. Go saat ini meminta cm 40–130. Jangan menebak pilihan, menyambung WFL
  dengan WFH, menambah parameter atau mengubah backend tanpa kesepakatan.
- WHO umur tersedia 0–1826. Pengukuran di luar tabel atau reference melewati
  domain ini menghasilkan 503, tanpa hasil parsial, pemotongan rentang atau
  ekstrapolasi. Konflik izin kontrak sampai 1856 masih menunggu penyelarasan;
  grafik Go anak yang lebih tua dapat meminta rentang di luar domain.
- Grid ukuran cm mengikuti kontrak 0,1 cm; angka di luar grid ditolak 422,
  tanpa pembulatan diam-diam. WFL/WFH untuk evaluasi titik tetap dipilih dari
  umur dan posisi dikoreksi core, lalu lookup tepat pada grid tabel. Ukuran
  terkoreksi di luar tabel menyebabkan 503.
- Umur bulat KPSP di luar 0–60 pada `as_of` ditolak 422 sebagaimana cakupan
  core/kontrak 07B. Skema batas tanggal pengukuran tidak diubah sepihak.
- Aturan posisi tetap kontrak (731 hari). Isu flag WHO berdiri sebelum 9 bulan
  dan pembulatan flag belum diselaraskan; hasil tidak diklaim identik dengan
  seluruh WHO Anthro. Lima kasus klinis pembanding penuh masih diperlukan.
- Patch ini belum membuktikan integrasi Go/PostgreSQL/frontend/laptop tim.
  Health atau route terdaftar bukan bukti semua fitur/domain siap.

## Error dan data

Semua respons endpoint di atas memakai `{data, error}`. Input tidak valid:
422/VALIDATION_ERROR dengan fields. Validasi body, grid dan jadwal dilakukan
sebelum membaca WHO, sehingga berkas hilang tidak menutupi error input.
WHO hilang, checksum rusak atau domain belum tersedia: 503/ENGINE_UNAVAILABLE.
Error tak terduga: 500/INTERNAL. Error tidak memuat data anak, path internal,
atau traceback; server mempertahankan log exception bawaan.

Kelima berkas WHO diverifikasi pada setiap permintaan evaluasi/referensi.
Tidak ada network saat runtime, cache riwayat anak, database atau hasil
normal pengganti. Score KPSP independen dari kesiapan bank; keberhasilan
score tidak membuktikan pertanyaan siap diberikan ke orang tua.

## Pengujian aktual

Lingkungan lokal: Python 3.12; requirements repository berhasil dipasang:
FastAPI 0.128.2, Pydantic 2.13.5, pytest 9.0.2 dan httpx 0.28.1.

- Suite lengkap dengan kelima berkas WHO resmi yang lolos checksum:
  **262 passed, 137 subtests passed, 1 warning**, 4,01 detik.
- Suite lengkap ketika direktori WHO sementara ditiadakan, lalu dipulihkan:
  **246 passed, 16 skipped, 137 subtests passed, 1 warning**, 1,69 detik.
- Tes endpoint baru: **37 passed**. Mencakup struktur respons lengkap,
  WHO autentik + diet + jadwal, enam kombinasi indikator/sex referensi,
  batas akhir hari 1826, presisi setelah klasifikasi, skor tanpa WHO,
  validasi input, sanitasi exception dan kegagalan domain eksplisit.
- Warning berasal alias `BlockingPortal` Starlette/AnyIO yang deprecated,
  bukan kegagalan tes. Ini hasil pengembangan lokal, bukan hasil Windows.
- Smoke server Uvicorn melalui HTTP localhost nyata lulus untuk health,
  evaluasi, referensi lengkap 1827 hari dan skor; tiga panggilan terakhir
  berurutan selesai 0,27 detik secara lokal. Bukan tolok ukur jaringan tim
  atau pengujian Go end-to-end.

## Memasang dan menjalankan

Ekstrak ke akar repo sehingga berkas berada di `engine/app/...` dan
`docs/...`. Pertahankan data WHO lokal. Dari folder engine:

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Bila WHO belum tersedia, jalankan saat setup dengan internet:

```powershell
python scripts/fetch_who_tables.py
```

Cek `http://127.0.0.1:8001/engine/v1/health` serta `/docs` pada origin yang
sama. Contoh referensi:
`/engine/v1/reference?indicator=lhfa&sex=female&x_from=0&x_to=500`.

Untuk menguji melalui Go, gunakan `ENGINE_URL` engine asli secara eksplisit
pada terminal Go dan restart prosesnya. Fake engine sebelumnya berada di
port lain dan hasilnya fixture. Pilih data dalam domain yang tersedia;
pengujian questionnaire/reference gabungan masih memiliki batas di atas.
Jika Go sempat menyimpan pengukuran/catatan makan lalu mengembalikan 503,
baca riwayat terlebih dahulu sebelum mengirim ulang.

## Berkas patch

- `app/api/evaluation.py`: tiga adapter endpoint untuk core yang sudah ada.
- `app/api/errors.py`, `app/main.py`: pendaftaran route/error bersama.
- `tests/test_api_foundation.py`: sesuaikan tes fondasi dengan route nyata.
- `tests/test_evaluation_api.py`: regresi HTTP dan integrasi WHO.
- `debug/PATCH_09.md`, `docs/HANDOFF.md`, `docs/CHANGELOG.md`.

Dokumen bersama digabung dari repo terbaru saat pengemasan, termasuk bukti
backend pukul 14:14. Bagian backend/frontend/matriks dipertahankan persis;
semua catatan CHANGELOG sebelumnya dipertahankan. Periksa perubahan tim yang
lebih baru sebelum menimpa dokumen dari ZIP.
