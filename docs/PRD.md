# PRD — Pantau Tumbuh Kembang Anak

Nov 7, 2026 · @Zenacia

Kami membangun satu alur yang utuh untuk orang tua: catat pengukuran sepulang Posyandu, lihat posisi anak di kurva WHO, terima peringatan dini sebelum stunting terjadi, lalu tahu apa yang harus dilakukan. Bentuk data dan API mengikuti tab kontrak; PRD ini mengunci apa yang dibangun dan bagaimana kami tahu itu selesai.

## Masalah dan pengguna

Masalahnya bukan ketiadaan data, melainkan data yang tidak pernah berubah menjadi tindakan. Anak ditimbang setiap bulan, tetapi perlambatan baru disadari setelah ia stunted.

Prevalensi stunting nasional 19,8% menurut SSGI 2024, dengan target 17,5% pada 2026. Kemenkes menyebut usia 12–24 bulan sebagai tantangan terbesar: stunting relatif terkendali sampai 12 bulan berkat ASI eksklusif, lalu naik saat anak masuk fase MPASI. Sekitar 11% bayi sudah lahir dengan panjang badan di bawah 48 cm ([InfoPublik, 18 Mei 2026](https://infopublik.id/kategori/nasional-sosial-budaya/970585/intervensi-masa-krusial-jadi-fokus-kemenkes-tekan-angka-stunting)). Pengamat gizi juga menyoroti kurangnya pemahaman orang tua tentang MPASI yang sehat ([Asia News Network](https://asianews.network/?p=206272)).

| Masalah | Akibatnya bagi anak |
| --- | --- |
| Orang tua menerima angka berat dan panjang badan tanpa tahu artinya | kondisi yang memburuk terlihat "normal" |
| Sistem baru bereaksi ketika z-score sudah di bawah −2 SD | intervensi datang setelah kerusakan terjadi |
| Orang tua tidak tahu tindakan konkret yang harus diambil | peringatan tidak berubah menjadi perbaikan MPASI atau rujukan |

**Pengguna utama.** Orang tua, umumnya ibu, dengan anak 0–24 bulan dan fokus pada 6–24 bulan. Rutin datang ke Posyandu setiap bulan, memakai ponsel Android kelas menengah, paham angka berat badan tetapi tidak paham z-score atau persentil. Yang ia butuhkan hanya dua jawaban: apakah anak saya baik-baik saja, dan apa yang harus saya lakukan.

**Pengguna kedua** (tidak dibangun dalam MVP): kader Posyandu dan bidan, yang menerima laporan ekspor dari orang tua saat konsultasi.

## Tujuan dan ukuran keberhasilan

Produk ini dinilai pada empat aspek rubrik HIMTEC dengan bobot setara, sehingga setiap tujuan di bawah terikat ke satu aspek dan punya ukuran yang bisa dicek sebelum presentasi.

| Aspek rubrik | Yang kami tunjukkan | Selesai jika |
| --- | --- | --- |
| Fungsionalitas | alur ujung ke ujung: input → status → kurva → tindak lanjut → ekspor | demo berjalan 3 kali berturut-turut tanpa error; semua tes engine lulus; input satu pengukuran ≤ 30 detik |
| Kreativitas desain (UI/UX) | tampilan ponsel lebih dulu, tiga warna tingkat, bahasa awam | semua layar rapi di lebar 360 px; diuji di ponsel sungguhan oleh orang di luar tim |
| Kelengkapan dokumen | kontrak, PRD, diagram, sumber data | laporan memuat bab masalah, solusi, arsitektur, API, dan pengujian, dengan sumber dikutip |
| Kesesuaian tema | pertumbuhan (z-score, peringatan), perkembangan (KPSP), pencegahan (tindak lanjut) | cerita demo menunjukkan peringatan muncul sebelum `lhfa` < −2 |

Untuk nilai seri, presentasi dinilai dari penguasaan materi dan jawaban atas pertanyaan juri. Setiap anggota harus mampu menjawab tentang bagiannya sendiri. Siapkan jawaban untuk empat pertanyaan yang hampir pasti muncul: apa bedanya dengan KMS digital, mengapa orang tua mau memasukkan data, seberapa akurat perhitungannya, dan bagaimana data anak dilindungi.

## Cakupan fitur

Enam usulan fitur dilebur menjadi tiga fitur wajib dan tiga fitur pendukung yang murah karena isinya statis. Nama fitur dari usulan tim tetap dipakai di UI dan slide.

| Fitur | Prioritas | Yang dibangun | Pemilik |
| --- | --- | --- | --- |
| Pantau Pertumbuhan (Growth Tracker) | wajib | input BB, PB/TB, LK; z-score WHO; kurva BB/U, PB/U, BB/PB dengan pita SD | engine: Zena · API: backend · layar: frontend |
| Deteksi Risiko Dini (Early Alert) | wajib | tingkat Aman / Perlu perhatian / Segera periksakan dengan alasan yang bisa dibaca; tampil di aplikasi, bukan notifikasi push | engine: Zena · kalimat: backend · layar: frontend |
| Skrining Perkembangan (Smart Milestone) | wajib | KPSP sesuai jadwal umur, dibingkai sebagai pra-skrining mandiri | engine: Zena · layar: frontend |
| GiziCerdas | sebaiknya | kartu panduan ASI/MPASI per kelompok umur dari Buku KIA; muncul saat peringatan kuning atau merah | isi: Zena · API: backend · layar: frontend |
| Stimulasi Pintar | sebaiknya | kartu stimulasi per umur dan aspek dari pedoman SDIDTK; muncul saat KPSP meragukan | isi: Zena · API: backend · layar: frontend |
| Laporan untuk Posyandu (bagian Posyandu Connect) | sebaiknya | halaman laporan ramah cetak: identitas anak, tabel pengukuran, kurva, status, riwayat KPSP; tombol unduh memakai cetak-ke-PDF peramban | frontend |
| Penjelasan status (LLM lokal) | tambahan, setelah H+7 | ringkasan status dalam bahasa sehari-hari dari output engine | Zena |

**Tidak dibangun:** jadwal imunisasi dan pengingat Posyandu, notifikasi push, login produksi/multi-pengguna produksi, dashboard kader, pembacaan foto Buku KIA (OCR), pembuat menu otomatis, koreksi umur prematur. Semuanya disebut di slide sebagai pengembangan lanjutan.

Kartu GiziCerdas dan Stimulasi disajikan Go lewat `GET /api/v1/guides`, sehingga aturan "frontend tidak menyusun kalimat medis" tetap berlaku (lihat kontrak v0.3).

**Catatan Makan Kemarin** (PRD v0.2; prioritas sebaiknya; dikerjakan H+4 sampai H+7; bagian dari GiziCerdas). Kurva hanya menunjukkan akibat; catatan makan menunjukkan penyebab yang mungkin. Untuk anak 6–23 bulan, orang tua mencentang kelompok pangan yang dimakan anak kemarin, apakah anak menyusu, dan berapa kali ia makan. Engine menghitung tiga indikator WHO/UNICEF (keragaman pangan, frekuensi makan, konsumsi telur atau daging), lalu memunculkan kode alasan pola makan yang memilih kartu GiziCerdas.

- **Layar:** satu layar, delapan kotak centang bergambar ditambah dua angka; selesai dalam 30 detik. Kartu "Isi catatan makan kemarin" muncul di beranda bila belum ada catatan dalam 7 hari terakhir.
- **F-15, kriteria penerimaan:** tanggal bawaan kemarin; hasil tampil di layar status berdampingan dengan alasan pertumbuhan; satu hari yang buruk tidak menaikkan tingkat; pola berulang menaikkan ke kuning.
- **Pemilik:** engine Zena · API backend · layar frontend.

**Peta jalan setelah MVP.** Fase 2: pencatatan porsi memakai Ukuran Rumah Tangga dan Tabel Komposisi Pangan Indonesia, dengan takaran bergambar khusus balita. Fase 3: estimasi porsi dari foto makanan, satu-satunya bagian yang membutuhkan machine learning, dilatih dari data yang terkumpul di fase 2.

**Login dan peran (produksi setelah MVP; OTP dummy lokal tersedia untuk pengujian).** Masuk memakai kode sekali pakai (OTP) yang dikirim ke nomor ponsel atau email pemilik akun. Akses ditolak secara bawaan; setiap endpoint menyebut peran yang diizinkan.

| Peran | Boleh | Tidak boleh |
| --- | --- | --- |
| Orang tua | mengelola anak dan data miliknya sendiri | melihat anak milik akun lain |
| Admin | mendaftarkan dan menonaktifkan akun, memicu pengiriman kode ke pemilik akun | melihat kode autentikasi; melihat data kesehatan anak |
| Peran lain (misalnya kader atau bidan) | ditentukan kemudian; data anak hanya dengan persetujuan orang tua | — |

Kode disimpan dalam bentuk hash, sekali pakai, kedaluwarsa dalam beberapa menit, dan jumlah percobaannya dibatasi. Setiap tindakan admin dicatat di log audit.

**Persiapan yang dikerjakan di MVP:** tabel `users` dengan kolom `role` (`parent`, `admin`), kolom `children.parent_id` yang mengarah ke `users.id`, dan satu orang tua demo di-seed. Semua query anak difilter dengan ID orang tua tersebut. Kontrak API tidak berubah.

**Status implementasi pengujian saat ini.** OTP dummy lokal telah tersedia atas permintaan pengguna: pendaftaran email, kode terminal, verifikasi, sesi bearer, me dan logout. Mode ini opsional melalui AUTH_MODE=otp_dummy dan hanya bind loopback. Default/demo tetap tanpa login. Tiga tabel tambahan otp_codes/auth_sessions/audit_logs ditambahkan oleh migrasi 004; total delapan tabel (lima bisnis, tiga auth). Pengiriman email/SMS nyata dan pengelolaan akun admin tetap roadmap. Spesifikasi API dummy tercatat pada draf kontrak v0.5 dan backend/AUTH_TESTING.md.

## Alur utama

Satu kunjungan Posyandu harus berubah menjadi satu keputusan yang jelas bagi orang tua dalam waktu kurang dari satu menit.

1. **Daftar anak (sekali saja).** Nama, jenis kelamin, tanggal lahir; berat dan panjang lahir opsional.
2. **Catat pengukuran sepulang Posyandu.** Tombol "Catat pengukuran" di beranda membuka formulir dengan tanggal hari ini dan sumber "Posyandu" sudah terisi. Posisi ukur otomatis "berbaring" untuk anak di bawah 24 bulan. Orang tua cukup mengetik berat dan panjang, lalu menyimpan.
3. **Lihat status seketika.** Setelah disimpan, layar langsung menampilkan kartu status: warna tingkat, satu kalimat utama, dan alasan yang bisa dibuka.
4. **Terima tindak lanjut sesuai tingkat.**
   1. Aman: ucapan singkat dan tanggal timbang berikutnya.
   2. Perlu perhatian: kartu GiziCerdas yang relevan dan ajakan mengukur lagi bulan depan.
   3. Segera periksakan: ajakan ke Puskesmas dan tombol "Buka laporan".
5. **Skrining perkembangan saat jatuh tempo.** Kartu "Saatnya skrining perkembangan" muncul di beranda. Sepuluh pertanyaan ya/tidak, satu per layar, lalu hasil. Hasil meragukan memunculkan kartu Stimulasi Pintar.
6. **Lihat kurva kapan saja.** Tab per indikator (BB/U, PB/U, BB/PB) dengan pita SD WHO dan titik pengukuran anak.
7. **Bawa laporan saat konsultasi.** Halaman laporan dapat ditunjukkan di layar atau diunduh sebagai PDF.

## Kebutuhan fungsional

Sebuah fitur dianggap selesai hanya jika kriteria penerimaannya terbukti di demo atau di tes. Tabel ini sekaligus menjadi daftar uji untuk bab pengujian di laporan.

| ID | Kebutuhan | Kriteria penerimaan |
| --- | --- | --- |
| F-01 | Tambah anak | validasi sesuai kontrak; anak di atas 60 bulan ditolak dengan pesan yang jelas |
| F-02 | Catat pengukuran | tanggal, sumber, dan posisi terisi otomatis; isian wajib yang harus diketik hanya berat (dan panjang bila diukur); kesalahan tampil di bawah isian dalam bahasa awam |
| F-03 | Z-score dan klasifikasi | 5 kasus uji sama dengan WHO Anthro, selisih z ≤ 0,01; klasifikasi sesuai Permenkes 2/2020 |
| F-04 | Kurva pertumbuhan | tiga indikator dengan garis −3, −2, median, +2, +3 SD; sumbu umur ditampilkan dalam bulan; titik yang kena flag ditandai berbeda |
| F-05 | Status dan alasan | tingkat = alasan tertinggi; setiap alasan punya judul, kalimat, dan bukti (z dari–ke, tanggal); `PROJECTED_STUNTING` selalu ditulis "diperkirakan" |
| F-06 | Ringkasan di beranda | setiap anak di daftar menampilkan warna tingkat terakhir dan tanggal pengukuran terakhir |
| F-07 | Jadwal KPSP | kuesioner yang muncul sesuai aturan pembulatan umur; jawaban tidak bisa dikirim sebelum 10 butir terisi |
| F-08 | Hasil KPSP | sesuai / meragukan / penyimpangan sesuai skor; layar hasil menyebut ini pra-skrining yang perlu dikonfirmasi di Posyandu |
| F-09 | Kartu GiziCerdas dan Stimulasi | kartu tampil sesuai `related_codes` dan umur anak; setiap kartu menampilkan sumbernya |
| F-10 | Laporan untuk Posyandu | rapi saat dicetak A4; memuat identitas, tabel pengukuran, kurva PB/U, status, riwayat KPSP, tanggal cetak, dan penafian |
| F-11 | Hapus pengukuran | ada konfirmasi; status dan kurva langsung dihitung ulang |
| F-12 | Penafian | setiap layar status menyebut "alat skrining, bukan diagnosis" |
| F-13 | Engine tidak terjangkau | data tetap tersimpan; layar menampilkan "perhitungan sementara tidak tersedia" tanpa merusak halaman |
| F-14 | Penjelasan LLM (tambahan) | hanya memakai output engine; bisa dimatikan lewat variabel lingkungan; bila gagal, bagian itu tidak muncul tanpa pesan error |

## Layar dan kebutuhan non-fungsional

Desain dimulai dari ponsel lebar 360 px. Versi desktop cukup berupa kolom yang sama di tengah layar.

| Layar | Isi utama | Catatan desain |
| --- | --- | --- |
| Beranda | daftar anak dengan warna tingkat terakhir; tombol besar "Catat pengukuran"; kartu KPSP jatuh tempo | tombol utama selalu terjangkau ibu jari |
| Tambah anak | nama, jenis kelamin, tanggal lahir, data lahir opsional | satu layar, tanpa gulir panjang |
| Catat pengukuran | berat, panjang/tinggi, posisi, lingkar kepala opsional | papan ketik angka; isian yang sudah terisi tampak berbeda |
| Status anak | kartu tingkat besar, kalimat utama, alasan yang bisa dibuka, kartu tindak lanjut | angka z-score hanya muncul di "Lihat detail" |
| Kurva | tab BB/U, PB/U, BB/PB; pita SD dan titik anak | legenda dengan kata, bukan hanya warna |
| Riwayat | daftar pengukuran terbaru dulu, hapus dengan konfirmasi | — |
| KPSP | satu pertanyaan per layar, penanda 1/10, tombol Ya/Tidak besar, layar hasil | — |
| Panduan | kartu GiziCerdas dan Stimulasi Pintar, bisa disaring per umur | sumber tampil di setiap kartu |
| Laporan | identitas, tabel, kurva PB/U, status, KPSP, penafian | tata letak A4 saat dicetak |

**Kebutuhan non-fungsional**

- **Bahasa.** Bahasa Indonesia awam. Istilah teknis (z-score, SD) hanya muncul di bagian detail.
- **Warna tingkat.** Hijau, kuning, merah selalu didampingi ikon dan kata, sehingga tetap terbaca oleh pengguna buta warna.
- **Sentuhan dan teks.** Target sentuh minimal 44 px; teks isian minimal 16 px agar ponsel tidak memperbesar halaman sendiri.
- **Kecepatan.** Status tampil kurang dari 1 detik setelah pengukuran disimpan.
- **Sepenuhnya lokal.** Tidak ada ketergantungan pada internet saat demo: huruf, ikon, dan pustaka dibundel, bukan diambil dari CDN.
- **Privasi.** Demo memakai data fiktif; tidak ada data yang dikirim ke layanan luar. Slide menjelaskan rencana persetujuan orang tua sesuai UU Pelindungan Data Pribadi.

## Risiko, batasan, dan pertanyaan terbuka

Risiko terbesar bukan teknis, melainkan angka medis yang salah dan demo yang putus di tengah jalan.

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Ambang atau tabel medis diambil dari ingatan AI | anak salah diklasifikasi; kredibilitas hilang di depan juri | semua angka dari WHO, Permenkes 2/2020, dan SDIDTK; 5 kasus uji dibandingkan dengan WHO Anthro |
| Hotspot putus atau IP laptop Zena berubah saat demo | engine tidak terjangkau, status kosong | `ENGINE_URL` dicek sebelum tampil; mode satu laptop via `docker-compose` diuji sebelum H+9; video demo cadangan |
| Cakupan melebar setelah H+9 | fitur setengah jadi, kestabilan turun | hanya fitur di tabel cakupan yang dibangun; setelah H+9 hanya perbaikan bug |
| Integrasi baru dicoba di akhir | layanan tidak saling cocok | setiap endpoint diintegrasikan begitu selesai, bukan menunggu semuanya jadi |
| Laptop Zena kepanasan (GTX 1060 Max-Q) | respons lambat saat demo | LLM mati secara bawaan; dinyalakan hanya untuk bagian demo yang membutuhkannya |
| Isi kartu panduan dikarang | saran gizi menyesatkan | disalin dari Buku KIA dan SDIDTK, sumber tercantum di setiap kartu |
| KPSP diisi orang tua sendiri | hasil bias | dibingkai sebagai pra-skrining yang dikonfirmasi di Posyandu |

**Batasan yang diakui.** Pengukuran oleh orang tua kurang akurat dibanding alat Posyandu. Standar WHO yang dipakai hanya untuk umur 0–60 bulan. Umur prematur tidak dikoreksi. Aplikasi tidak menggantikan tenaga kesehatan.

**Pertanyaan terbuka**

- [ ] Nama produk
- [ ] Apakah panitia mewajibkan pencantuman penggunaan AI dalam pengembangan
- [ ] Apakah pedoman SDIDTK mengizinkan KPSP diisi orang tua sendiri, atau hanya oleh petugas terlatih
- [ ] Apakah panitia menyediakan templat laporan dan proposal
- [ ] Jumlah kartu GiziCerdas dan Stimulasi yang realistis disiapkan sebelum H+9

## Skema database

Lima tabel PostgreSQL, semuanya dimiliki Go. Satu orang tua memiliki banyak anak; setiap anak memiliki banyak pengukuran, hasil KPSP, dan catatan makan. Hasil evaluasi engine (z-score, tingkat, kode alasan) tidak disimpan, melainkan dihitung ulang setiap kali diminta.

DDL di bawah adalah acuan untuk migrasi pertama. Backend boleh menyesuaikan tipe, asal bentuk JSON di kontrak tidak berubah. Pilihan nilai memakai `text` + `CHECK`, bukan `ENUM`, supaya menambah nilai tidak perlu migrasi tipe.

```sql
CREATE TABLE users (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name        text NOT NULL,
  phone       text UNIQUE,
  email       text UNIQUE,
  role        text NOT NULL CHECK (role IN ('parent', 'admin')),
  is_active   boolean NOT NULL DEFAULT true,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE children (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id        uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name             text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 60),
  sex              text NOT NULL CHECK (sex IN ('male', 'female')),
  birth_date       date NOT NULL,
  birth_weight_kg  numeric(3,2) CHECK (birth_weight_kg BETWEEN 0.5 AND 6.0),
  birth_length_cm  numeric(4,1) CHECK (birth_length_cm BETWEEN 30 AND 60),
  is_preterm       boolean NOT NULL DEFAULT false,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE measurements (
  id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id               uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  measured_at            date NOT NULL,
  weight_kg              numeric(4,2) NOT NULL CHECK (weight_kg BETWEEN 0.5 AND 40),
  length_height_cm       numeric(4,1) CHECK (length_height_cm BETWEEN 40 AND 130),
  position               text CHECK (position IN ('recumbent', 'standing')),
  head_circumference_cm  numeric(4,1) CHECK (head_circumference_cm BETWEEN 30 AND 60),
  source                 text NOT NULL CHECK (source IN ('posyandu', 'puskesmas', 'home')),
  note                   text CHECK (char_length(note) <= 200),
  created_at             timestamptz NOT NULL DEFAULT now(),
  UNIQUE (child_id, measured_at),
  CHECK (length_height_cm IS NULL OR position IS NOT NULL)
);

CREATE TABLE kpsp_results (
  id                        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id                  uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  questionnaire_age_months  smallint NOT NULL
    CHECK (questionnaire_age_months IN (3,6,9,12,15,18,21,24,30,36,42,48,54,60)),
  answered_at               date NOT NULL,
  answers                   jsonb NOT NULL,  -- [{"item_no":1,"answer":true}, ...], tepat 10 butir
  yes_count                 smallint NOT NULL CHECK (yes_count BETWEEN 0 AND 10),
  result                    text NOT NULL CHECK (result IN ('sesuai', 'meragukan', 'penyimpangan')),
  created_at                timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON kpsp_results (child_id, answered_at);

CREATE TABLE food_recalls (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  child_id         uuid NOT NULL REFERENCES children(id) ON DELETE CASCADE,
  recall_date      date NOT NULL,
  breastfed        boolean NOT NULL,
  food_groups      text[] NOT NULL DEFAULT '{}',
  meal_count       smallint NOT NULL CHECK (meal_count BETWEEN 0 AND 10),
  milk_feed_count  smallint CHECK (milk_feed_count BETWEEN 0 AND 10),
  created_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (child_id, recall_date)
);
```

Aturan yang tidak bisa dijaga oleh `CHECK` dan tetap divalidasi Go: tanggal tidak di masa depan, `measured_at` ≥ `birth_date`, umur anak ≤ 60 bulan, umur 6–23 bulan untuk catatan makan, dan isi `food_groups` hanya dari tujuh nilai di kontrak. Seed berisi satu baris `users` berperan `parent` sebagai orang tua demo.

**Setelah MVP (login) hanya menambah tabel, tidak mengubah yang ada:** `otp_codes` (pemilik, hash kode, kedaluwarsa, jumlah percobaan, waktu dipakai), `audit_logs` (pelaku, tindakan, akun sasaran, waktu), dan nanti tabel persetujuan orang tua bila peran kader atau bidan ditambahkan.

## Struktur folder

Setiap folder ujung berisi `.gitkeep` agar tetap ter-commit walau masih kosong; hapus `.gitkeep` begitu folder itu berisi berkas pertama. Setiap orang hanya mengisi folder miliknya (lihat AGENTS.md).

```text
tumbuh-kembang/
├── README.md              pintu masuk repo
├── AGENTS.md              aturan untuk manusia dan semua asisten AI
├── CLAUDE.md              merujuk ke AGENTS.md
├── .env.example
├── .gitignore
├── docs/                  semua dokumen proyek lainnya
│   ├── CONTRACT.md        protokol komunikasi: data, API publik, API engine
│   ├── PRD.md             apa yang dibangun dan kapan selesai
│   ├── CHANGELOG.md       setiap perubahan yang memengaruhi orang lain
│   └── HANDOFF.md         serah terima per peran + status integrasi
├── engine/                Python FastAPI · Zena
│   ├── app/
│   │   ├── api/           router /engine/v1
│   │   ├── core/          z-score, klasifikasi, peringatan, KPSP, IYCF
│   │   └── schemas/       model Pydantic sesuai kontrak
│   ├── data/
│   │   ├── who/           tabel LMS WHO
│   │   ├── kpsp/          butir KPSP (JSON)
│   │   └── iycf/          kelompok pangan dan ambang IYCF
│   └── tests/             pytest
├── backend/               Go · backend
│   ├── cmd/server/        main.go
│   ├── internal/
│   │   ├── handler/       HTTP /api/v1
│   │   ├── service/       logika bisnis
│   │   ├── repository/    akses PostgreSQL
│   │   ├── engineclient/  klien HTTP ke engine (ENGINE_URL)
│   │   └── model/         struct sesuai kontrak
│   ├── migrations/        SQL skema
│   └── data/              messages.id.json, guides.id.json, seed
└── frontend/              Vue 3 + Vite + TS + shadcn-vue · desain + frontend
    ├── public/
    └── src/
        ├── api/           klien HTTP (VITE_API_URL)
        ├── assets/
        │   ├── fonts/     dibundel, tanpa CDN
        │   └── images/
        ├── components/
        │   ├── ui/        komponen shadcn-vue
        │   ├── growth/    kurva, kartu status
        │   ├── kpsp/
        │   └── diet/      Catatan Makan Kemarin
        ├── composables/
        ├── lib/
        ├── router/
        ├── types/         tipe TS sesuai kontrak
        └── views/         satu berkas per layar
```
