# Pantau — laporan redesign

Desain sudah diterapkan pada 10 jenis halaman, navigasi, dialog konfirmasi, asisten, dan tampilan cetak. Urbanist dibundel lokal; tidak memakai CDN. Warna brand #23695b dan logo dipertahankan. Navigasi teks menggantikan ikon dekoratif, beranda disusun ulang, formulir lebih lapang, dan mobile memakai satu kolom serta navigasi bawah.

## Perbandingan yang terukur

Ukuran hasil build, sebelum kompresi; bukan skor kecepatan browser.

| Pemeriksaan | Sebelum | Sesudah |
|---|---:|---:|
| TypeScript + build | Lulus | Lulus |
| ESLint | Belum tersedia | Lulus, 0 warning |
| CSS | 11,97 kB | 36,96 kB |
| JavaScript utama | 145,75 kB | 153,60 kB |
| Modul grafik terpisah | 538,33 kB | 538,33 kB |
| Font WOFF2 lokal | — | 48,16 kB (4 bobot) |
| CSS gzip | 3,40 kB | 8,33 kB |
| JavaScript utama gzip | 53,18 kB | 56,19 kB |

CSS bertambah karena sistem desain dan motion kit. Grafik masih dimuat terpisah; peringatan chunk >500 kB sudah ada sebelum redesign.

## Yang terverifikasi

- `npm run lint`: lulus tanpa warning.
- `npm run build`: lulus pemeriksaan tipe dan bundling.
- 126 pemeriksaan preservasi sumber lulus: backend, engine, API, formulir, komponen skrining/grafik/asisten, dan tes asli tidak berubah. Script App berubah hanya pada judul beranda dan penghapusan import ikon yang tidak terpakai.
- Payload dan endpoint tidak diubah. Teks medis dari backend dan disclaimer tetap dipertahankan.
- 28 tes browser asli terdeteksi; ini bukan pernyataan bahwa 28 tes lulus.

## Batas verifikasi

Screenshot before dibebaskan oleh pengguna. Perekam skill gagal membuka Chrome; percobaan Edge tidak menyelesaikan koneksi lokal. Pengujian Playwright dibatasi 60 detik dan berhenti pada setup server/plugin sebelum tes berjalan. Screenshot after, hasil consistency/layout/perf berbasis browser, click-through seluruh tautan/form, dan verifikasi visual pada 1440/1024/820/768/390 belum tersedia. Responsivitas sudah diimplementasikan, tetapi belum dapat dinyatakan lolos inspeksi visual. Tidak ada skor atau screenshot yang direkayasa.

## Menjalankan

Dari folder frontend:

```sh
npm ci
npm run dev
npm run lint
npm run build
npm test
```

Isi VITE_API_URL sesuai `.env.example` dan jalankan layanan backend proyek untuk data sebenarnya. Pengujian Playwright memakai respons API tiruan yang sudah ada dalam proyek. Jika Chrome berada di lokasi lain, set CHROME_PATH. Source dan hasil build disertakan dalam ZIP; node_modules serta profil browser tidak disertakan.

## Cakupan rute

| Rute | Perubahan |
|---|---|
| / | Beranda dua bagian: panel pengantar, langkah penggunaan, kartu profil |
| /new | Identitas anak, jarak field dan tindakan yang konsisten |
| /guides | Filter dan daftar panduan dengan hierarki baca baru |
| /children/:id | Ringkasan status, metrik dan alasan terstruktur |
| /children/:id/measurement | Form pengukuran dan error field |
| /children/:id/growth | Bingkai grafik, kontrol dan legenda |
| /children/:id/history | Tabel riwayat dan dialog hapus |
| /children/:id/kpsp | Progress, pilihan jawaban dan navigasi langkah |
| /children/:id/food | Kelompok checkbox dan form catatan makan |
| /children/:id/report | Tampilan laporan dan aturan cetak A4 dipertahankan |

Tidak ada aset foto, harga, alamat, nama brand, atau fakta medis baru yang diasumsikan. Referensi digunakan untuk komposisi dan nuansa, bukan disalin.
