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

- 16:45 · kontrak v0.6 (draf) + engine + backend · Zena · batas umur `measured_at` 1856 → 1826 hari agar sama dengan tabel WHO harian (1856 = ⌊61 × 30,4375⌋ dari konvensi bulan penuh SDIDTK hlm. 91; alasannya di "Penegasan v0.6"). Go menolak > 1826 dengan VALIDATION_ERROR dan membatasi garis acuan ke 1826; engine menolak dengan 422 (sebelumnya 503). `GET /children` ditetapkan tanpa ringkasan; `otp_dummy` dan `/auth/*` dinyatakan ekstensi pengujian di luar kontrak; garis acuan `wfl_wfh` tetap isu terbuka · — · backend: tinjau perubahan Go di ZIP; frontend: tidak ada perubahan; semua: Go demo wajib mode `demo`

- 16:15 · frontend · Zena (audit, atas nama tim frontend) · favicon kosong agar tidak ada 404 di setiap pemuatan; tautan "Buka laporan" disembunyikan di halaman laporan itu sendiri · — · frontend: tinjau perubahan di ZIP audit

- 16:15 · backend · Zena (audit, atas nama tim backend) · jendela 14 hari `GET /food-recalls` dan riwayat ke engine memakai tanggal Go (sama dengan `as_of`), bukan `CURRENT_DATE` PostgreSQL; bila zona waktu DB berbeda (mis. UTC di Docker), catatan makan hari ini tersimpan tetapi hilang dari riwayat dan dari `diet` antara 00.00–07.00 WIB. Fixture sqlmock disesuaikan · — · backend: tinjau perubahan di ZIP audit

- 16:10 · backend · Zena (audit, atas nama tim backend) · validasi pengukuran menolak `length_height_cm`/`head_circumference_cm` lebih dari 1 desimal sesuai kontrak; sebelumnya 75,25 cm tersimpan lalu setiap evaluasi anak itu 422 sampai baris dihapus · — · backend: tinjau perubahan di ZIP audit

- 16:10 · docs · Zena · README: frontend sudah ada (perintah npm dikembalikan), status endpoint engine diperbarui, Compose dinyatakan belum ada; HANDOFF engine diperbarui dengan bukti audit dan empat keputusan kontrak yang menunggu · — · semua: baca bagian "Keputusan kontrak" di HANDOFF

- 14:29 · engine · Zena (Patch 09, entri susulan) · endpoint `POST /growth/evaluate`, `POST /kpsp/score`, `GET /reference` (wfa, lhfa, hcfa) aktif; `GET /kpsp/questionnaire` tetap 404 dan `reference` wfl_wfh 503 · — · backend/frontend: kurva wfl_wfh dan KPSP next belum bisa dipakai; lihat engine/debug/PATCH_09.md

- 14:14 · docs/backend · hasil uji pengguna · tambahkan bukti sesi OTP akun existing, GET children awal kosong, POST/GET anak akun login, POST logout logged_out:true dan penolakan token lama UNAUTHORIZED; pertahankan seluruh catatan engine ZIP 08 dan frontend; tidak menganggap data lintas akun/engine asli sudah teruji · — · backend: lanjut login setelah logout dan baca anak yang sama, lalu isolasi dua akun

- 14:07 · backend · hasil uji pengguna Windows/PostgreSQL lokal · POST /children dengan Authorization berhasil membuat Anak Mutia Uji; GET /children dengan sesi yang sama menampilkan objek ber-ID sama dan error:null; GET sebelumnya menghasilkan [] pada akun yang belum memiliki anak · — · tim: data baru terkait akun sesi; hasil ini belum membuktikan penolakan akses akun lain

- 14:01 · docs/engine · engine (hotfix dokumentasi ZIP 08) · gabungkan ulang CHANGELOG/HANDOFF dari main terbaru: pertahankan seluruh catatan backend sampai 13:45 termasuk OTP dan bukti uji pengguna, pulihkan status Engine 07B/08; tanpa perubahan kode atau push GitHub · — · semua: terapkan hotfix docs setelah ZIP 08 agar catatan backend terbaru tidak tertimpa

- 14:01 · backend · paket penyelarasan basis 6551237 · tambah cmd/check-engine dan probe read-only health/OpenAPI maksimal 3 detik, kenali fake/route hilang/OpenAPI unknown; error 503 membedakan endpoint belum tersedia dari gangguan koneksi sambil mempertahankan pesan data tersimpan; loader .env bersama CLI/server; dokumentasi kontrak v0.5 draf, OTP/401/429, PRD dan status 07B/layanan diselaraskan · — · engine/frontend: komponen asli tidak ditambahkan oleh patch backend; review pemilik kontrak tetap diperlukan

- 14:01 · backend · validasi paket penyelarasan · Go unit/race, vet, kompilasi server dan check-engine Windows, smoke CLI fake dan 5 tes fake Python lulus; SQL suite tidak dijalankan ulang tanpa BACKEND_TEST_DATABASE_URL; tidak ada perubahan kode engine/frontend/migrasi dalam patch ini · — · tim: hasil paket pengembangan terpisah dari bukti penerapan laptop dan validasi medis

- 13:50 · engine · engine (ZIP 08) · core MDD/MMF/EFF dari referensi WHO/UNICEF 2021, jendela 14 tanggal selaras Go, pola >=2 kegagalan dari maksimal 3 catatan terbaru, recency 7 tanggal dan penggabungan severity/evidence pertumbuhan. 35 tes unittest lulus termasuk WHO asli+diet; pytest penuh belum tersedia lokal. Selisih umur hari 730 proyek vs WHO dicatat. Klarifikasi kontrak v0.5/riwayat 07B digabung kembali dari paket yang telah diberikan, catatan tim tetap dipertahankan · — · tim: jalankan pytest; backend/frontend: endpoint evaluasi belum aktif, KPSP gambar masih menunggu; lihat engine/debug/PATCH_08.md

