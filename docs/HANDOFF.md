# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Diperbarui:** 2026-11-07 13:01 WIB (persiapan ZIP 07A; basis `02aeba3e68b4ee63c4e4ac0e92fd0a6055b1a55a`).
- **Status kode:** Patch 01–06 sudah ada pada repository. Bagian engine pada HANDOFF upstream masih merujuk Hotfix 04A walaupun kode Patch 05/06 sudah ada; bagian ini diselaraskan. Endpoint HTTP pada main masih hanya health.
- **Selesai pada persiapan 07A:** validasi ketat 10 jawaban unik item_no 1–10, umur jadwal sesuai kontrak, skor yes_count/result, primitif pembulatan literal kontrak atas bulan penuh/sisa hari yang sudah dihitung, pemilihan umur kuesioner dari umur bulat, serta loader bank lokal lengkap dengan atribusi/validasi struktur. Body skor cocok dengan client Go pada commit acuan. Aturan dibaca dari `data/kpsp/rules.json`; tidak menambah endpoint, enum, dependensi, atau mengubah kontrak/backend/frontend.
- **Belum selesai pada Patch 07:** bank 140 butir untuk 14 umur, transkripsi/verifikasi instruksi dan gambar, perhitungan umur dari tanggal, next_kpsp/due, evaluasi ulang meragukan, serta endpoint skor/kuesioner. Jangan menyebut persiapan ini sebagai fitur KPSP siap pakai.
- **Masalah yang perlu keputusan:** kontrak menyebut pembulatan bila sisa >16 hari, sedangkan contoh sumber Kemenkes membulatkan tepat 16. Primitif 07A tetap mengikuti literal kontrak dan belum dihubungkan ke jadwal publik. Perlu pedoman SDIDTK pilihan tim untuk bank pertanyaan; tidak ada pertanyaan klinis yang dikarang/disisipkan. Loader gagal bila bank hilang atau tidak lengkap; metadata sumber saja bukan bukti validitas klinis.
- **Pengujian 07A:** 19 tes baru lulus melalui unittest (Python 3.12/Pydantic 2.14.2). Pytest penuh dicoba tetapi gagal karena modul pytest belum tersedia. Tes bank memakai teks sintetis berlabel TEST FORMAT SENTINEL, tidak ada bank klinis yang dibundel.
- **Bukti sebelumnya:** pengguna melaporkan Hotfix 04A 107 passed/1 warning (1,49 detik) pada Windows/Python 3.10.6; Patch 05 119 passed/3 skipped/52 subtests/1 warning (1,18 detik). Tiga tes WHO pada hasil pengguna itu dilewati. Lokal Patch 05 sebelumnya 15 tes unittest lulus dengan WHO asli, Patch 06 29 tes unittest lulus termasuk satu integrasi WHO. Belum ada hasil pytest Patch 06/07A dari laptop pengguna pada sesi ini.
- **Komponen pertumbuhan:** core evaluasi per pengukuran, klasifikasi, flag dan early warning tersedia. 1T/2T memakai bulan kalender berurutan sesuai klarifikasi pengguna, pengukuran valid terakhir per bulan; bulan terlewat memutus 2T. KBM masih fallback kontrak <=0 g. Domain umur WHO 1826 vs kontrak 1856, grid/presisi WFL-WFH, flag posisi berdiri sebelum 9 bulan dan penyelarasan pembulatan masih terbuka.
- **Cara uji:** `cd engine && python -m unittest discover -s tests -p test_kpsp.py -v`, lalu `python -m pytest -q` di lingkungan requirements. Perkiraan suite menjadi 170 kasus setelah Patch 06+07A, dengan empat tes WHO yang dapat dilewati jika data belum tersedia; hitung hasil nyata. Uraian lengkap: `engine/debug/PATCH_07A.md`.
- **Dokumentasi bersama:** penanda konflik merge di CHANGELOG upstream diselesaikan dengan mempertahankan seluruh entri unik kedua sisi. Bagian backend/frontend serta matriks integrasi HANDOFF dipertahankan dari repo terbaru; tidak menimpa catatan koneksi DB/jaringan tim.
- **Butuh dari tim/pengguna:** unggahan pedoman SDIDTK/formulir pilihan tim, keputusan batas tepat 16 hari, dan keputusan perhitungan komponen umur serta jadwal/due; hasil pytest dengan tabel WHO asli. Sumber bank diperlukan sebelum transkripsi. Tidak ada asumsi izin redistribusi seluruh pedoman.
- **Langkah berikutnya:** selesaikan Patch 07 setelah sumber/keputusan tersedia; lanjut IYCF, endpoint respons lengkap dan uji integrasi lima kasus WHO. Paket dikirim ZIP tanpa push GitHub; periksa docs terbaru sebelum merge.

