# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Diperbarui:** 2026-11-07 17:30 WIB (data demo + tampilan alasan, basis `6d4cdf1`).
- **Data demo (17:30):** `backend/migrations/005_seed_demo_measurements.sql` (dijalankan manual setelah 002, hari yang sama) dan `engine/scripts/verify_demo_seed.py`. Bukti: verifier 365 hari seed 0 kegagalan; lewat Go + PostgreSQL 16 + engine asli: Anisa red `WEIGHT_NOT_GAINING_2X`, Bima green, Citra red `STUNTED`, seed aman diulang; hapus dua titik terakhir Anisa → green, catat ulang → yellow → red. Ringkasan anak kini menampilkan kalimat tindakan tiap alasan tanpa diklik (Playwright 23 passed, termasuk tes baru).
- **Status kode:** Patch 01–09 di main. Endpoint aktif: `health`, `growth/evaluate`, `kpsp/score`, `reference` (wfa, lhfa, hcfa). Belum: `kpsp/questionnaire` (sengaja, bank belum lengkap) dan `reference` wfl_wfh (503, menunggu kontrak).
- **Bukti audit 16:10:** pytest 262 passed dengan tabel WHO asli (Linux, Python 3.13). Uji ujung ke ujung engine asli + Go + PostgreSQL 16: skenario Anisa green → yellow `WEIGHT_NOT_GAINING` → red `WEIGHT_NOT_GAINING_2X` dengan lhfa normal; catatan makan, skor KPSP, kurva wfa/lhfa/hcfa berhasil.
- **IYCF selesai (core):** MDD kelompok unik +ASI, MMF menurut umur/menyusu dan jumlah makan/susu, EFF telur/flesh foods; pola tiga catatan terakhir dalam 14 tanggal; satu hari buruk hanya info, >=2 kegagalan yang tersedia dapat yellow; NO_RECENT_FOOD_RECALL. Teks pengguna tetap milik Go. Semua aturan/URL sumber berada di `data/iycf/rules.json`.
- **Batas data makan:** umur pada recall memakai hari/30,4375 sesuai proyek, bukan umur pada as_of. Selisih terhadap WHO <730 hari di batas atas (proyek masih menerima hari 730) dicatat. Jendela as_of−13..as_of sama dengan backend; tujuh tanggal recency as_of−6..as_of. Susu opsional null dihitung nol untuk MMF; bukan bukti klinis tidak minum susu. Dairy tidak ditambahkan dari jumlah susu. MMF tidak sama dengan minimum frekuensi susu/MAD. Kode NO_ANIMAL_SOURCE_FOOD merujuk EFF kontrak (eggs/flesh), bukan klaim dairy tidak hewani.
- **Penggabungan:** `evaluate_growth_and_diet(request,tables)` mempertahankan per_measurement dan bukti pertumbuhan, menambah diet/reasons dan mengambil severity tertinggi. Red tidak diturunkan oleh diet baik. WHODataError tetap diteruskan. Respons core belum memiliki next_kpsp dan belum respons HTTP lengkap.
- **Pengujian Patch 08:** 35 tes baru lulus via unittest, termasuk satu integrasi WHO autentik+diet; tanpa berkas WHO, 34 berjalan/1 skipped. Pytest penuh dicoba tetapi gagal karena pytest tidak tersedia di lingkungan lokal Python 3.12/Pydantic 2.14.2. Perkiraan seluruh suite 225 kasus/5 integrasi WHO yang dapat skipped; itu bukan hasil lulus nyata.
- **KPSP 07B:** umur dengan pinjaman 30 hari dan pembulatan >=16 (disetujui pengguna), next_kpsp/due dan pengulangan meragukan 14 hari tersedia sebagai core. 140 teks/14 formulir dari MD pengguna ditranskripsi; gambar/rubrik tidak tersedia sehingga default loader menolak penayangan. Hanya for_review=True untuk peninjauan, bukan bypass produksi. 39 tes KPSP lulus unittest sebelumnya. Tidak membatalkan klarifikasi v0.5 meskipun docs main masih v0.4/status 07A.
- **Bukti pengguna terakhir:** Hotfix 04A 107 passed/1 warning (1,49 detik), Patch 05 119 passed/3 skipped/52 subtests/1 warning (1,18 detik) di Windows/Python 3.10.6. Tidak mengklaim tes WHO/patch berikutnya di laptop sudah lulus tanpa hasil baru.
- **Pertumbuhan:** core evaluasi/klasifikasi/flag dan early warning tersedia. 1T/2T kalender berurutan, bulan kosong memutus 2T, titik valid terakhir per bulan; KBM masih fallback <=0 g. Batas umur kini 1826 hari di kontrak v0.6, Go dan engine. Presisi WFL/WFH, flag berdiri sebelum 9 bulan dan pembulatan flag tetap isu integrasi.
- **Cara uji:** `cd engine && python -m unittest discover -s tests -p test_iycf.py -v`, lalu `python -m pytest -q` dengan requirements. Bila belum ada WHO, unduh saat setup memakai scripts/fetch_who_tables.py. Penjelasan `engine/debug/PATCH_08.md`.
- **Dokumentasi:** versi kontrak v0.5 dan entri 07B yang telah disetujui/diberikan sebelumnya digabung kembali dengan docs GitHub terbaru, kemudian catatan IYCF ditambahkan. Hotfix dokumentasi menggabungkan ulang HANDOFF/CHANGELOG dari main, termasuk pembaruan backend 13:45 (OTP dan bukti uji pengguna); bagian backend/frontend/matriks dipertahankan persis dari sumber terbaru. Tidak mengubah API/enum/dependensi/backend/frontend.
- **Belum selesai:** `kpsp/questionnaire` (gambar dan review klinis KPSP), `reference` wfl_wfh, lima kasus penuh WHO Anthro. IYCF ini adaptasi skrining proyek, bukan diagnosis atau evaluasi kecukupan gizi menyeluruh.
- **Kontrak v0.6 (draf):** batas umur 1826 hari (asal 1856 dan alasannya di bagian "Penegasan v0.6"); `GET /children` tanpa ringkasan; `otp_dummy` dinyatakan di luar kontrak. Satu isu tetap terbuka dengan sadar: garis acuan `wfl_wfh` (kurva BB/PB-TB belum ada untuk demo).
- **Menunggu keputusan Zena:** (1) KPSP: aktifkan bank teks berlabel atau biarkan nonaktif; (2) kurva BB/PB: Go memilih `wfl`/`wfh` dari umur (menambah enum API internal).
- **Langkah berikutnya:** umumkan v0.6 di grup; pastikan Go demo berjalan dalam mode `demo`; seed 002+005 pada hari demo; gladi penuh di laptop Windows demo.

