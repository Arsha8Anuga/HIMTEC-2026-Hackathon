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

- **Diperbarui:** 7 November 2026, 13:45 WIB; berdasarkan file lampiran dan hasil pengujian yang dilaporkan pengguna pada percakapan ini.
- **Acuan:** kontrak medis v0.4, PRD users/children.parent_id, paket kompatibilitas backend, fake engine testing dan paket OTP dummy berbasis repository 1a0fe1b. Dokumen ini memperbarui status backend tanpa menimpa bagian engine/frontend.
- **Status:** API dasar dan alur dengan fake engine telah diuji pengguna pada Windows/PostgreSQL lokal. Pendaftaran OTP, verifikasi dan pengenalan sesi /auth/me berhasil. Integrasi engine medis asli dan frontend lengkap belum terverifikasi. Tidak ada push GitHub pada pekerjaan dokumentasi ini; status commit/push pengguna di luar percakapan tidak diasumsikan.

### Implementasi yang sudah dikerjakan

- Go API pada 8080/api/v1: daftar/tambah/detail anak; status; input/riwayat/hapus pengukuran; kurva; jadwal/input/riwayat KPSP; panduan; input/riwayat catatan makan. GET/HEAD /api/v1 dan /api/v1/ diarahkan 307 ke /children; unknown path tetap JSON 404 dan POST root tidak dialihkan.
- Migrasi 001+003+004 dijalankan dalam satu transaksi dengan advisory lock. Seed anak 002 tetap opsional. Lima tabel bisnis ditambah tiga tabel auth menjadi delapan: users, children, measurements, kpsp_results, food_recalls, otp_codes, auth_sessions, audit_logs.
- Migrasi 003 menambah parent demo, children.parent_id NOT NULL/FK/indeks; anak legacy tanpa pemilik diberi parent demo, pemilik existing dan riwayat dipertahankan. food_groups text[] dari DDL PRD diubah ke JSONB dengan nilai/urutan tetap; JSON API tidak berubah. Akun demo nonaktif/role berbeda tidak diaktifkan ulang otomatis.
- Query anak dan seluruh data turunannya memeriksa pemilik serta parent aktif. Kegagalan engine dan DB dipisahkan; route engine belum tersedia/koneksi gagal/response invalid menjadi 503, validasi engine 422 diteruskan dengan fields, error DB menjadi 500, data lokal di luar scope/tidak ada menjadi 404.
- POST pengukuran/catatan makan menyimpan sebelum evaluasi. Pesan kegagalan evaluasi menjelaskan data sudah tersimpan, ID dicatat di log, dan pengguna diminta membaca riwayat sebelum POST ulang. Duplikasi tanggal ditolak DB.
- Validasi umur recall memakai hari/30,4375 pada recall_date untuk rentang [6,24), tanggal KPSP tidak boleh sebelum lahir/di masa depan. Titik grafik kosong disaring; client menolak respons kosong/null/rusak/lebih dari 4 MiB; skor KPSP hilang tidak dianggap nol, jadwal dan jumlah butir diperiksa.
- Port 8080 di-bind sebelum DB; pesan siap muncul sesudah bind, migrasi dan data statis berhasil. guides.id.json tetap kosong menunggu materi resmi.

### Fake engine — mode pengujian

- Addon backend/testing/fake_engine.py memakai Python standar, bind loopback port 18001, dijalankan dengan --testing-only; override ENGINE_URL hanya pada terminal Go, tidak mengganti .env/engine medis asli. Lima tes HTTP Python lulus pada pengembangan.
- Endpoint health: /engine/v1/health dengan status ok dan who_tables_loaded=false. Root /engine/v1 memang 404; ini terpisah dari akses data Go/PostgreSQL.
- Fixture growth selalu green, z-score null, klasifikasi/alasan kosong; reference array kosong, diet null, jadwal KPSP tetap 9 bulan, 10 pertanyaan DUMMY TEST dan result selalu sesuai. Tidak menguji WHO, IYCF atau validitas KPSP. Label Aman/sesuai pada pengujian bukan hasil kesehatan.
- Sebelum OTP, pengguna berhasil menjalankan alur ini dengan data milik parent demo. Setelah mode OTP aktif, semua pengujian route data harus membawa bearer token dan UUID anak milik akun sesi.

