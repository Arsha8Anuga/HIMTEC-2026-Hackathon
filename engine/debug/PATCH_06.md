# Patch 06 — early warning core

Basis kode: `1aeec608b6f8d99a615197e5f36153e742dc47ad` (Patch 05).

## Isi dan sumber

`app/core/early_warning.py` menyediakan
`evaluate_early_warning(request, tables)`. Fungsi memanggil core Patch 05 dan
mengembalikan `per_measurement`, `level`, `reasons` tanpa menyimpan status.
Seluruh angka aturan dibaca dari `data/early_warning.json`, dengan sumber
`docs/CONTRACT.md` v0.4 dan klarifikasi kalender pengguna, 7 November 2026.
Aturan tren merupakan heuristik skrining proyek, bukan kriteria diagnosis WHO.

Kode yang dicakup: SEVERELY_STUNTED, STUNTED, SEVERELY_WASTED, WASTED,
SEVERELY_UNDERWEIGHT, UNDERWEIGHT, OVERWEIGHT, WEIGHT_NOT_GAINING,
WEIGHT_NOT_GAINING_2X, CROSSING_DOWN, PROJECTED_STUNTING, HOME_MEASUREMENT,
IMPLAUSIBLE_VALUE, NO_RECENT_LENGTH, KPSP_DEVIATION dan KPSP_DOUBTFUL.
Setiap kode memiliki kasus tes. Riwayat KPSP hanya dibaca; skor/jadwal dan
kuesioner belum diimplementasikan.

## Kebijakan kalender yang digunakan

- Klarifikasi pengguna: periode harus berbeda bulan dan boleh memakai kalender.
- Untuk 1T/2T, setiap bulan diwakili pengukuran valid terakhir dalam bulan itu.
  Pengukuran pada bulan yang sama tidak menjadi periode bulanan tambahan.
- 1T membandingkan bulan terakhir dengan tepat satu bulan kalender sebelumnya.
  2T membutuhkan tiga bulan kalender berurutan dan dua interval tidak naik.
  Jika 2T aktif, kode 1T tidak ditambahkan lagi.
- Bulan terlewat atau bulan yang hanya berisi titik implausible memutus rantai.
  Tidak menyambungkan Januari ke Maret sebagai periode bulanan berurutan.
- Tidak ada batas minimum hari tambahan: 31 Januari ke 1 Februari memenuhi
  kebijakan kalender walaupun hanya satu hari. Ini konsekuensi kebijakan
  proyek, bukan penetapan interval penimbangan klinis yang direkomendasikan.
- Kenaikan <=0 g dipakai sementara, sesuai izin eksplisit kontrak, karena
  tabel KBM resmi Buku KIA belum ditranskripsi. Kode tidak mengklaim telah
  menerapkan KBM berbasis umur. Kebijakan ini belum menaikkan versi kontrak;
  pemilik kontrak perlu memasukkan klarifikasi ke versi berikutnya.

## Aturan lain

- Input disortir internal menurut tanggal; output `per_measurement` tetap
  sesuai urutan input. Tidak ada mutasi atau perubahan data dalam database.
- Titik implausible dikeluarkan dari semua tren. Jika titik terbaru implausible,
  tampilkan infonya, tanpa mengganti statusnya dengan klasifikasi titik lama.
- CROSSING_DOWN memakai pembanding valid 60–120 hari sebelumnya, batas
  inklusif, penurunan >=0,67. Jika ada beberapa pembanding memenuhi, bukti
  menggunakan penurunan terbesar; tanggal terbaru memecahkan nilai seri.
  WFA dan LHFA dapat menghasilkan dua alasan berkode sama dengan bukti
  indikator berbeda. Tidak ada pembulatan z-score sebelum perbandingan.
- Proyeksi memakai regresi linear OLS LHFA terhadap hari, >=3 titik valid
  dalam enam bulan kalender sebelum `as_of`, termasuk batasnya. Tanggal
  dipotong ke hari terakhir bulan tujuan bila perlu. Horizon 90 hari dihitung
  dari `as_of`. Harus ada kemiringan negatif dan garis menembus -2 pada
  waktu >0 sampai <=90 hari; garis yang sudah menembus sebelum `as_of`
  tidak diberi kode proyeksi baru. LHFA pengukuran terakhir harus >=-2.
- NO_RECENT_LENGTH memakai tanggal `as_of`: panjang valid berumur <=90 hari
  masih dianggap terkini. Panjang dari titik implausible tidak dihitung.
- KPSP memakai hasil terbaru menurut answered_at, umur kuesioner terbesar
  sebagai pemecah tanggal seri. Tidak mengarang masa kedaluwarsa hasil.
- Level adalah alasan tertinggi: red > yellow > green; info tidak menaikkan
  level. Green berarti tidak ada alasan red/yellow yang ditemukan oleh modul,
  bukan bukti anak sehat atau datanya lengkap. Riwayat kosong tetap kosong.

## Batas integrasi

Ini core, **bukan respons evaluasi publik lengkap**. `/growth/evaluate` tetap
belum aktif. `next_kpsp`, `diet`, skor/kuesioner KPSP dan IYCF belum lengkap.
Jangan memasang hasil core ini langsung sebagai respons endpoint final.
Go tetap bertugas menerjemahkan kode menjadi kalimat; proyeksi harus ditulis
sebagai perkiraan. Tidak ada endpoint, enum, dependensi atau kontrak yang diubah.

Masalah domain WHO 1826 vs 1856 hari, grid 0,1 cm, posisi berdiri sebelum
9 bulan dan penyelarasan pembulatan flag dari Patch 05 tetap terbuka.
Kesalahan lookup WHO diteruskan, tidak diganti dengan level green.

## Pengujian dan penerapan

- Patch 05 di laptop pengguna: **119 passed, 3 skipped, 52 subtests passed,
  1 warning**, 1,18 detik. Tiga tes WHO asli belum berjalan pada hasil itu.
- Patch 06: **29 tes baru lulus** via unittest, termasuk satu integrasi dengan
  lima tabel WHO autentik yang diverifikasi loader. Banyak batas memiliki
  subkasus tambahan; angka 29 adalah jumlah metode tes.
- Tanpa data WHO, 28 tes baru berjalan dan 1 integrasi dilewati.
- Pytest penuh tetap dicoba tetapi belum tersedia di lingkungan ini
  (`No module named pytest`). Jangan menyebut seluruh suite Patch 06 lulus
  berdasarkan hasil unittest. Lingkungan lokal Python 3.12/Pydantic 2.14.2,
  sedangkan laptop pengguna Python 3.10.6.

Ekstrak ZIP ke akar repository setelah Patch 05. Dari folder `engine/`:

```bash
python -m unittest discover -s tests -p test_early_warning.py -v
python scripts/fetch_who_tables.py
python -m pytest -q
```

Dengan tabel WHO lengkap, diperkirakan ada 151 metode/kasus pytest; tanpa
tabel ada 4 tes integrasi yang dilewati di seluruh suite. Catat hasil nyata.
Data WHO tidak dibundel ZIP. Dokumen bersama diperiksa dari GitHub terbaru;
jika tim mengubahnya setelah itu, merge bagian engine/entri Patch 06 saja.
