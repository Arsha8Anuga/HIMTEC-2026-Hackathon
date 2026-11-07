# Patch 001 — catatan pengiriman

- Menambah aplikasi Vue responsif dan koneksi API Go mode demo.
- Verifikasi: vue-tsc dan build Vite lulus. Tidak menjalankan backend/DB atau membuktikan alur end-to-end.
- Browser pemeriksaan tidak dapat menjangkau server localhost (timeout); tampilan 360/768/1440 dan cetak masih perlu verifikasi pada laptop tim.
- Runtime tidak memakai CDN. Dependensi perlu dipasang saat setup.
- KPSP/reference/panduan mengikuti kesiapan backend/engine, tanpa hasil kesehatan pengganti.
- Autentikasi OTP belum bagian patch ini.
- Rollback: pulihkan cadangan frontend sebelum ekstraksi; patch tidak mengubah database.