### OTP dummy — mode pengujian lokal

- Diaktifkan eksplisit dengan AUTH_MODE=otp_dummy; bind Go hanya pada 127.0.0.1:8080. Default/demo tetap alur parent demo lama tanpa login. Konfigurasi harus berada pada terminal yang menjalankan Go dan proses perlu di-restart setelah perubahan.
- Endpoint tambahan: POST /auth/register (name/email), POST /auth/login (email), POST /auth/verify (challenge_id/code string), GET /auth/me, POST /auth/logout. Prefix seluruhnya /api/v1. Penjelasan ekstensi API dan perintah lengkap ada di backend/AUTH_TESTING.md; kontrak medis tidak diubah otomatis.
- OTP dikirim hanya ke terminal Go, bukan email/SMS. challenge_id adalah UUID permintaan, berbeda dari kode enam digit. Akun parent baru dibuat setelah verifikasi berhasil; request role/parent_id tidak diterima.
- OTP tersimpan HMAC, berlaku 5 menit, satu kali pakai, maksimal 5 percobaan; request minimal berselang 60 detik dan maksimal 5 per email per jam. Kode baru membatalkan kode sebelumnya; restart membatalkan OTP pending. Presisi waktu diselaraskan dengan mikrodetik DB.
- Sesi token acak disimpan hashed (SHA-256), berlaku 24 jam, dicabut lewat logout; lookup memeriksa role parent/status aktif. Audit mencatat peristiwa tanpa OTP/access_token. Kode dan token aktual tidak dimasukkan ke dokumentasi.
- Semua route bisnis di mode OTP membutuhkan Authorization: Bearer. Store/Service disalin per request dengan user dari sesi, tanpa mengubah ParentID shared atau fallback ke demo. CORS mengizinkan Authorization untuk origin yang dikonfigurasi.
- Error auth tambahan: 401 UNAUTHORIZED dan 429 RATE_LIMITED. Browser tanpa header pada /children dapat 401. Akun baru mulai tanpa anak; data demo lama tidak otomatis dipindahkan. Admin/nonaktif tidak mendapat akses login parent.

### Bukti dari laptop pengguna

| Pemeriksaan | Bukti yang diterima | Status |
| --- | --- | --- |
| Daftar/tambah/detail anak | Respons data anak dan error:null | Berhasil, mode demo |
| Simpan/baca pengukuran | ID yang sama terbaca setelah POST 503 dengan pesan sudah tersimpan | Berhasil, PostgreSQL lokal |
| parent_id | Screenshot pgAdmin menampilkan parent_id terisi untuk dua anak | Terlihat terisi; bukan bukti seluruh constraint |
| Status via fake engine | Respons green/Aman, pengukuran terbaca, error:null | Berhasil, fixture |
| Kuesioner dummy | 10 item DUMMY TEST, umur jadwal 9, error:null | Berhasil, fixture |
| POST/GET KPSP | yes_count 10, result fixture sesuai; ID POST sama dengan riwayat | Berhasil, penyimpanan lokal |
| POST/GET food-recalls | Catatan tanggal 6 November terbaca dengan ID sama, error:null | Berhasil, penyimpanan lokal |
| Growth wfa | Titik berat 8, umur 304 hari; z null/reference kosong | Berhasil, data protokol |
| Berat tidak valid | weight_kg 0 ditolak VALIDATION_ERROR pada fields.weight_kg | Berhasil |
| Tanggal pengukuran duplikat | Ditolak VALIDATION_ERROR pada fields.body | Penolakan berhasil; hasil GET riwayat setelah percobaan terakhir belum dikirim |
| Startup OTP | Log AUTH_MODE=otp_dummy dan siap pada loopback | Berhasil |
| Pendaftaran dan verifikasi OTP | Challenge cocok dengan log; verify menghasilkan user role parent | Berhasil pada Windows/PostgreSQL lokal |
| GET /auth/me | User uji yang sama, role parent, error:null dengan bearer token | Sesi dikenali; berhasil |
| Daftar/tambah anak akun OTP baru | Baru disarankan, belum ada hasil pengguna | Belum diverifikasi di laptop |
| Login ulang/logout/expired/replay/isolasi akun | Belum ada hasil pengguna | Baru teruji di lingkungan pengembangan |

