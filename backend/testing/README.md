# Fake engine untuk pengujian lokal

Addon untuk backend Go yang sudah ada. Tidak mengganti engine asli, rumus medis, database atau konfigurasi .env. Menggunakan Python 3 standar tanpa pip/dependensi tambahan. Ekstrak ZIP ke akar repository agar berkas berada di backend/testing/.

## Jalankan

Terminal A, dari folder backend:

```powershell
python testing/fake_engine.py --testing-only
```

Terminal B, dari folder backend: hentikan Go lama dengan Ctrl+C, kemudian:

```powershell
$env:ENGINE_URL="http://127.0.0.1:18001/engine/v1"
go run ./cmd/server
```

Biarkan kedua terminal tetap berjalan. Variabel ENGINE_URL pada terminal B mengalahkan nilai .env untuk proses Go tersebut; .env asli tidak diubah. PostgreSQL dan DATABASE_URL tetap diperlukan. Pilih database uji/data fiktif: pengukuran, catatan makan dan hasil KPSP yang dikirim lewat Go tetap disimpan ke database yang dipilih.

Terminal C:

```powershell
Invoke-RestMethod http://127.0.0.1:18001/engine/v1/health | ConvertTo-Json -Depth 10
Invoke-RestMethod http://localhost:8080/api/v1/children | ConvertTo-Json -Depth 10
```

Gunakan UUID anak dari database yang sedang dipakai untuk GET /children/{id}/status, /growth?indicator=lhfa, dan /kpsp/next. POST pengukuran baru dapat menghasilkan 201 beserta status dummy, selama data valid dan tanggal belum dipakai. Data yang sudah tersimpan tidak perlu dikirim ulang; langsung GET status atau riwayat.

## Respons yang sengaja dummy

- Health 200, who_tables_loaded=false: memang tidak memuat data WHO. Header X-Fake-Engine: true menandai respons langsung dari fake engine.
- Growth: satu titik untuk setiap pengukuran, seluruh z-score null, klasifikasi kosong, alasan kosong; level tetap green untuk menguji jalur sukses backend. Label Aman pada Go/UI adalah fixture, BUKAN hasil skrining.
- Panjang dikembalikan tanpa koreksi medis. Tidak menguji rumus WHO atau ketepatan posisi ukur.
- Reference: semua array kosong; pita/garis WHO memang tidak tampil. Tidak membuat angka acuan WHO palsu.
- KPSP: jadwal tetap 9 bulan dan 10 pertanyaan berlabel DUMMY TEST. Skor yes_count hanya menghitung jawaban true; result selalu sesuai sebagai fixture, tanpa klasifikasi medis. Hasil ini bukan KPSP asli dan tidak boleh digunakan menilai perkembangan.
- Diet selalu null. Tidak ada penilaian IYCF atau deteksi risiko dini.

Fake engine hanya bind 127.0.0.1 di laptop yang sama dengan Go. Port 18001 dipilih supaya tidak bentrok dengan engine asli di 8001. Tidak ada fallback otomatis ke fake engine saat engine asli gagal.

## Kembali ke engine asli

Hentikan Go, lalu di terminal B:

```powershell
Remove-Item Env:ENGINE_URL
go run ./cmd/server
```

Go kembali membaca ENGINE_URL dari .env. Hentikan fake engine di terminal A dengan Ctrl+C. Jika memilih database uji melalui variabel DATABASE_URL, hapus override itu juga saat kembali ke konfigurasi asli.

## Tes

```powershell
python -m unittest discover -s testing -p "test_*.py"
```

Lima tes HTTP Python telah lulus: health, growth/riwayat kosong, reference kosong, questionnaire/score dummy, dan input/route invalid. Pengujian ini belum membuktikan alur lengkap Go-PostgreSQL pada laptop pengguna lulus dengan addon ini.
