# Patch 05 — evaluasi per pengukuran

Basis kode: `af4193a6da0a9019a25f25738b0e9caf9243ffac`, setelah Hotfix 04A.

## Isi

- `app/core/growth_evaluation.py`: `evaluate_measurement` dan
  `evaluate_measurements` menghubungkan skema tervalidasi dengan tabel WHO.
  Menghitung umur pada tanggal ukur, koreksi posisi, WFA, LHFA, WFL/WFH,
  HCFA opsional; hasil mempertahankan urutan input dan tidak mengubah data.
- `data/anthropometry.json`: ambang klasifikasi ditranskripsi dari Permenkes
  2/2020 Lampiran Bab II B, halaman tercetak 14 (PDF halaman ke-14).
  URL resmi, commit sumber WHO untuk flag, dan pemetaan enum dicatat di JSON.
- `app/core/anthropometry.py`: membaca ambang dari data lokal untuk
  klasifikasi dan flag. Tidak ada angka ambang medis dari ingatan AI.
- Jika satu indikator WFA/LHFA/WFL-WFH kena flag, `flags` memuat satu
  `IMPLAUSIBLE_VALUE`; semua klasifikasi titik itu `None` dan z-score tetap
  ada sebagai bukti. Titik ini wajib dikeluarkan dari tren pada patch berikutnya.
  `None` tidak berarti normal. HCFA hanya dihitung, tanpa klasifikasi/flag
  tambahan karena belum diatur kontrak.
- Z-score tetap presisi penuh pada core. Pembulatan dua desimal dilakukan di
  batas API kelak. Perbandingan batas memakai nilai mentah mengikuti Patch 04
  dan kontrak; WHO Anthro membulatkan sebelum flag, sehingga kasus sangat
  dekat ambang dapat berbeda dan harus dibahas sebelum klaim kesetaraan penuh.

## Batas yang sengaja belum diputuskan

Tidak ada endpoint baru, perubahan kontrak, dependency, database, ataupun
perubahan kode backend/frontend dalam patch ini. `/growth/evaluate` tetap
belum aktif. Level/reasons/tren, KPSP dan IYCF belum diimplementasikan.

Lookup mengikuti grid 0,1 cm kontrak; tidak membulatkan input presisi tinggi
diam-diam dan belum memakai utilitas interpolasi. `WHODataError` diteruskan
untuk koordinat di luar tabel, data yang hilang atau ukuran tidak tepat grid.
Jangan menangkap error ini lalu menggantinya dengan nilai normal/nol.

Skema kontrak tetap menerima sampai 1856 hari, tetapi tabel harian hanya
0–1826; umur 1827–1856 gagal lookup, bukan diekstrapolasi. Domain WFL
45–110 cm dan WFH 65–120 cm juga lebih sempit daripada rentang input umum.
Kebijakan penanganan domain, presisi, flag berdiri sebelum 9 bulan, dan
pembulatan flag harus dikunci sebelum endpoint publik diaktifkan.

## Verifikasi

- Hotfix 04A: pengguna melaporkan **107 passed, 1 warning, 1,49 detik** di
  Windows/Python 3.10.6. Warning deprecation berasal dari Starlette/AnyIO.
- Patch 05: **15 tes unittest lulus**, termasuk tiga pemeriksaan dengan tabel
  WHO asli yang diverifikasi loader/checksum. Batas klasifikasi, flag,
  kesalahan domain, koreksi umur 730/731, data opsional, presisi, dan tidak
  adanya mutasi dicakup. Satu metode memuat beberapa subkasus batas.
- Tanpa berkas WHO: suite baru lulus dengan 3 tes integrasi dilewati.
  Berkas yang ada tetapi rusak tidak dilewati: loader akan menggagalkan tes.
- Kompilasi modul berhasil. Lingkungan lokal: Python 3.12, Pydantic 2.14.2.
  Pytest penuh belum dapat dijalankan di sini (`No module named pytest`);
  instalasi requirements gagal di lingkungan ini. Hasil 107 bukan hasil
  suite Patch 05. Tidak ada klaim bahwa semua tes baru telah lulus pytest.
- Tiga kasus resmi yang dibandingkan adalah kasus LHFA male hari 44,
  WFA female hari 1522, dan flag WFA female hari 1 dari tes WHO Anthro.
  Ini belum memenuhi lima kasus lengkap end-to-end pada kriteria PRD F-03.

Semua tes baru memakai `unittest.TestCase` yang dapat dikoleksi oleh pytest.
Dari folder `engine/`, setelah dependensi terpasang:

```bash
python -m unittest discover -s tests -p test_growth_evaluation.py -v
python -m pytest -q
```

Jika semua data WHO tersedia, pytest diperkirakan mengoleksi 122 kasus
(107 sebelumnya + 15 baru); angka hasil nyata tetap harus dicatat.
Data WHO tidak dibundel. Jika belum ada, unduh saat setup menggunakan
`python scripts/fetch_who_tables.py`, lalu jalankan suite lagi.

## Penerapan

Ekstrak ZIP ke akar repository setelah Hotfix 04A. Berkas `docs/` berasal
dari GitHub terbaru yang diperiksa sebelum pengemasan; jika tim sudah
mengubahnya lagi, merge entri engine Patch 05 dan bagian Engine saja.
Bagian backend/frontend dan riwayat perubahan tim tetap dipertahankan.
