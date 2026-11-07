# Patch 07B — umur, jadwal KPSP dan transkripsi 140 butir

Basis repository: `1a0fe1bacb4d174e0b900931ca7feacaf4c24862`, setelah 07A.
Sumber adalah Markdown yang diunggah pengguna, bukan isi dari ingatan AI.

## Sumber dan perubahan

- `BUKU-PEDOMAN-SDIDTK-revisi-23082022.md`, SHA256:
  `caab23502a0674b296e799699a170f7ef6ff6d29c3dad685f44383b7692d8443`.
- Aturan umur dibaca dari halaman tercetak 117–119; formulir dari 122–141.
- Sesuai keputusan eksplisit pengguna, sisa **>=16 hari** dibulatkan ke atas:
  8 bulan 15 hari memilih formulir 6 bulan; 8 bulan 16 hari memilih 9 bulan.
  Kontrak dinaikkan ke v0.5 draf untuk mencatat klarifikasi tersebut.
- Perhitungan komponen umur mengikuti pengurangan tahun/bulan/hari pedoman:
  bila hari negatif, pinjam 30 hari dan kurangi satu bulan. Tidak memakai
  hari/30,4375 atau panjang riil bulan sebelumnya. Contoh pedoman
  2018-09-25 ke 2020-04-15 menghasilkan 18 bulan 20 hari.
- Koreksi prematur tetap di luar cakupan proyek sesuai kontrak/PRD.

## Core jadwal

`next_kpsp(request)` menerima request tervalidasi dan tidak menyimpan status.

- Di bawah 3 bulan bulat: umur formulir berikutnya 3, due=false.
- Belum mengisi formulir yang sesuai umur: due=true, gunakan umur jadwal
  paling dekat yang tidak lebih tua dari umur bulat anak.
- Formulir sesuai umur sudah menghasilkan sesuai: pilih umur jadwal berikutnya,
  due=false sampai umur tersebut tercapai. Pada umur terakhir, tetap 60/false.
- Hasil terakhir meragukan: ulangi formulir yang sama setelah >=14 hari,
  termasuk saat anak telah melewati batas umur formulir berikutnya. Ini
  mengikuti evaluasi intervensi pada halaman 119, bukan langsung mengganti
  formulir yang gagal dengan yang lebih tua.
- Hasil terakhir penyimpangan: due=false; pedoman mengarahkan rujukan, bukan
  penjadwalan ulang otomatis mandiri. Kode KPSP_DEVIATION tetap ditangani oleh
  early warning; due=false bukan penghapusan hasil tersebut.
- Riwayat terbaru dipilih dari tanggal, umur formulir terbesar memecahkan
  tanggal yang sama, konsisten dengan Patch 06. Input tidak dimutasi.
- Umur bulat di luar 0–60 ditolak; hubungan dengan batas 1856 hari pada
  kontrak pengukuran tetap isu integrasi terbuka, tidak diperluas diam-diam.

Jadwal 14 formulir (3–60) tetap mengikuti proyek. Pedoman menyebut jadwal
pemeriksaan rutin yang lebih terbatas; tersedianya 14 formulir tidak berarti
semuanya diklaim sebagai jadwal kunjungan rutin resmi baru.

## Bank teks dan gambar yang belum tersedia

`data/kpsp/questionnaires.json` berisi 14 kelompok umur x10 butir dengan nomor,
aspek, dan teks dari sumber pengguna. Umur 66/72 tidak masuk kontrak proyek.
Baris terbungkus digabung, label aspek dipetakan ke enum, pagar Markdown dan
header/footer halaman dihapus; isi instruksi tidak dibuat ulang atau disingkat.
Peralatan dan navigasi halaman dicatat pada metadata sumber, bukan API.

Script `scripts/import_kpsp_markdown.py` mereproduksi transkripsi dari sumber
MD. Script menolak nomor, umur atau label aspek yang hilang/ambigu. Metadata
mencatat hash sumber dan kandidat butir yang merujuk gambar/contoh. Deteksi
kandidat bukan pengganti pemeriksaan manual terhadap seluruh halaman.

**Markdown tidak memuat gambar aslinya.** Teks seperti "gambar di bawah" dan
rubrik gambar Ya/Tidak tetap dipertahankan, bukan diganti gambar buatan.
Karena itu:

- `load_kpsp_bank()` secara default menolak bank ini sebagai belum siap tayang.
- `load_kpsp_bank(for_review=True)` hanya untuk peninjauan transkripsi; jangan
  memakainya untuk melewati penjagaan pada endpoint atau UI produksi.
- Loader memerlukan visual_assets_status dan clinical_review_status bernilai
  verified sebelum pemuatan normal; pengisian metadata harus dilakukan sesudah
  gambar dan transkripsi diverifikasi, bukan sekadar mengubah flag agar lolos.
  Metadata adalah catatan audit, bukan bukti otomatis bahwa verifikasi benar.
- Untuk menyelesaikan penayangan, diperlukan PDF/gambar halaman tercetak
  122–141 berikut pemeriksaan kecocokan instruksi/aspek. Kontrak respons yang
  hanya berisi question/aspect/item_no belum mengatur aset gambar; pemilik
  kontrak perlu menetapkan cara penyajiannya sebelum router questionnaire
  diaktifkan. Tidak menambah field gambar secara sepihak.

## Batas integrasi dan pengujian

Tidak ada endpoint yang diaktifkan dalam patch ini. Main tetap hanya health;
scoring/jadwal tersedia sebagai core, bank teks untuk review. Jangan menyebut
KPSP visual lengkap atau integrasi frontend/Go sudah lulus.

39 tes KPSP lulus melalui unittest: 19 tes 07A diperbarui +20 tes baru. Cakupan
termasuk contoh umur sumber, >=16, peminjaman 30 hari, umur terminal, due,
riwayat acak tanpa mutasi, kelengkapan 140 butir, atribusi, parser, serta
penolakan bank yang belum memiliki verifikasi gambar/klinis.

Lingkungan lokal Python 3.12/Pydantic 2.14.2. Pytest penuh dicoba tetapi belum
tersedia (`No module named pytest`). Ini bukan hasil pytest seluruh proyek.
Perkiraan suite menjadi 190 kasus setelah 07B, dengan 4 tes WHO yang dapat
dilewati jika datanya tidak tersedia; catat hasil nyata dari laptop tim.

```bash
cd engine
python -m unittest discover -s tests -p 'test_kpsp*.py' -v
python -m pytest -q
```

Ekstrak ZIP ke akar repository setelah 07A. Dokumen bersama dicek dari
GitHub terbaru sebelum dikemas; jika tim telah mengubah docs lagi, merge
perubahan engine dan kontrak v0.5 tanpa menimpa catatan backend/frontend.
