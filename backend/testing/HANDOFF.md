# Handoff — addon fake engine

7 November 2026. Scope: pengujian alur backend dengan fixture HTTP lokal, atas permintaan pengguna. Bukan perubahan engine medis asli.

Selesai: server Python standar pada 127.0.0.1:18001, amplop data/error yang dipakai Go, health, growth/evaluate, reference, questionnaire dan score dummy; lima tes HTTP lulus; README memuat startup, batas fixture dan cara kembali ke engine asli.

Backend yang sudah ada memakai override ENGINE_URL tanpa perubahan kode Go. PostgreSQL tetap diperlukan; data yang dikirim ke Go tetap tersimpan. Pakai database uji dan data fiktif. Seluruh label Aman/sesuai dan jadwal KPSP pada mode ini adalah fixture. Z-score null, reference kosong, diet null.

Berikutnya: jalankan kedua proses sesuai README, cek health fake dan status anak pada Go, lalu uji input tanggal baru. Jangan mengulang pengukuran yang sudah tersimpan. Catat respons nyata; integrasi laptop belum diverifikasi. Kembalikan ENGINE_URL ke .env setelah pengujian. Gabungkan catatan addon ini ke bagian backend pada docs/HANDOFF.md terbaru bila akan di-commit; pertahankan catatan engine/frontend.
