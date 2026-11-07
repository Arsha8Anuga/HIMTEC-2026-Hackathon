# Hotfix 04A — validasi riwayat dan grid koreksi posisi

Tanggal: 7 November 2026. Terapkan setelah Patch 04.
Basis GitHub: `852ac74a75e781b32f56ac08aa233ebfe1acd4bf`.

## Perubahan

- Riwayat KPSP harus berada di antara tanggal lahir dan `as_of`, inklusif.
- Catatan makan tidak boleh sebelum lahir atau setelah `as_of`; umur pada
  tanggal recall harus 6 sampai kurang dari 24 bulan. Bulan mengikuti kontrak
  v0.4: hari / 30,4375, tanpa pembulatan tampilan.
- ID pengukuran, tanggal pengukuran, dan tanggal catatan makan tidak boleh
  duplikat. Urutan riwayat tidak diubah dan data tidak dibuang diam-diam.
- Koreksi posisi memakai operasi desimal agar input 0,1 cm tetap cocok dengan
  lookup WHO. Presisi input yang lebih tinggi tidak dipotong atau dibulatkan.
- Tes health mengisolasi kedua kemungkinan ketersediaan tabel dengan
  `monkeypatch`, sehingga tidak bergantung pada isi `data/who/` laptop.

Tidak ada perubahan kontrak, dependensi, endpoint, klasifikasi, maupun batas
umur 1856 hari pada skema pengukuran. `/growth/evaluate` tetap belum aktif.

## Bukti dan batas pengujian

- 22 pemeriksaan manual lulus dengan Python 3.12 dan Pydantic 2.14.2.
  Cakupan: tanggal riwayat, batas umur recall (182/183/730/731 hari),
  duplikasi, urutan input, koreksi dengan lookup WHO asli, dan presisi input.
- Di dalam pemeriksaan itu, seluruh 1.802 kombinasi koreksi posisi pada grid
  input 40,0–130,0 cm lolos kesetaraan desimal (dua cabang koreksi).
- Lima berkas WHO pada commit yang dipin lolos checksum; loader membaca
  13.366 baris. Data WHO dipakai untuk pengecekan lokal dan tidak dibundel ZIP.
- Kompilasi seluruh modul aplikasi dan tes berhasil.
- Kasus regresi pytest ditambahkan, tetapi **suite pytest hotfix belum lulus
  terverifikasi**. `python -m pytest -q` gagal dengan `No module named pytest`.
  Pemasangan dependensi dari `requirements.txt` juga gagal di lingkungan ini
  (`No matching distribution found`), termasuk percobaan tanpa pin versi.
  Ini tidak membuktikan versi paket di repository tidak tersedia secara umum.
- Pydantic pemeriksaan manual (2.14.2) berbeda dari pin repository (2.13.5).
  Angka 91 tes lulus merupakan laporan Patch 04 sebelumnya, bukan hasil hotfix.
- Tes HTTP/TestClient, termasuk tes health yang diubah, belum dieksekusi pada
  lingkungan ini karena FastAPI/httpx/pytest belum tersedia.

## Penerapan dan pemeriksaan wajib

ZIP hanya berisi berkas yang berubah. Ekstrak dari akar repository setelah
Patch 04; jangan menaruh folder `engine/` di dalam `engine/` lagi.

`docs/HANDOFF.md` dan `docs/CHANGELOG.md` telah dibandingkan dengan GitHub
sebelum dikemas. Jika dokumen tim berubah setelah basis di atas, gabungkan
hanya bagian engine/entri hotfix, jangan menimpa catatan terbaru anggota lain.
Duplikasi bagian backend yang sudah ada di basis tetap dipertahankan.

Dari akar repository, dengan lingkungan virtual aktif:

```bash
cd engine
python -m pip install -r requirements.txt
python -m pytest -q
python scripts/fetch_who_tables.py
python -m pytest -q
```

Jalankan suite sebelum dan sesudah pemasangan tabel WHO; tes health harus
tetap lulus pada kedua kondisi. Unduhan hanya diperlukan saat setup, bukan
saat aplikasi berjalan. Bila tabel sudah terpasang, langsung jalankan suite.

Hotfix belum boleh ditandai tervalidasi penuh sebelum hasil pytest dicatat.
Keputusan kontrak mengenai umur 1856 vs 1826 hari, presisi WFL/WFH, dan posisi
berdiri sebelum 9 bulan tetap terbuka untuk pekerjaan Patch 05.