- 13:45 · docs/backend · tim backend · perbarui file lampiran dengan seluruh pekerjaan backend sampai hasil verifikasi OTP dan GET /auth/me pengguna; bedakan implementasi, tes pengembangan dan bukti laptop; catatan engine/frontend serta riwayat sebelumnya dipertahankan · — · tim: lanjut uji sesi, isolasi pemilik dan integrasi engine/frontend nyata; tidak ada push GitHub pada pembaruan ini

- 13:34 · backend · hasil uji pengguna · Go berjalan dalam AUTH_MODE=otp_dummy pada loopback; POST /auth/register menghasilkan challenge dan OTP terminal; pengguna kemudian berhasil POST /auth/verify serta GET /auth/me dengan bearer token, menampilkan akun uji role parent dan error:null; kode OTP/token tidak dicatat dalam dokumen · — · backend: lanjut uji daftar/tambah anak dengan sesi, login ulang, logout dan akses lintas akun; hasilnya belum dilaporkan

- 13:31 · backend · tim backend · paket OTP dummy berbasis 1a0fe1b menambah register/login/verify/me/logout, migrasi 004 (otp_codes/auth_sessions/audit_logs dan indeks email lower), HMAC OTP sekali pakai 5 menit/5 percobaan, resend 60 detik/5 per jam/email, sesi hashed 24 jam dan audit tanpa kode/token; context pemilik per request berasal dari parent aktif; default demo lama tetap tersedia · [MERUSAK] mode OTP memerlukan Authorization Bearer dan menambah error 401/429; JSON medis tetap · frontend: kirim token; akun baru tidak otomatis mendapat anak demo lama

- 13:31 · backend · tim backend · unit/race dan SQL auth via PGlite/PostgreSQL WASM lulus untuk pendaftaran/login/sesi/logout, expiry, replay, batas percobaan/request, restart, verifikasi bersamaan, isolasi dua parent dan akun nonaktif; smoke server Go nyata dengan DB pengujian lulus; vet dan kompilasi Linux/Windows lulus; perbaiki presisi waktu OTP pada batas mikrodetik DB; AUTH_TESTING.md disertakan · — · tim: hasil pengembangan tidak menggantikan suite PostgreSQL native/Windows lengkap

- 13:30 · kontrak v0.5 draf + engine · engine (ZIP 07B) · sesuai keputusan pengguna, pembulatan KPSP menjadi sisa >=16 hari; core umur memakai pinjaman 30 hari dari pedoman SDIDTK 2022, next_kpsp/due dan pengulangan meragukan 14 hari diperjelas. Payload API tetap. 140 butir/14 formulir ditranskripsi dari MD pengguna dengan hash sumber; gambar tidak tersedia, default loader menolak penayangan sampai verifikasi visual/klinis lengkap. 39 tes KPSP unittest lulus; pytest penuh belum tersedia lokal · — · semua: gunakan kontrak v0.5 draf; tim materi: lengkapi gambar/rubrik; backend/frontend: endpoint belum aktif, jangan tampilkan bank teks sebagai kuesioner lengkap; lihat engine/debug/PATCH_07B.md

- 13:12 · backend · hasil uji pengguna dengan fake engine · POST dan GET food-recalls berhasil dengan ID yang sama; growth?indicator=wfa mengembalikan titik berat tersimpan pada umur 304 hari, error:null; berat 0 ditolak VALIDATION_ERROR dan tanggal pengukuran duplikat ditolak aturan DB · — · backend: cek riwayat untuk memastikan tidak ada baris tambahan; diet/z-score/reference tetap dummy, bukan penilaian medis

- 13:10 · backend · hasil uji pengguna dengan fake engine · status dan kpsp/next berhasil, 10 pertanyaan DUMMY TEST tampil; POST jawaban KPSP menghasilkan yes_count 10 dan result fixture sesuai, GET riwayat mengembalikan ID yang sama; baca/tulis PostgreSQL nyata terbukti pada alur tersebut · — · tim: hasil sesuai/Aman merupakan fixture dan tidak membuktikan perhitungan klinis

- 13:01 · engine · engine (persiapan ZIP 07A) · core skor KPSP dan validasi 10 jawaban, primitif umur literal kontrak dan loader bank lokal; 19 tes unittest lulus, pytest penuh belum tersedia lokal. Bank pertanyaan, umur dari tanggal, due dan endpoint belum tersedia; batas tepat 16 hari masih berbeda antara kontrak dan contoh resmi · — · tim/pemilik kontrak: sediakan pedoman SDIDTK dan putuskan pembulatan tepat 16 hari; jangan anggap KPSP lengkap

- 13:01 · docs · engine · selesaikan penanda konflik CHANGELOG dari main terbaru dengan mempertahankan seluruh entri unik kedua sisi; selaraskan bagian Engine HANDOFF dengan keberadaan kode Patch 05/06 dan status persiapan 07A; catatan backend/frontend dan matriks integrasi dipertahankan · — · semua: merge dokumen terbaru sebelum menerapkan ZIP

- 12:52 · backend/testing · tim backend · tambah fake engine Python standar di 127.0.0.1:18001, diaktifkan eksplisit melalui override ENGINE_URL; health/growth/reference/kuesioner/skor dummy, 5 tes HTTP lulus; README, handoff/changelog addon tersedia; tidak mengubah engine asli/.env atau membuat acuan WHO palsu · — · tim: gunakan data uji, z-score null/reference kosong/diet null dan label Aman/sesuai hanya fixture; health pada /engine/v1/health, root /engine/v1 tetap 404

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
