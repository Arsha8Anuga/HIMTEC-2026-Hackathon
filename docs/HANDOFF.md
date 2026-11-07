# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Status sinkronisasi dokumentasi:** diperiksa dari kode snapshot 6551237 dan engine/debug/PATCH_07B.md; bukan laporan pengujian engine baru oleh patch backend.
- **Kode tersedia:** pertumbuhan/klasifikasi/early warning (05/06), core KPSP (07A/07B), komponen umur dari tanggal dengan peminjaman 30 hari, pembulatan >=16, pemilihan kuesioner/jadwal/due serta bank transkripsi 14 kelompok x10 butir. Keputusan >=16 tercatat di Patch 07B/rules; dokumen kontrak diselaraskan sebagai v0.5 draf untuk review pemilik.
- **Router HTTP:** engine/app/main.py masih hanya memasang health. /growth/evaluate, /reference, /kpsp/questionnaire dan /kpsp/score belum didaftarkan ke aplikasi FastAPI. Fungsi core tersedia tidak berarti API Go sudah dapat memakainya.
- **Bank pertanyaan:** source metadata menyatakan visual_assets_status=missing dan clinical_review_status=text_transcription_only. Loader runtime normal menolak bank belum terverifikasi; for_review hanya untuk pemeriksaan. Gambar/aset serta review klinis perlu diselesaikan sebelum tayang. Tidak ada klaim bank visual/klinis lengkap dari patch dokumentasi ini.
- **Bukti pengujian yang tercatat:** Patch 07B melaporkan 39 tes KPSP unittest lulus (19 diperbarui +20 baru) pada Python 3.12/Pydantic 2.14.2; pytest penuh belum tersedia pada sesi tersebut. Ini laporan sumber, tidak dijalankan ulang pada pekerjaan backend. Bukti terdahulu 07A/05/06 tetap merupakan riwayat di changelog/debug, bukan tes endpoint engine nyata.
- **Terbuka:** endpoint HTTP dan output kontrak lengkap, gambar/review bank, IYCF, WHO 1826 vs batas input 1856 hari, kebijakan presisi/posisi, serta pembandingan klinis dan integrasi seluruh layanan.
- **Berikutnya:** pemilik engine menambahkan router sesudah komponen/data siap dan menjalankan pengujian; backend sudah menyediakan diagnostik health/OpenAPI tanpa data anak. Tidak ada kode atau data engine yang diubah dalam paket backend ini.

## Backend — tim backend


### Validasi patch penyelarasan

Go test -race ./... dan go vet ./... lulus pada Go 1.22.12/Linux. Suite SQL integrasi dilewati pada pengujian ulang ini karena BACKEND_TEST_DATABASE_URL tidak diisi; kode auth/repository/migrasi tidak diubah oleh patch. Kompilasi server dan check-engine untuk Windows amd64 lulus. CLI yang berjalan terhadap HTTP fixture fake lulus, dan lima tes fake engine Python lulus. PostgreSQL native/Windows runtime serta engine medis asli tetap perlu diuji. Tidak ada kode/ambang/data medis engine yang diubah.

- **Patch penyelarasan 13:59 WIB:** basis kode 6551237. Backend mempertahankan OTP dummy, data dan fake engine yang sudah berjalan; tambah diagnostik read-only health/OpenAPI, pesan 503 yang membedakan route hilang dari koneksi, serta .env loader bersama CLI/server. Draf kontrak v0.5, PRD dan README kini membedakan fitur aktual dari rencana. Tidak ada perubahan kode engine/frontend atau migrasi DB.
- **Cara cek engine:** dari backend jalankan go run ./cmd/check-engine. Exit 0 untuk diagnostik dasar/fake, 1 untuk health gagal/route hilang/WHO real false, 2 untuk konfigurasi kosong, 3 untuk route belum dapat diperiksa. OpenAPI hanya petunjuk registrasi; bukan bukti perhitungan benar. Server melakukan probe maksimal 3 detik lalu tetap melayani CRUD/login. Kegagalan engine tidak mengaktifkan fake otomatis.
- **Batas pekerjaan:** core/rute medis asli dan frontend/Compose belum dibangun oleh patch ini. Fake tetap dipilih melalui ENGINE_URL. Pembulatan KPSP diserahkan ke engine; Go tidak membuat algoritma medis baru. Kontrak sinkronisasi masih draf, perlu review pemilik.

- **Diperbarui:** 7 November 2026, 13:45 WIB; berdasarkan file lampiran dan hasil pengujian yang dilaporkan pengguna pada percakapan ini.
- **Acuan:** kontrak v0.5 draf sinkronisasi (model medis tetap kompatibel v0.4), PRD users/children.parent_id, paket kompatibilitas backend, fake engine testing dan paket OTP dummy berbasis repository 1a0fe1b. Dokumen ini memperbarui status backend tanpa menimpa bagian engine/frontend.
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
- Endpoint tambahan: POST /auth/register (name/email), POST /auth/login (email), POST /auth/verify (challenge_id/code string), GET /auth/me, POST /auth/logout. Prefix seluruhnya /api/v1. Penjelasan ekstensi API dan perintah lengkap ada di backend/AUTH_TESTING.md; model medis tetap kompatibel; kontrak v0.5 draf menyatukan dokumentasi OTP dan keputusan Patch 07B, untuk review pemilik.
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
