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

`docs/CONTRACT.md` v0.4 menerima pengukuran anak sampai 1856 hari, sedangkan
tabel WHO Anthro harian berbasis usia hanya hingga 1826 hari. Endpoint
perhitungan belum boleh mengekstrapolasi melebihi sumber; perlu disepakati
batas validasi usia (tanpa mengubah kontrak sendiri).

Hal lain yang belum diselesaikan: WHO `wfl`/`wfh` memakai langkah 0,1 cm.
Data input lebih presisi dari itu tidak boleh dibulatkan diam-diam sebelum
metode penyelarasan disetujui dan diuji dengan WHO Anthro.
