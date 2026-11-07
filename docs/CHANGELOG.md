# Changelog

Entri terbaru di atas. Catat setiap perubahan yang memengaruhi orang lain: kontrak, PRD, API,
skema database, port, variabel lingkungan, atau aturan kerja. Perubahan kecil di dalam folder
sendiri cukup ditulis di pesan commit.

Format satu baris:

```
- HH:MM · <area atau versi> · <siapa> · <apa yang berubah> · [MERUSAK] · <siapa yang harus menyesuaikan>
```

Tandai `[MERUSAK]` bila mengganti nama, mengubah tipe, atau menghapus field/endpoint.

## 2026-11-07

- 11:53 · docs/backend · tim backend · gabungkan CHANGELOG/HANDOFF dari main b4958d3 dengan seluruh patch backend dan bukti uji pengguna: daftar/tambah/detail anak dan simpan/baca pengukuran berhasil pada PostgreSQL lokal; parent_id terisi; evaluasi masih 503 dan health engine IP yang diuji tidak terhubung; patch redirect root sudah dibuat/dites tetapi penerapan di laptop belum dikonfirmasi · — · tim: selesaikan koneksi engine dan verifikasi paket root terbaru

- 11:48 · backend · tim backend · atas permintaan pengguna, GET/HEAD /api/v1 dan /api/v1/ diarahkan 307 ke /api/v1/children; unknown path tetap JSON 404, POST root tidak dialihkan; tes routing/race/vet dan kompilasi Windows lulus; gangguan koneksi engine tetap terpisah dari routing/data PostgreSQL · — · frontend: gunakan route data langsung; alamat dasar dapat dibuka melalui browser

- 11:35 · backend · tim backend · sesuaikan PRD users/children.parent_id melalui migrasi tambahan 003; backfill anak legacy ke orang tua demo tanpa menghapus riwayat atau menimpa pemilik yang sudah ada; FK/indeks dan pemeriksaan akun parent aktif; konversi food_groups text[] PRD ke JSONB mempertahankan nilai; startup menerapkan 001+003 secara transaksional dengan advisory lock, seed 002 tetap opsional dan mengikuti pemilik · [MERUSAK] skema SQL langsung; JSON API tetap · backend: gunakan seluruh patch bersama migrasi; SQL langsung harus menyertakan parent_id; API JSON tetap

- 11:35 · backend · tim backend · seluruh query anak/pengukuran/KPSP/catatan makan/hapus dibatasi pemilik; umur recall mengikuti hari/30,4375 pada recall_date dan KPSP menolak tanggal sebelum lahir; sertakan perbaikan error engine versus database, pesan data sudah tersimpan, client respons invalid, grafik kosong dan validasi respons KPSP dari patch sebelumnya; port 8080 diperiksa sebelum akses DB dan pesan siap dicetak setelah bind/migrasi berhasil · — · frontend: tampilkan pesan error dan periksa riwayat sebelum POST ulang; engine: endpoint HTTP tetap mengikuti kontrak v0.4

- 11:35 · backend · tim backend · go test -race lulus termasuk lima tes SQL integrasi melalui lib/pq ke PGlite/PostgreSQL WASM (bukan PostgreSQL native); migrasi fresh/legacy, seed, isolasi parent/admin/nonaktif, preservasi array PRD dan rollback lulus; go vet, kompilasi Linux/Windows amd64 dengan buildvcs=false, smoke HTTP dan konflik port lulus; go-sqlmock hanya dependensi tes · — · tim: ulangi tes pada PostgreSQL native dan laptop Windows demo; engine Python nyata/hasil medis belum diuji

- 11:35 · docs/backend · tim backend · perbarui README/PATCH_NOTES backend, changelog dan handoff; gabungkan duplikasi bagian backend menjadi satu status terkini sambil mempertahankan bagian engine/frontend; paket ZIP berisi backend lengkap + docs/CHANGELOG.md + docs/HANDOFF.md; tidak ada push GitHub · — · semua: gabungkan perubahan dokumen yang lebih baru sebelum menerapkan ZIP