## Backend — tim backend

- **Merge dokumentasi 11:53 WIB:** basis main `b4958d3c2725990c781e5287bc7f4176d3a666a0`; catatan engine/frontend asli dipertahankan. Backend merangkum paket ZIP yang dikerjakan pada sesi ini; merge dokumentasi bukan bukti kode paket sudah di-push/diterapkan. Kode engine pada main sudah mendapat modul evaluasi/early warning, tetapi main.py masih hanya mendaftarkan health. Bagian engine upstream di bawah/atas tetap dicatat sesuai sumber tanpa mengklaim tes baru.

### Bukti terbaru dari laptop pengguna

- go test ./... dilaporkan lulus pada Windows untuk versi yang dijalankan pengguna.
- GET /children, POST /children dan GET /children/{id} berhasil; anak uji dapat dibaca kembali.
- POST pengukuran menghasilkan ENGINE_UNAVAILABLE dengan pesan "Pengukuran sudah tersimpan"; GET riwayat menampilkan pengukuran yang sama. Penyimpanan PostgreSQL nyata terbukti untuk alur ini.
- Screenshot pgAdmin memperlihatkan dua anak dengan parent_id terisi. Screenshot tersebut tidak menampilkan hasil lengkap tabel users/seluruh tabel, sehingga tidak menjadi bukti semua constraint telah diuji.
- Request health ke http://192.168.43.20:8001/engine/v1/health gagal dengan "Unable to connect to the remote server". IP/port/startup/firewall/jaringan perlu diperiksa. Penyebab spesifik koneksi belum dipastikan.
- Patch redirect GET/HEAD /api/v1 dan /api/v1/ ke /children sudah dibuat dan diuji di lingkungan pengembangan. Pengguna belum mengonfirmasi hasil setelah memasang paket root dan restart; 404 sebelumnya berasal dari root lama, terpisah dari koneksi engine.
- Belum diverifikasi di laptop: semua tes integrasi native, isolasi lintas pemilik, catatan makan, KPSP, kurva, endpoint engine nyata, frontend, serta runtime paket root terbaru.


- **Pembaruan routing 11:48 WIB:** GET/HEAD /api/v1 dan /api/v1/ memberi 307 ke /api/v1/children sesuai permintaan pengguna. Daftar anak tetap memakai route/model yang ada; unknown path tetap JSON 404, POST root tidak dialihkan. Suite Go/race, vet dan kompilasi Windows lulus; tes SQL integrasi tidak diulang untuk perubahan ini. Kegagalan health engine adalah masalah koneksi terpisah; daftar anak dan riwayat tidak bergantung pada engine.

- **Diperbarui:** 7 November 2026, 11:35 WIB.
- **Acuan:** repository `af4193a6da0a9019a25f25738b0e9caf9243ffac` (`Document Update`), `docs/CONTRACT.md` v0.4 (draf), PRD dengan tabel users dan kepemilikan anak, serta hotfix engine 04A. Paket ini menggabungkan perbaikan backend dari arsip sebelumnya dan penyesuaian PRD terbaru. Belum di-push ke GitHub.
- **Status serah terima:** implementasi dan tes paket selesai; penerapan pada PostgreSQL native/laptop Windows serta integrasi engine Python/ frontend nyata masih perlu dilakukan. Bagian backend yang terduplikasi di versi sumber sudah digabungkan menjadi satu di sini.

