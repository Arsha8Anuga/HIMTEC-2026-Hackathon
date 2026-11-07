# Patch 08 — catatan makan dan pola peringatan IYCF

Basis kode: `4ca72a386b03ee92213f6cfe8109ba7ea7c499e3`, setelah 07B.

## Yang ditambahkan

- `app/core/iycf.py`: evaluate_food_recall, evaluate_diet dan
  evaluate_growth_and_diet; seluruh ambang dibaca dari data/iycf/rules.json.
- MDD: kelompok berbeda dihitung sekali, ASI menambah satu kelompok;
  minimal lima dari delapan. Duplikasi checkbox tidak menaikkan hitungan.
- MMF: menyusu umur <9 bulan minimal dua kali makanan; menyusu >=9 bulan
  minimal tiga. Tidak menyusu minimal empat kali gabungan makanan/susu,
  dengan minimal satu kali makanan padat/semi-padat/lunak.
- MMF bukan indikator minimum frekuensi susu atau minimum acceptable diet.
  Empat kali makanan tanpa susu bisa memenuhi MMF, bukan bukti seluruh
  kebutuhan makan/susu telah terpenuhi.
- EFF: telur atau flesh foods. Kode kontrak NO_ANIMAL_SOURCE_FOOD merujuk
  indikator spesifik ini; dairy saja tidak memenuhi EFF. Jangan mengartikannya
  sebagai pernyataan bahwa susu bukan produk hewani.
- milk_feed_count yang tidak diisi dihitung nol untuk MMF, sesuai konvensi
  perhitungan frekuensi yang hilang dalam pedoman 2021. Ini konvensi hitungan,
  bukan bukti anak pasti tidak minum susu. Jumlah susu tidak otomatis mengisi
  checkbox dairy. Untuk anak menyusu, jumlah susu non-ASI tidak mengganti
  frekuensi makanan pada MMF.

## Sumber dan batas umur

Definisi indikator diverifikasi melalui WHO/UNICEF 2021 (ISBN 9789240018389),
metadata MMF WHO dan daftar indikator UNICEF; URL lengkap tercatat di JSON.
Ini adaptasi untuk skrining proyek, bukan diagnosis individual atau penilaian
porsi, energi, kualitas gizi keseluruhan maupun sebab stunting.

Umur pada recall_date memakai aturan validasi proyek yang sudah ada:
6 <= age_days/30,4375 <24. Jadi hari 183–730 diterima. Rumus survei WHO
2021 memakai 183 <= age_days <730. Selisih satu hari di batas atas dicatat;
patch ini tidak mengubah validasi engine/backend sepihak dan tidak mengklaim
kesetaraan persis dengan kriteria umur survei WHO. Peralihan MMF menyusu
9 bulan tetap terjadi pada hari 274. Hasil harian memakai umur saat recall,
bukan umur pada as_of.

Pada as_of di luar umur proyek, diet=null dan tidak ada alasan pola makan
aktif, walaupun masih ada catatan historis saat umur memenuhi syarat.
Riwayat di database tidak dihapus.

## Jendela dan pola

- Gunakan 14 tanggal kalender termasuk as_of, yaitu as_of-13 sampai as_of.
  Selaras query Foods pada backend terbaru. Catatan as_of-14 tidak dihitung.
- Catatan terkini untuk NO_RECENT_FOOD_RECALL mencakup tujuh tanggal,
  as_of-6 sampai as_of. Tepat tujuh hari sebelumnya sudah di luar jendela.
- Ambil maksimal tiga catatan terbaru di dalam jendela 14 tanggal. Dua
  kegagalan pada indikator yang sama menaikkan alasan itu ke yellow; dua
  catatan gagal yang tersedia sudah cukup, tidak harus menunggu catatan ketiga.
- Bila hanya satu kegagalan, info muncul hanya jika catatan terbaru gagal.
  Satu kegagalan lama dengan catatan terbaru membaik tidak menghasilkan info.
- Dua dari tiga catatan gagal tetap menjadi yellow walaupun hari terbaru
  membaik. Catatan keempat/lebih tua tidak memengaruhi pola.
- Catatan terbaru di luar tujuh tanggal tetapi masih dalam 14 tanggal dapat
  menampilkan pola serta info NO_RECENT_FOOD_RECALL bersamaan.
- Aturan pola/jendela/severity berasal dari kontrak proyek, bukan ambang
  diagnostik WHO. Semua pengurutan internal tidak mengubah urutan/data input.

## Penggabungan dan status API

evaluate_growth_and_diet mempertahankan per_measurement dan bukti pertumbuhan,
menambahkan diet serta alasan makan, dan mengambil severity tertinggi.
Satu hari buruk tidak menaikkan green; pola berulang bisa menjadi yellow;
red pertumbuhan/KPSP-history tidak diturunkan oleh hasil diet. Error tabel WHO
tetap diteruskan, tidak disamarkan sebagai aman.

Ini belum respons endpoint final karena next_kpsp dirakit pada integrasi
berikutnya. Tidak ada router yang ditambahkan; main masih hanya health.
KPSP visual tetap diblokir sampai gambar/rubrik dan review klinis lengkap.

## Bukti pengujian dan penerapan

35 tes baru lulus melalui unittest, termasuk satu integrasi pertumbuhan+diet
dengan tabel WHO asli yang lolos loader/checksum. Tanpa data WHO, 34 tes
berjalan dan satu integrasi dilewati. Cakupan: batas umur/frekuensi, jumlah
kelompok unik, susu opsional, EFF, pola setiap kode alasan, tanggal jendela,
duplikasi/future input, tidak ada mutasi serta severity/error pertumbuhan.

Lingkungan lokal Python 3.12/Pydantic 2.14.2. Pytest penuh tetap dicoba tetapi
gagal karena pytest belum tersedia. Angka unittest tidak menggantikan hasil
pytest seluruh proyek; perkiraan total setelah patch ini 225 kasus, termasuk
lima integrasi WHO yang bisa dilewati bila tabel belum ada.

```bash
cd engine
python -m unittest discover -s tests -p test_iycf.py -v
python -m pytest -q
```

Ekstrak ke akar repository setelah 07B. Bank WHO tidak dibundel; bila perlu,
unduh saat setup lewat python scripts/fetch_who_tables.py dan ulangi pytest.

Dokumen main yang diperiksa masih kontrak v0.4/status 07A walaupun kode 07B
sudah ada. Paket ini mempertahankan klarifikasi v0.5 yang sudah disetujui
pengguna pada 07B, lalu menambahkan catatan IYCF; tidak membatalkan aturan
>=16. Catatan backend/frontend disalin dari dokumen GitHub terbaru tanpa
perubahan. Jika ada update tim sesudah paket ini, merge docs secara hati-hati.
