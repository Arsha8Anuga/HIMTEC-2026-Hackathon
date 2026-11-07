# Patch 07A — persiapan core KPSP, belum fitur KPSP lengkap

Basis repository: `02aeba3e68b4ee63c4e4ac0e92fd0a6055b1a55a`.
Paket melanjutkan Patch 06 tanpa mengubah backend/frontend atau kontrak API.

## Yang tersedia

- `app/schemas/kpsp.py`: request skor mengikuti body client Go yang sudah
  ada: questionnaire_age_months dan answers. Harus tepat 10 jawaban, item_no
  1–10 masing-masing sekali, boolean ketat, umur sesuai jadwal kontrak dan
  tidak menerima field tambahan.
- `app/core/kpsp.py`: skor yes_count dan result tanpa memutasi input.
  Ambang dan jadwal dibaca dari `data/kpsp/rules.json`; ambang skor cocok
  dengan Lampiran 2 sumber Kemenkes yang ditautkan di JSON.
- `round_kpsp_months` adalah fungsi primitif atas bulan penuh dan sisa hari
  yang SUDAH dihitung oleh pemanggil; literal kontrak membulatkan bila >16.
- `select_kpsp_age` memilih umur jadwal terdekat yang tidak lebih tua; hasil
  None bila di bawah umur pertama, dan menolak umur di luar cakupan proyek.
- `load_kpsp_bank` memerlukan atribusi dan seluruh 14 kelompok umur kontrak,
  10 butir per kelompok, nomor unik/lengkap dan aspek sesuai enum. Bank
  hilang/tidak lengkap/rusak menghasilkan error, bukan pertanyaan buatan.

## Yang belum tersedia — tidak boleh dianggap selesai

- **Tidak ada bank pertanyaan klinis dalam paket ini.** `questionnaires.json`
  belum dibuat. Teks TEST FORMAT SENTINEL hanya ada di fixture tes, bukan
  isi klinis atau data aplikasi. Validasi loader memeriksa struktur saja,
  bukan membuktikan keaslian, izin penggunaan, atau ketepatan isi klinis.
- Seluruh formulir membutuhkan pedoman SDIDTK yang dipilih/disediakan tim
  untuk transkripsi dan pemeriksaan nomor, aspek, instruksi serta gambar.
  Instruksi yang bergantung pada gambar tidak boleh hilang saat konversi.
- Ada selisih batas pembulatan: kontrak menyebut lebih dari 16 hari; sumber
  resmi juga menulis >16 tetapi contoh tepat 16 dibulatkan ke bulan berikutnya.
  Sebelum diintegrasikan, pemilik kontrak harus memutuskan >16 atau >=16.
  Tes fungsi literal kontrak bukan pengesahan klinis atas konflik itu.
- Penghitungan komponen umur dari birth_date/as_of, aturan next_kpsp/due,
  evaluasi ulang meragukan dan penanganan umur di luar jadwal belum dikunci.
  Jangan mengganti umur KPSP dengan umur tampilan hari / 30,4375 tanpa dasar.
- Tidak ada router/endpoint KPSP yang didaftarkan. Main tetap tidak memasang
  /growth/evaluate, /kpsp/score, /kpsp/questionnaire atau /reference.

Contoh format bank INTERNAL yang diperlukan: root berisi source (title, url,
verified_on) dan questionnaires. Setiap kuesioner memiliki
questionnaire_age_months serta items (item_no, aspect, question).
Ini bukan penambahan field API; metadata hanya untuk data lokal.

## Pengujian

19 tes baru lulus melalui unittest di Python 3.12/Pydantic 2.14.2: seluruh
11 kemungkinan skor, batas umur primitif, kelengkapan jawaban, tipe ketat,
ketiadaan mutasi, dan penolakan bank rusak/tidak lengkap. Tes loader hanya
menggunakan teks sintetis yang jelas diberi label, bukan bank KPSP resmi.

Pytest penuh belum dapat dijalankan di lingkungan ini (pytest belum terpasang).
Jangan menandai Patch 07 lengkap atau seluruh suite pytest lulus berdasarkan
hasil ini. Paket menambah 19 tes yang juga dapat dikoleksi pytest; perkiraan
total setelah Patch 06 adalah 170 kasus, dengan 4 tes WHO yang dapat dilewati
bila berkas resmi belum tersedia. Hasil nyata tetap perlu dicatat.

Dari folder engine dengan dependensi requirements yang terpasang:

```bash
python -m unittest discover -s tests -p test_kpsp.py -v
python -m pytest -q
```

Ekstrak paket dari akar repo setelah Patch 06. Dokumen bersama berasal dari
repo terbaru yang diperiksa sebelum pengemasan. Penanda konflik CHANGELOG
diselesaikan dengan mempertahankan seluruh entri unik dari kedua sisi;
bagian backend/frontend HANDOFF dipertahankan. Jika tim memperbarui docs
lagi, merge catatan engine dan perbaikan konflik tanpa menimpa catatan baru.