Hasil login awal merupakan verifikasi OTP pendaftaran yang langsung menerbitkan sesi. Keberhasilan endpoint /auth/login untuk akun existing dan /auth/logout pada laptop tidak disimpulkan dari /auth/me saja.

### Tes pada lingkungan pengembangan

- Go unit, race detector dan vet lulus; kompilasi Linux/Windows amd64 lulus. Kompilasi Windows tidak menggantikan runtime/pengujian lengkap laptop pengguna.
- SQL melalui lib/pq ke PGlite 0.3.2/PostgreSQL WASM (socket 0.0.7) lulus untuk fresh/legacy migration, idempotensi, seed, preservasi array PRD, rollback dan isolasi repository.
- Tes auth melalui SQL pengujian lulus untuk register/login/verify/me/logout, expiry, replay, rate/attempt limit, restart, role injection, akun nonaktif, request concurrent antar parent dan satu kode yang diverifikasi bersamaan hanya berhasil sekali.
- Smoke server Go yang berjalan dengan DB pengujian lulus: startup migrasi, OTP terminal, aktivasi akun, me, tambah anak milik sesi, logout dan penolakan token lama. Tes fake engine lima kasus HTTP lulus.
- Suite SQL/native otomatis lengkap di laptop belum dilaporkan. Uji lokal pengguna pada tabel di atas merupakan bukti aktual untuk endpoint tertentu, bukan bukti seluruh suite native/engine medis lulus.

### Menjalankan kembali dan langkah berikutnya

1. Pertahankan .env lokal. Dari backend, jalankan fake engine di terminal terpisah: python testing/fake_engine.py --testing-only.
2. Pada terminal Go: set $env:AUTH_MODE="otp_dummy" dan $env:ENGINE_URL="http://127.0.0.1:18001/engine/v1", lalu go run ./cmd/server. Hentikan proses Go lama dahulu bila port dipakai.
3. Di terminal pengujian pertahankan $base, $session dan $headers. Uji GET "$base/children" -Headers $headers. Daftar kosong normal untuk akun baru; hasilnya belum diterima pada sesi ini.
4. Tambah anak milik sesi dengan -Headers $headers, kemudian uji pengukuran/status/KPSP/catatan makan memakai ID baru. Uji logout dan login ulang setelah jeda request OTP; jangan mengirim token atau kode ke chat/dokumentasi.
5. Uji dua akun untuk memastikan data terpisah; jalankan suite SQL pada database uji terpisah melalui BACKEND_TEST_DATABASE_URL. Jangan arahkan suite ke DB demo/produksi.
6. Selesaikan koneksi engine asli (IP/port/bind/firewall) dan endpoint medis sesudah tersedia. Kegagalan koneksi real engine sebelumnya masih belum terpecahkan; fake engine hanya menyediakan fixture lokal.
7. Hubungkan frontend dengan bearer header, lengkapi materi guides dan keputusan kontrak yang terbuka (ringkasan anak, reference, rentang WHO 1826 vs kontrak 1856, presisi/posisi). Integrasikan spesifikasi auth tambahan bersama pemilik kontrak.
8. Gabungkan dokumen dan kode tim sebelum commit/push; hasil git di luar percakapan tidak diasumsikan. Pada pembaruan ini hanya file lampiran yang disunting, tidak ada kode atau push yang dijalankan.

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

**Status backend terkini:** alur dasar dan fixture fake engine telah dilaporkan berhasil di laptop; OTP pendaftaran, verifikasi dan /auth/me juga berhasil. Sesi logout/login ulang, isolasi akun native, frontend dan engine medis asli masih perlu diuji. Tabel end-to-end di atas tetap Belum karena integrasi seluruh layanan belum dibuktikan.