### Implementasi yang sudah tersedia

- Go API pada port 8080, prefix `/api/v1`, 14 route publik: daftar/tambah/detail anak, status, riwayat/input/hapus pengukuran, kurva, jadwal/input/riwayat KPSP, panduan, serta input/riwayat catatan makan.
- Model dan validasi kontrak, amplop data/error, PostgreSQL melalui lib/pq, pembagian handler/service/repository/engineclient/model, CORS_ORIGIN dan client ENGINE_URL dengan timeout 3 detik.
- `messages.id.json` untuk teks Indonesia; `guides.id.json` tetap kosong menunggu materi resmi. Engine tetap menghitung hasil medis; Go menyimpan riwayat dan menambahkan teks pengguna.

### Perubahan database dan kepemilikan terbaru

1. `003_demo_parent.sql` menambahkan tabel users, akun parent demo, children.parent_id NOT NULL, FK ke users dan indeks parent. ID demo server: `00000000-0000-4000-8000-000000000001`.
2. Startup menjalankan 001 lalu 003 dalam satu transaksi dengan advisory lock. Migrasi boleh dijalankan berulang. Bila gagal, transaksi dibatalkan. Seed identitas anak 002 tetap manual/opsional dan telah disesuaikan dengan parent.
3. Anak legacy tanpa pemilik diberi parent demo. ID dan riwayat dipertahankan; parent yang sudah ada tidak ditimpa. Akun demo nonaktif/role berbeda tidak diaktifkan ulang diam-diam.
4. Database yang dibuat dari DDL PRD dengan food_groups text[] di-upgrade ke JSONB menggunakan to_jsonb, mempertahankan nilai/urutan. Public JSON tetap array string; PRD mengizinkan penyesuaian tipe penyimpanan.
5. Semua query repository memeriksa kepemilikan serta parent aktif, termasuk baca/tulis/hapus data turunan. Anak milik orang lain tidak dapat dibaca lewat detail dan tidak dapat ditulis melalui repository. Context parent dipilih server; tidak ada parent_id baru pada JSON publik.
6. MVP tetap satu orang tua demo tanpa login. OTP, pengelolaan akun dan autentikasi multi-pengguna adalah pekerjaan setelah MVP.

### Perubahan validasi dan perbaikan lain

- Umur catatan makan pada recall_date memakai hari / 30,4375 tanpa pembulatan dengan rentang 6 sampai kurang dari 24 bulan, selaras engine 04A. KPSP menolak answered_at sebelum birth_date atau setelah hari ini.
- Error HTTP/protokol engine diberi tipe internal terpisah dari error DB. Route engine belum tersedia, timeout, koneksi gagal atau respons invalid menjadi 503 ENGINE_UNAVAILABLE. HTTP 422 VALIDATION_ERROR diteruskan beserta fields; error DB saat evaluasi menjadi 500 INTERNAL; anak/pengukuran lokal yang tidak ada atau di luar scope menjadi 404 NOT_FOUND.
- POST pengukuran/catatan makan tetap menyimpan sebelum evaluasi. Pesan menyebut sudah tersimpan bila evaluasi berikutnya gagal; ID dicatat di log. Frontend perlu membaca riwayat sebelum mengirim ulang. Amplop error tetap data:null sesuai kontrak.
- Client menolak JSON rusak, data kosong/null, field error hilang dan respons lebih dari 4 MiB. Titik kurva berkoordinat kosong disaring. Skor KPSP hilang tidak dianggap nol; umur jadwal dan 10 butir kuesioner diperiksa.
- Port 8080 di-bind sebelum membuka DB. Pesan siap dicetak sesudah bind, migrasi dan data statis berhasil; konflik port dilaporkan dengan instruksi memeriksa backend/proses lama.
- Tidak menambah endpoint, field JSON publik, enum, port atau variabel runtime wajib; batas umur pengukuran tetap kontrak. Skema DB berubah sesuai PRD dan harus diterapkan bersama kode patch.

### Hasil uji dan batas bukti