- 11:13 · docs · Zena · README.md kembali ke akar repo; tautan di README, kalimat di AGENTS.md, dan pohon folder PRD disesuaikan · — · semua: buka README dari akar repo

- 11:08 · PRD · Zena · menambah bagian "Skema database": lima tabel (`users`, `children`, `measurements`, `kpsp_results`, `food_recalls`) dengan DDL acuan, sudah diuji di PostgreSQL 16; kontrak API tidak berubah · — · backend: `migrations/001_init.sql` saat ini belum punya tabel `users` dan kolom `children.parent_id`; tambahkan, seed satu orang tua demo, dan filter semua query anak dengan ID-nya (PostgreSQL < 13 butuh ekstensi `pgcrypto` untuk `gen_random_uuid()`)

- 11:06 · engine · engine (hotfix ZIP 04A) · melengkapi validasi tanggal KPSP/recall, umur recall menurut tanggalnya dan keunikan riwayat; koreksi posisi memakai desimal untuk grid WHO; tes health diisolasi dari data lokal dan tes regresi ditambahkan. 22 pemeriksaan manual serta kompilasi lulus; 5 checksum WHO cocok dan 13.366 baris termuat. Pytest hotfix belum terverifikasi (pytest/dependensi tidak tersedia di lingkungan ini); angka 91 lulus adalah hasil Patch 04 sebelumnya. Tidak mengubah kontrak/endpoint/dependensi; data WHO tidak dibundel · — · engine/tim: jalankan pytest dengan requirements repository sebelum menandai hotfix lulus dan melanjutkan Patch 05; lihat engine/debug/HOTFIX_04A.md

- 11:05 · PRD · Zena · peta jalan login setelah MVP: OTP ke pemilik akun, peran orang tua dan admin; admin mengelola akun tetapi tidak bisa melihat kode maupun data kesehatan anak; MVP tetap tanpa login · — · backend: lihat persiapan tabel `users` di entri 11:08

- 11:04 · docs/backend · tim backend · dibuat arsip backend-docs-update.zip berdasarkan 852ac74; berisi catatan backend sampai patch kompatibilitas awal dan konsolidasi handoff; arsip tersebut belum masuk main saat pembacaan af4193a · — · backend: dokumentasi pada paket baru ini menggantikan catatan backend versi arsip tersebut

- 11:02 · backend · tim backend · dibuat backend-engine-compatible.zip berdasarkan 852ac74; go test, race detector, vet dan kompilasi Windows lulus pada lingkungan Linux dengan SQL mock/HTTP test server; paket awal belum mencakup users/parent_id dari PRD terbaru · — · backend: perbaikan awal sudah digabungkan ke paket terbaru ini

- 10:59 · backend · tim backend · patch awal memisahkan error engine/DB, menjelaskan POST sudah tersimpan jika evaluasi gagal, memperbaiki titik grafik kosong serta validasi response KPSP; API/port tetap · — · frontend: periksa riwayat sebelum POST ulang; engine: evaluasi/reference/KPSP masih diperlukan

- 10:47 · engine · engine (patch ZIP 04) · menambah fungsi murni z-score LMS, restricted LMS (khusus indikator berbasis berat), invers LMS untuk garis SD, koreksi posisi berdasar 731 hari, dan interpolasi linear 0,1 cm sebagai utilitas terpisah; 91 tes pytest lulus (48 lama + 43 baru), termasuk kasus resmi WHO Anthro. Tidak menambah endpoint/field/enum dan data WHO tidak dibundel · — · backend: endpoint evaluasi medis belum tersedia; pemilik kontrak: tetapkan kebijakan presisi 0,1 cm, batas umur, dan penanganan posisi berdiri di bawah 9 bulan sebelum integrasi