## Backend — tim backend

- **Pembaruan bukti 14:14 WIB, 7 November 2026:** verifikasi OTP berikutnya untuk akun existing dikenali oleh /auth/me; daftar anak awal kosong, tambah/baca anak dengan token berhasil; logout dan penolakan token lama berhasil pada Windows/PostgreSQL lokal. Login setelah logout dan pembacaan ulang anak setelah login itu belum dilaporkan. Hanya dokumentasi backend yang diperbarui; catatan engine ZIP 08/frontend dipertahankan.

- **Diperbarui:** 7 November 2026, 13:45 WIB; berdasarkan file lampiran dan hasil pengujian yang dilaporkan pengguna pada percakapan ini.
- **Acuan:** kontrak medis v0.4, PRD users/children.parent_id, paket kompatibilitas backend, fake engine testing dan paket OTP dummy berbasis repository 1a0fe1b. Dokumen ini memperbarui status backend tanpa menimpa bagian engine/frontend.
- **Status:** API dasar dan alur dengan fake engine telah diuji pengguna pada Windows/PostgreSQL lokal. Pendaftaran OTP, verifikasi/sesi /auth/me, tambah/baca anak dengan token, logout dan penolakan token lama berhasil. Integrasi engine medis asli dan frontend lengkap belum terverifikasi. Tidak ada push GitHub pada pekerjaan dokumentasi ini; status commit/push pengguna di luar percakapan tidak diasumsikan.

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
| Verifikasi OTP berikutnya akun existing | /auth/me kembali mengenali akun yang sama, error:null | Berhasil; raw request /auth/login tidak disertakan dalam hasil terakhir |
| Daftar anak akun OTP sebelum tambah | GET /children dengan bearer menghasilkan data:[], error:null | Berhasil; akun memang belum punya anak |
| Tambah anak akun OTP | POST menghasilkan Anak Mutia Uji, error:null, created_at 14:07:46 WIB | Berhasil pada Windows/PostgreSQL lokal |
| Baca anak setelah tambah | GET /children menampilkan anak dengan ID sama seperti POST | Berhasil pada sesi yang sama |
| Logout | POST /auth/logout menghasilkan logged_out:true dan error:null | Berhasil |
| Token setelah logout | GET /children memakai token lama menghasilkan UNAUTHORIZED | Berhasil; sesi lama ditolak |
| Login setelah logout, expiry/replay OTP dan isolasi dua akun | Hasil lanjutan belum dikirim | Belum terverifikasi di laptop; tes pengembangan telah tercatat |

