# WHO Child Growth Standards: data lokal

Engine hanya membaca referensi WHO secara **offline**. Tidak ada angka medis buatan
atau data WHO parsial yang dibundel dalam patch ini.

## Sumber resmi (diakses 7 November 2026)

- [WHO Child Growth Standards](https://www.who.int/tools/child-growth-standards/standards)
- [WHO `anthro` (data harian LMS)](https://github.com/WorldHealthOrganization/anthro/tree/master/data-raw/growthstandards)
- Commit upstream yang dipin: `b776d8a12b1c97369c748b561159fd2ec4f4db58`
- Lisensi sumber: [WHO Anthro GPL-3](https://github.com/WorldHealthOrganization/anthro/blob/master/LICENSE.md)

**Penting:** Lisensi data dan persyaratan atribusi harus ditinjau tim sebelum
file dari WHO dimasukkan ke repository publik atau dibagikan ke luar tim.
Patch ini belum menyalin/mendistribusikan tabel WHO.

## Persiapan data (sekali, butuh koneksi internet)

Dari root `engine/`:

```bash
python scripts/fetch_who_tables.py
python -m pytest -q
```

Script mengunduh 5 berkas `.txt` dari commit WHO yang dipin, lalu memverifikasi
**Git blob SHA-1** dan kelengkapan seluruh tabel sebelum menyimpan:

| Nama file WHO | Indikator | Sumbu | Rentang sumber |
| --- | --- | --- | --- |
| `weianthro.txt` | wfa (BB/U) | hari | 0–1826 |
| `lenanthro.txt` | lhfa (PB/TB/U) | hari | 0–1826 |
| `wflanthro.txt` | wfl (BB/PB) | panjang cm, 0,1 cm | 45,0–110,0 |
| `wfhanthro.txt` | wfh (BB/TB) | tinggi cm, 0,1 cm | 65,0–120,0 |
| `hcanthro.txt` | hcfa (LK/U) | hari | 0–1826 |

Jika unduhan gagal, buka repositori WHO di atas, pilih `data-raw/growthstandards`,
dan unduh kelima file `.txt` **dari commit yang dipin** ke `engine/data/who/`.
Jangan mengedit nilainya; checksum gagal bila berubah.

`GET /engine/v1/health` akan melaporkan `who_tables_loaded: true` **hanya**
jika semua tabel asli valid dan lengkap. Perhitungan z-score belum
tersedia pada Patch 03; health true berarti **data terverifikasi**, bukan
fitur medis sudah bisa dipakai.

## Catatan kontrak yang perlu diputuskan pemiliknya

Sejak kontrak v0.6, batas umur pengukuran 1826 hari, sama dengan tabel
WHO Anthro harian berbasis usia; tidak ada ekstrapolasi (lihat "Penegasan
v0.6" di `docs/CONTRACT.md`).

Hal lain yang belum diselesaikan: WHO `wfl`/`wfh` memakai langkah 0,1 cm.
Data input lebih presisi dari itu tidak boleh dibulatkan diam-diam sebelum
metode penyelarasan disetujui dan diuji dengan WHO Anthro.

## Patch 04: fungsi perhitungan murni

`app/core/growth_math.py` menyediakan `lms_zscore`, `restricted_lms_zscore`,
`lms_value_at_z`, `correct_length_height_cm`, dan `interpolate_length_lms`.
Matematika diselaraskan dengan kode R WHO Anthro pada commit yang dipin,
khususnya `R/z-score-helper.R` serta `R/z-score-weight-for-lenhei.R`.

- Pakai **restricted LMS** hanya untuk BB/U serta BB/PB atau BB/TB;
  PB/TB/U dan LK/U menggunakan LMS biasa. Z-score dipertahankan pada
  presisi penuh untuk perhitungan dan baru dibulatkan pada respons akhir.
- Koreksi posisi sesuai `docs/CONTRACT.md` v0.4: umur <731 hari,
  ukuran berdiri ditambah 0,7 cm; umur >=731 hari, ukuran berbaring
  dikurangi 0,7 cm. Aturan WHO Anthro tentang pengukuran berdiri
  sebelum usia 9 bulan perlu diputuskan pemilik kontrak.
- WHO Anthro menggunakan interpolasi linear LMS antara dua baris WFL/WFH
  berjarak 0,1 cm untuk ukuran pecahan. Utilitas sudah tersedia
  **terpisah** tetapi tidak otomatis dipakai endpoint hingga aturan
  presisi disetujui. Di luar domain WHO harus ditolak, bukan diekstrapolasi.
- Patch 04 menguji kasus numerik dari tes upstream WHO Anthro serta
  batas matematis. **Belum** ada evaluasi kesehatan atau klasifikasi
  pada API dan **belum** ada validasi lima kasus end-to-end WHO Anthro.

Referensi implementasi:

- https://github.com/WorldHealthOrganization/anthro/blob/b776d8a12b1c97369c748b561159fd2ec4f4db58/R/z-score-helper.R
- https://github.com/WorldHealthOrganization/anthro/blob/b776d8a12b1c97369c748b561159fd2ec4f4db58/R/z-score-weight-for-lenhei.R
- https://github.com/WorldHealthOrganization/anthro/tree/b776d8a12b1c97369c748b561159fd2ec4f4db58/tests/testthat