| Pemeriksaan | Hasil | Lingkungan/batas |
| --- | --- | --- |
| Unit/handler/client/service dan race detector | Lulus | Go 1.22.12 Linux; HTTP test server dan SQL mock |
| Lima tes repository SQL | Lulus | lib/pq ke PGlite 0.3.2/PostgreSQL WASM melalui pglite-socket 0.0.7; bukan PostgreSQL native |
| Migrasi fresh dan seed | Lulus | Lima tabel, satu parent demo, startup tidak menjalankan seed anak, migrasi/seed idempoten |
| Migrasi legacy dan kepemilikan | Lulus | Anak/riwayat dipertahankan; parent existing tidak diubah |
| Isolasi parent/admin/nonaktif | Lulus | Baca/tulis/hapus repository diuji, termasuk penolakan akses lintas parent |
| Penyimpanan text[] PRD dan rollback | Lulus | Isi array dipertahankan; migrasi gagal tidak meninggalkan tabel parsial |
| go vet | Lulus | Analisis statis Go |
| Kompilasi Linux dan Windows amd64 | Lulus | buildvcs=false pada lingkungan pengembangan; Windows belum dijalankan |
| Smoke HTTP backend yang berjalan | Lulus | Startup migrasi, tambah/baca anak, POST lalu engine 404, pesan sudah tersimpan, GET riwayat, duplikasi dan KPSP sebelum lahir |
| Konflik port 8080 | Lulus | Pesan gagal jelas sebelum akses DB; tidak mencetak pesan siap |

Tes SQL integrasi disertakan dalam `internal/repository/postgres_integration_test.go` dan normalnya dilewati tanpa BACKEND_TEST_DATABASE_URL. Gunakan database pengujian terpisah dengan izin membuat schema; tes membuat dan menghapus schema unik backend_test_*. PGlite dan harness pengujian tidak menjadi dependensi atau isi paket backend.

**Laporan dari laptop pengguna:** go test ./... sebelumnya lulus pada Windows; go run sempat gagal bind port 8080 karena port sudah dipakai. Hasil itu untuk versi sebelum paket ini. Pengguna sebelumnya juga melaporkan POST pengukuran 503. Penyebab spesifik runtime 503 tersebut belum dipastikan dari log engine/Go.

**Batas pengujian:** CRUD dasar anak dan simpan/baca pengukuran telah dibuktikan pengguna pada layanan Windows/PostgreSQL lokal. Suite integrasi native lengkap, runtime paket root terbaru, engine Python nyata, frontend, alur lengkap dan ketepatan medis tetap belum diverifikasi. Keberhasilan SQL WASM/HTTP tiruan tidak menggantikan pemeriksaan tersebut.

### Masalah dan ketergantungan yang masih terbuka

- Pada commit acuan, Python baru mendaftarkan /engine/v1/health. Fungsi matematika dan hotfix validasi ada, tetapi /growth/evaluate, /reference, /kpsp/questionnaire, /kpsp/score belum menjadi endpoint HTTP. Status/kurva/KPSP masih bisa 503. Health sukses atau who_tables_loaded=true belum membuktikan evaluasi siap.
- Bentuk ringkasan GET /children, body lengkap score KPSP dan respons reference perlu dikunci bersama pemilik kontrak. Daftar anak tetap berupa Child tanpa field ringkasan tambahan yang belum disepakati.
- Batas umur pengukuran kontrak 1856 hari versus tabel WHO 1826 hari tetap memerlukan keputusan pemilik kontrak/engine. Kebijakan presisi/posisi tidak diubah sepihak.
- Materi guides masih menunggu sumber resmi. Riwayat KPSP lama dengan tanggal yang sudah tidak valid tidak dibuang otomatis; bila ditemukan saat integrasi, tinjau datanya secara eksplisit.
- SQL langsung/skrip lama yang menambah anak harus mengikuti parent_id NOT NULL. Terapkan seluruh folder backend bersama migrasi 003; jangan hanya menyalin sebagian file Go.

### Menjalankan dan menerapkan