Hasil login awal adalah verifikasi OTP pendaftaran. Hasil sesi berikutnya memperlihatkan /auth/me mengenali akun existing yang sama; request mentah /auth/login tidak ditampilkan dalam kiriman terakhir. Logout dan penolakan token lama kini dibuktikan oleh respons terpisah, bukan disimpulkan dari /auth/me. Pembacaan anak setelah login ulang pasca-logout belum dikonfirmasi.

**Referensi data uji (bukan credential):** pengguna `Mutia Uji`, ID `8b86d1cb-4703-4f5e-adfe-b261fbfb21b7`; anak `Anak Mutia Uji`, ID `9ab42e38-99f7-430a-afd4-20c99db8253c`, dibuat 7 November 2026 pukul 14:07:46 WIB. ID anak pada POST dan GET sama. Tidak ada OTP atau access_token yang disimpan dalam dokumen. Pemeriksaan ini membuktikan data tampil di akun sesi, tetapi belum membuktikan isolasi dari akun kedua.

### Tes pada lingkungan pengembangan

- Go unit, race detector dan vet lulus; kompilasi Linux/Windows amd64 lulus. Kompilasi Windows tidak menggantikan runtime/pengujian lengkap laptop pengguna.
- SQL melalui lib/pq ke PGlite 0.3.2/PostgreSQL WASM (socket 0.0.7) lulus untuk fresh/legacy migration, idempotensi, seed, preservasi array PRD, rollback dan isolasi repository.
- Tes auth melalui SQL pengujian lulus untuk register/login/verify/me/logout, expiry, replay, rate/attempt limit, restart, role injection, akun nonaktif, request concurrent antar parent dan satu kode yang diverifikasi bersamaan hanya berhasil sekali.
- Smoke server Go yang berjalan dengan DB pengujian lulus: startup migrasi, OTP terminal, aktivasi akun, me, tambah anak milik sesi, logout dan penolakan token lama. Tes fake engine lima kasus HTTP lulus.
- Suite SQL/native otomatis lengkap di laptop belum dilaporkan. Uji lokal pengguna pada tabel di atas merupakan bukti aktual untuk endpoint tertentu, bukan bukti seluruh suite native/engine medis lulus.

### Menjalankan kembali dan langkah berikutnya