- 10:37 · docs · engine (hotfix ZIP dokumentasi patch 03) · merge ulang `docs/CHANGELOG.md` dan `docs/HANDOFF.md` dari versi terbaru GitHub; mempertahankan semua catatan backend pukul 09:39 dan 10:03, isi serah terima backend, dan matriks integrasi; tidak ada perubahan kode engine · — · semua: gunakan dokumentasi hasil merge; hindari menimpa dokumen terbaru dengan dokumen dari ZIP patch lama

- 10:30 · engine · engine (patch ZIP 03) · loader WHO LMS offline (5 berkas resmi dari WHO Anthro, sumber/commit + checksum Git blob diverifikasi), skrip unduh saat setup, status `/health` berbasis validitas seluruh tabel, dokumentasi sumber dan 48 tes pytest lulus; tabel belum dibundel karena sandbox tidak dapat mengunduhnya · — · backend: jangan gunakan endpoint evaluasi karena perhitungan medis belum diimplementasikan; pemilik kontrak: selaraskan batas umur 1856 hari dengan tabel WHO 0–1826 hari sebelum implementasi evaluasi

- 10:13 · engine · engine (patch ZIP 02) · menambah fondasi FastAPI (`/engine/v1/health`), skema Pydantic input `/growth/evaluate` sesuai kontrak v0.4, amplop error validasi, 26 tes pytest lulus; `/health` melaporkan `who_tables_loaded=false` sampai tabel WHO resmi dimuat · — · backend: kirim `food_recalls` sebagai daftar (boleh kosong) sesuai kontrak v0.4; jangan anggap engine pertumbuhan sudah siap

- 10:03 · backend · tim backend · hasil uji di laptop Windows: kendala dependensi `github.com/lib/pq`/`go.sum` telah teratasi setelah penataan modul (`go mod tidy`); startup sempat terhenti karena `DATABASE_URL` belum terisi, lalu layanan berhasil menerima HTTP di `localhost:8080`; akses `GET /api/v1/` mengembalikan `NOT_FOUND` karena bukan route terdaftar (perilaku yang diharapkan). Belum ada bukti uji CRUD maupun evaluasi Python end-to-end · — · backend: lanjutkan tes `GET/POST /children` serta koneksi engine; frontend: gunakan route lengkap di bawah `/api/v1`

- 09:39 · backend · tim backend · implementasi Go API + migrasi PostgreSQL + client HTTP Python, pesan Indonesia dan seed identitas fiktif; panduan resmi dan verifikasi bentuk respons engine masih dibutuhkan · — · Zena: konfirmasi score/reference dan isi panduan; frontend: integrasi endpoint yang sudah tersedia

- 09:25 · docs · Zena · semua dokumen dipindah ke `docs/` (README, CONTRACT, PRD, CHANGELOG, HANDOFF); hanya AGENTS.md dan CLAUDE.md di akar · — · semua: perbarui rujukan path

- 08:50 · kontrak v0.4 + PRD v0.2 · Zena · fitur Catatan Makan Kemarin: entitas `FoodRecall`, `POST/GET /children/{id}/food-recalls`, field `diet` di `/status`, `food_recalls` di `/growth/evaluate`, kode alasan `NO_ANIMAL_SOURCE_FOOD`, `LOW_DIET_DIVERSITY`, `LOW_MEAL_FREQUENCY`, `NO_RECENT_FOOD_RECALL` · — · backend: tabel + endpoint; frontend: layar catatan makan; engine: indikator IYCF

- 08:37 · docs · Zena · menambah AGENTS.md, CLAUDE.md, CHANGELOG.md, HANDOFF.md · — · semua: baca AGENTS.md

- 08:31 · kontrak v0.3 · Zena · menambah `GET /api/v1/guides` untuk kartu GiziCerdas dan Stimulasi; PRD v0.1 ditulis · — · backend: siapkan `guides.id.json`; frontend: layar Panduan

- 08:29 · kontrak v0.2 · Zena · jaringan demo: engine di laptop Zena, Go membaca `ENGINE_URL` · — · backend

- 08:10 · kontrak v0.1 · Zena · draf awal kontrak · — · semua