Hentikan backend lama dengan Ctrl+C. Backup database lama yang perlu dipertahankan, simpan perubahan lokal, lalu gabungkan isi ZIP ke akar repo. Hasilnya backend/go.mod dan docs/HANDOFF.md, bukan backend/backend. Pertahankan .env lokal.

```dotenv
DATABASE_URL=postgres://postgres:<PASSWORD>@localhost:5432/tumbuh?sslmode=disable
ENGINE_URL=http://<IP_LAPTOP_ENGINE>:8001/engine/v1
CORS_ORIGIN=http://localhost:5173
```

Database tumbuh harus sudah dibuat. Dari akar repo:

```powershell
cd backend
go mod download
go test ./...
go run ./cmd/server
```

Startup menjalankan 001+003. Seed opsional: psql -U postgres -d tumbuh -f migrations/002_seed_children.sql. Go minimal 1.22, PostgreSQL minimal 13. Gunakan PowerShell kedua untuk GET http://localhost:8080/api/v1/children; /api/v1/ kini mengarahkan ke daftar anak dan bukan health check engine.

Tes integrasi native pada DB uji terpisah:

```powershell
$env:BACKEND_TEST_DATABASE_URL="postgres://postgres:ISI_PASSWORD@localhost:5432/tumbuh_test?sslmode=disable"
go test -count=1 ./internal/repository
Remove-Item Env:BACKEND_TEST_DATABASE_URL
```

### Langkah berikutnya dan kebutuhan tim

1. Terapkan dan uji ulang pada PostgreSQL native/Windows, termasuk DB lama dan seed opsional. Periksa users, parent_id dan riwayat setelah migrasi; simpan hasil respons aktual.
2. Konfirmasikan ENGINE_URL, bind Python 0.0.0.0:8001 dan firewall hotspot. Uji evaluasi/reference/KPSP sesudah endpoint HTTP tersedia; gunakan log Go untuk menelusuri 503.
3. Hubungkan frontend; tampilkan error.message tentang data tersimpan, baca riwayat sebelum POST ulang, dan uji status/kurva/KPSP/catatan makan ujung ke ujung.
4. Minta pemilik kontrak mengunci bentuk respons yang belum lengkap serta rentang referensi; minta pemilik materi menyediakan panduan resmi.
5. Gabungkan perubahan dokumen tim yang lebih baru sebelum menimpa file docs dari ZIP, lalu commit backend dan catatan dokumentasinya bersama. Tidak ada push GitHub pada pekerjaan ini.

## Desain + frontend — (nama)

- **Diperbarui:** HH:MM
- **Selesai:**
- **Sedang dikerjakan:**
- **Belum dimulai:**
- **Cara menjalankan dan menguji:**
- **Masalah yang diketahui:**
- **Butuh dari orang lain:**
- **Langkah berikutnya:**

---

## Status integrasi

Status pada tabel ini membedakan **route terimplementasi** dan **terbukti teruji end-to-end**. Tanda `?` berarti belum dikonfirmasi oleh pemilik komponen.

| Endpoint | Go siap (kode) | Engine siap | Frontend tersambung | Uji end-to-end |
| --- | --- | --- | --- | --- |
| `GET/POST /children` | Ya | — | ? | Belum |
| `GET /children/{id}/status` | Ya | ? | ? | Belum |
| `POST /children/{id}/measurements` | Ya | ? | ? | Belum |
| `GET /children/{id}/growth` | Ya | ? | ? | Belum |
| `GET /children/{id}/kpsp/next`, `POST /children/{id}/kpsp` | Ya | ? | ? | Belum |
| `GET /guides` | Ya, data masih kosong | — | ? | Belum |
| `GET/POST /children/{id}/food-recalls` | Ya | ? | ? | Belum |

**Status backend setelah merge:** CRUD dasar dan penyimpanan/pembacaan pengukuran telah dilaporkan berhasil pada PostgreSQL lokal pengguna. Koneksi health engine gagal; integrasi engine/frontend lengkap belum lulus. Patch root redirect sudah diuji pada lingkungan pengembangan dan menunggu konfirmasi penerapan laptop. Kolom end-to-end pada tabel di atas tetap Belum untuk integrasi seluruh layanan.