1. Pertahankan .env lokal. Dari backend, jalankan fake engine di terminal terpisah: python testing/fake_engine.py --testing-only.
2. Pada terminal Go: set $env:AUTH_MODE="otp_dummy" dan $env:ENGINE_URL="http://127.0.0.1:18001/engine/v1", lalu go run ./cmd/server. Hentikan proses Go lama dahulu bila port dipakai.
3. Token lama sudah dicabut oleh logout yang berhasil. Minta OTP login baru untuk akun existing, lakukan verify, dan bentuk ulang $headers dari token baru. Patuhi jeda minimal 60 detik antar-request OTP. Jangan memakai token yang sudah logout.
4. Setelah login ulang pasca-logout, GET "$base/children" dengan token baru. Pastikan Anak Mutia Uji ber-ID 9ab42e38-99f7-430a-afd4-20c99db8253c masih ada; hasil ini belum dikirim. Tidak perlu POST anak yang sama lagi. Kemudian lanjutkan pengukuran/status/KPSP/catatan makan dengan token dan ID tersebut. Jangan mengirim kode/token ke chat.
5. Uji dua akun untuk memastikan data terpisah; jalankan suite SQL pada database uji terpisah melalui BACKEND_TEST_DATABASE_URL. Jangan arahkan suite ke DB demo/produksi.
6. Selesaikan koneksi engine asli (IP/port/bind/firewall) dan endpoint medis sesudah tersedia. Kegagalan koneksi real engine sebelumnya masih belum terpecahkan; fake engine hanya menyediakan fixture lokal.
7. Hubungkan frontend dengan bearer header, lengkapi materi guides dan keputusan kontrak yang terbuka (ringkasan anak, reference, rentang WHO 1826 vs kontrak 1856, presisi/posisi). Integrasikan spesifikasi auth tambahan bersama pemilik kontrak.
8. Gabungkan dokumen dan kode tim sebelum commit/push; hasil git di luar percakapan tidak diasumsikan. Pada pembaruan ini hanya file lampiran yang disunting, tidak ada kode atau push yang dijalankan.

### Paket penyelarasan backend yang juga telah dibuat

- Basis 6551237; tambah cmd/check-engine dan loader .env bersama server. Probe hanya GET health/OpenAPI, maksimal 3 detik, tanpa data anak. Health OK dipisahkan dari keberadaan route; fake ditandai; OpenAPI unknown tidak dianggap bukti route hilang. Tidak ada fallback fake otomatis.
- HTTP upstream 404 menghasilkan pesan endpoint perhitungan belum tersedia; error transport menjelaskan pemeriksaan ENGINE_URL/proses Python. Kode publik ENGINE_UNAVAILABLE tetap 503; pesan setelah POST tetap menyebut data tersimpan.
- Draf kontrak v0.5, PRD, README dan handoff pada paket diselaraskan dengan OTP serta keputusan >=16 KPSP yang sudah tercatat di Patch 07B. Review pemilik kontrak tetap diperlukan. Go tidak menambah perhitungan medis; frontend/Compose dan endpoint engine asli tidak dibangun oleh patch ini.
- Unit/race, vet, kompilasi Windows server/CLI, smoke CLI fake dan lima tes fake Python lulus pada pengembangan. Suite SQL tidak diulang pada patch diagnostik. Pengguna berhasil menguji auth/data, tetapi belum mengirim hasil cmd/check-engine sehingga penerapan diagnostik tepat versi paket tidak diasumsikan.

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

**Status backend terkini:** alur dasar/fake engine, pendaftaran-verifikasi OTP, sesi /auth/me, daftar/tambah/baca anak akun login, logout serta penolakan token lama telah dilaporkan berhasil. Login ulang setelah logout untuk memastikan anak tetap tersedia, expiry/replay native, isolasi dua akun, frontend dan engine medis asli masih perlu diuji. Tabel end-to-end tetap Belum untuk integrasi seluruh layanan, bukan membatalkan bukti pengujian endpoint yang sudah diterima.
