# Kontrak Tim — Pantau Tumbuh Kembang Anak (HIMTEC 2026)

Nov 7, 2026 · @Zenacia

## Tujuan dan aturan main

Kontrak ini mengikat bentuk data dan API antara frontend, backend Go, dan engine Python. Kode yang tidak cocok dengan kontrak dianggap salah, bukan kontraknya. Versi saat ini (v0.7 menayangkan KPSP 15/18/24 berlabel dan memilih tabel BB/PB atau BB/TB di Go, lihat "Penegasan v0.7"; v0.6 menetapkan batas umur pengukuran 1826 hari dan menuntaskan tiga isu terbuka, lihat "Penegasan v0.6"; v0.5 memperjelas umur/jadwal KPSP sesuai keputusan pengguna; v0.4 menambah Catatan Makan Kemarin; v0.3 jaringan demo dan kartu panduan): **v0.7 (draf)**, dibekukan menjadi v1.0 paling lambat satu jam setelah mulai.

**Masalah.** Orang tua balita 6–24 bulan menerima angka penimbangan Posyandu setiap bulan, tetapi tidak memahami artinya. Perlambatan pertumbuhan baru ketahuan setelah anak melewati −2 SD, ketika jendela intervensi hampir tertutup. Kemenkes menyebut usia 12–24 bulan sebagai tantangan terbesar, saat anak masuk fase MPASI ([InfoPublik, Mei 2026](https://infopublik.id/kategori/nasional-sosial-budaya/970585/intervensi-masa-krusial-jadi-fokus-kemenkes-tekan-angka-stunting)). Prevalensi nasional 19,8% (SSGI 2024), target 17,5% pada 2026.

**Solusi.** Aplikasi membaca lintasan pertumbuhan anak dari pengukuran rutin, memberi peringatan dini sebelum stunting terjadi, menjadwalkan skrining perkembangan (KPSP), lalu memberi tahu orang tua apa yang harus dilakukan. Aplikasi ini alat skrining, bukan diagnosis; setiap peringatan merah merujuk ke Posyandu/Puskesmas.

**Aturan perubahan kontrak**

1. Pemilik kontrak: Zena. Perubahan diusulkan di grup, disetujui Zena, lalu ditulis di dokumen ini dengan versi naik.
2. Menambah field opsional = tidak merusak, boleh langsung. Mengganti nama, mengubah tipe, atau menghapus field = merusak, harus disepakati bertiga.
3. Setiap anggota menempelkan versi terbaru kontrak di awal sesi asisten AI-nya (GPT atau Claude). Asisten tidak boleh mengarang field, endpoint, atau nilai enum di luar kontrak.
4. Angka medis (tabel LMS WHO, butir KPSP, ambang klasifikasi) hanya diambil dari sumber resmi, tidak pernah dari ingatan AI, lalu diuji dengan kasus yang hasilnya sudah diketahui.

## Arsitektur dan pembagian tugas

Tiga layanan bekerja paralel sejak menit pertama karena masing-masing hanya bergantung pada kontrak, bukan pada kode orang lain.

```text
Frontend (Vue, :5173) ──HTTP──> Backend Go (:8080/api/v1) ──HTTP──> Engine Python (:8001/engine/v1)
                                       │                                   │
                                  PostgreSQL (:5432)              tabel WHO, KPSP, IYCF
```

Go adalah satu-satunya pintu: frontend tidak pernah memanggil engine, engine tidak pernah menyentuh database.

| Peran | Memegang | Tidak menyentuh |
| --- | --- | --- |
| Full stack + AI engine (Zena) | engine Python, pemilik kontrak, integrasi, data demo | — |
| Desain + frontend | Vue 3 + Vite + TypeScript + Tailwind + shadcn-vue, grafik kurva (vue-echarts), alur layar | logika atau kalimat medis |
| Backend | Go API, PostgreSQL, validasi, `messages.id.json`, seed data | rumus z-score dan ambang |

Sebelum Go siap, frontend memakai contoh JSON dari kontrak ini sebagai data tiruan. Sebelum engine siap, Go mengembalikan respons evaluasi tiruan dengan bentuk yang sama.

Struktur folder repo lengkap ada di PRD, bagian "Struktur folder". Kontrak ini disimpan di repo sebagai `docs/CONTRACT.md`.

**Jaringan demo (v0.2).** Engine, dan LLM opsional, berjalan di laptop Zena. Go, PostgreSQL, dan frontend berjalan di laptop teman. Semua laptop tersambung ke hotspot ponsel tim, bukan Wi-Fi venue.

- Go membaca alamat engine dari variabel lingkungan `ENGINE_URL` (misalnya `http://192.168.43.20:8001/engine/v1`), tidak pernah di-hardcode.
- Engine bind ke `0.0.0.0:8001`; port 8001 dibuka di firewall laptop Zena. Cek ulang IP laptop Zena setiap kali hotspot tersambung ulang.
- Laptop Zena: mode sleep dimatikan, charger terpasang selama demo.
- Rencana cadangan: `docker-compose` mampu menjalankan ketiga layanan di satu laptop dengan `ENGINE_URL=http://engine:8001/engine/v1`. Uji sekali sebelum H+9.

## Konvensi umum

Semua JSON memakai snake\_case, satuan metrik, tanggal ISO, dan satu bentuk amplop response. Frontend tidak pernah menyusun kalimat medis sendiri; semua teks untuk orang tua datang dari backend.

| Hal | Aturan | Contoh |
| --- | --- | --- |
| Nama field | snake\_case | `birth_date` |
| ID | UUID v4, string | `"9b1d…"` |
| Tanggal | `YYYY-MM-DD`, tanpa jam | `"2025-03-01"` |
| Timestamp | RFC 3339 dengan offset | `"2026-11-07T09:00:00+07:00"` |
| Berat | kg, desimal | `9.4` |
| Panjang/tinggi, lingkar kepala | cm, 1 desimal | `74.5` |
| Umur | dihitung engine dalam hari dari `birth_date` dan `measured_at`; tampilan bulan = hari ÷ 30,4375, 1 desimal | `age_days: 365`, `age_months: 12.0` |
| Z-score | desimal, 2 angka di belakang koma | `-2.13` |
| Jenis kelamin | `"male"` atau `"female"` | `"female"` |
| Nilai enum | lower\_snake\_case | `"recumbent"` |
| Kode alasan & error | UPPER\_SNAKE\_CASE | `"WEIGHT_NOT_GAINING"` |
| Bahasa teks pengguna | Bahasa Indonesia | — |

**Amplop response** (berlaku untuk API Go dan engine):

```json
{ "data": { }, "error": null }
```

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "measured_at tidak boleh sebelum birth_date",
    "fields": { "measured_at": "before_birth_date" }
  }
}
```

| Kode error | HTTP | Kapan |
| --- | --- | --- |
| `VALIDATION_ERROR` | 422 | input melanggar aturan validasi |
| `NOT_FOUND` | 404 | anak/pengukuran tidak ada |
| `ENGINE_UNAVAILABLE` | 503 | Go gagal memanggil engine Python |
| `INTERNAL` | 500 | selain di atas |

## Model data

Go memiliki dan menyimpan tiga entitas ini. Engine Python tidak pernah menyentuh database; hasil evaluasi pertumbuhan dihitung ulang setiap kali diminta, tidak disimpan.

**Child** (anak)

| Field | Tipe | Wajib | Aturan |
| --- | --- | --- | --- |
| `id` | uuid | otomatis | — |
| `name` | string | ya | 1–60 karakter |
| `sex` | enum `male`/`female` | ya | — |
| `birth_date` | date | ya | tidak di masa depan; umur saat didaftarkan ≤ 60 bulan |
| `birth_weight_kg` | number | tidak | 0,5–6,0 |
| `birth_length_cm` | number | tidak | 30–60 |
| `is_preterm` | boolean | tidak | default `false`; hanya ditampilkan sebagai catatan, koreksi umur prematur di luar cakupan |
| `created_at` | timestamp | otomatis | — |

**Measurement** (pengukuran)

| Field | Tipe | Wajib | Aturan |
| --- | --- | --- | --- |
| `id` | uuid | otomatis | — |
| `child_id` | uuid | ya | anak harus ada |
| `measured_at` | date | ya | ≥ `birth_date`, ≤ hari ini, umur ≤ 1826 hari (v0.6); satu pengukuran per anak per tanggal |
| `weight_kg` | number | ya | 0,5–40 |
| `length_height_cm` | number | tidak | 40–130 |
| `position` | enum `recumbent`/`standing` | ya jika `length_height_cm` diisi | `recumbent` = berbaring (panjang badan), `standing` = berdiri (tinggi badan) |
| `head_circumference_cm` | number | tidak | 30–60 |
| `source` | enum `posyandu`/`puskesmas`/`home` | ya | dipakai untuk peringatan kualitas data |
| `note` | string | tidak | ≤ 200 karakter |
| `created_at` | timestamp | otomatis | — |

**KpspResult** (hasil skrining perkembangan)

| Field | Tipe | Wajib | Aturan |
| --- | --- | --- | --- |
| `id` | uuid | otomatis | — |
| `child_id` | uuid | ya | — |
| `questionnaire_age_months` | integer | ya | salah satu umur jadwal KPSP (lihat aturan medis) |
| `answered_at` | date | ya | ≤ hari ini |
| `answers` | array `{item_no, answer}` | ya | `item_no` 1–10, `answer` boolean; tepat 10 butir |
| `yes_count` | integer | dihitung engine | — |
| `result` | enum `sesuai`/`meragukan`/`penyimpangan` | dihitung engine | — |
| `created_at` | timestamp | otomatis | — |

**FoodRecall** (Catatan Makan Kemarin, v0.4) — hanya untuk anak umur 6–23 bulan

| Field | Tipe | Wajib | Aturan |
| --- | --- | --- | --- |
| `id` | uuid | otomatis | — |
| `child_id` | uuid | ya | umur anak pada `recall_date` 6–23 bulan |
| `recall_date` | date | ya | hari yang diingat, bawaan = kemarin; ≤ hari ini; satu catatan per anak per tanggal |
| `breastfed` | boolean | ya | anak minum ASI pada hari itu (dihitung sebagai kelompok pangan ke-8) |
| `food_groups` | array enum | ya | kelompok pangan yang dimakan, boleh kosong |
| `meal_count` | integer | ya | 0–10; berapa kali makan makanan padat, semi-padat, atau lunak |
| `milk_feed_count` | integer | tidak | 0–10; minum susu selain ASI; dipakai bila anak tidak menyusu |
| `created_at` | timestamp | otomatis | — |

Nilai `food_groups`: `grains_roots_tubers` (serealia, umbi), `pulses_nuts_seeds` (kacang-kacangan, biji), `dairy` (susu dan olahannya), `flesh_foods` (daging, ikan, unggas, jeroan), `eggs` (telur), `vita_fruits_veg` (buah dan sayur kaya vitamin A), `other_fruits_veg` (buah dan sayur lain).

## Aturan medis

Engine menghitung z-score dengan Standar Pertumbuhan Anak WHO 2006 (0–60 bulan, metode LMS) dan mengklasifikasikannya sesuai Permenkes No. 2 Tahun 2020 tentang Standar Antropometri Anak. Ambang di bawah ini ditulis dari ingatan dan **wajib dicocokkan dengan dokumen aslinya** sebelum kontrak dibekukan.

**Indikator**

| Kode | Indikator | Dipakai untuk |
| --- | --- | --- |
| `wfa` | BB/U (berat menurut umur) | berat kurang, tren berat |
| `lhfa` | PB/U atau TB/U (panjang/tinggi menurut umur) | stunting |
| `wfl` / `wfh` | BB/PB (< 24 bulan) atau BB/TB (≥ 24 bulan) | gizi kurang/buruk (wasting) |
| `hcfa` | LK/U (lingkar kepala menurut umur) | opsional, hanya ditampilkan |

**Rumus LMS** (L, M, S dibaca dari tabel WHO per hari umur dan jenis kelamin):

```latex
z = \frac{(X/M)^{L} - 1}{L \cdot S} \quad (L \neq 0), \qquad z = \frac{\ln(X/M)}{S} \quad (L = 0)
```

Untuk indikator berbasis berat (`wfa`, `wfl`, `wfh`), z di luar ±3 memakai penyesuaian WHO (restricted LMS). Pustaka seperti pygrowup sudah menanganinya; jangan menulis ulang dari nol.

**Koreksi posisi ukur.** Umur < 731 hari tetapi diukur berdiri: tambah 0,7 cm. Umur ≥ 731 hari tetapi diukur berbaring: kurangi 0,7 cm. Nilai terkoreksi yang dipakai menghitung `lhfa`, `wfl`, dan `wfh`.

**Klasifikasi (Permenkes 2/2020)**

| Indikator | < −3 SD | −3 s.d. < −2 SD | −2 s.d. +1 SD | > +1 s.d. +2 SD | > +2 s.d. +3 SD | > +3 SD |
| --- | --- | --- | --- | --- | --- | --- |
| BB/U | berat badan sangat kurang | berat badan kurang | normal | risiko berat badan lebih | risiko berat badan lebih | risiko berat badan lebih |
| PB/U, TB/U | sangat pendek | pendek | normal | normal | normal | tinggi |
| BB/PB, BB/TB | gizi buruk | gizi kurang | gizi baik | berisiko gizi lebih | gizi lebih | obesitas |

Nilai enum klasifikasi di JSON: `severely_underweight`, `underweight`, `normal`, `overweight_risk` (BB/U); `severely_stunted`, `stunted`, `normal`, `tall` (PB/U); `severely_wasted`, `wasted`, `normal`, `overweight_risk`, `overweight`, `obese` (BB/PB).

**Nilai tak masuk akal (flag WHO).** `lhfa` < −6 atau > +6; `wfa` < −6 atau > +5; `wfl`/`wfh` < −5 atau > +5. Pengukuran itu tidak diklasifikasi dan tidak dipakai untuk tren; engine mengembalikan `IMPLAUSIBLE_VALUE` dan meminta pengukuran ulang.

**KPSP**

1. Jadwal umur kuesioner: 3, 6, 9, 12, 15, 18, 21, 24, 30, 36, 42, 48, 54, 60 bulan.
2. Pembulatan umur: sisa **16 hari atau lebih (≥16)** dibulatkan ke atas satu bulan, sesuai klarifikasi pengguna 7 November 2026. Komponen umur dihitung dengan pengurangan tahun/bulan/hari; bila meminjam pada kolom hari, satu bulan = 30 hari dan satu tahun = 12 bulan, mengacu pedoman SDIDTK 2022 halaman 117. Ini berbeda dari umur tampilan pertumbuhan (hari ÷ 30,4375). Koreksi prematur tetap di luar cakupan.
3. Umur di luar jadwal memakai kuesioner umur jadwal terdekat yang lebih muda.
4. Skor dari jumlah jawaban "Ya": 9–10 = `sesuai`; 7–8 = `meragukan` (stimulasi, ulangi 2 minggu lagi); ≤ 6 = `penyimpangan` (rujuk).
5. Butir pertanyaan diketik dari Buku Pedoman SDIDTK Kemenkes, disimpan engine sebagai JSON statis.

**Penegasan KPSP v0.5 (draf).** Sumber yang dipilih tim: Pedoman Pelaksanaan SDIDTK revisi 23 Agustus 2022, berdasarkan Markdown unggahan pengguna. Daftar 14 formulir 3–60 bulan di atas tetap cakupan proyek; jangan menyamakannya dengan seluruh jadwal kunjungan rutin dalam pedoman.

- `next_kpsp`: sebelum umur bulat 3 bulan mengembalikan formulir 3 bulan dengan `due=false`. Bila belum ada hasil sesuai untuk formulir yang cocok dengan umur, `due=true`. Hasil sesuai untuk formulir umur saat ini memindahkan tampilan ke formulir jadwal berikutnya dengan `due=false` sampai umur tersebut tercapai; pada formulir terakhir tetap 60/`false`.
- Hasil terakhir meragukan mengulang formulir yang sama setelah ≥14 hari, termasuk bila batas umur formulir berikutnya telah terlewati; mengacu evaluasi intervensi halaman 119. Hasil terakhir penyimpangan tidak menjadwalkan skrining mandiri ulang secara otomatis (`due=false`); alasan rujukan tetap aktif. Riwayat terbaru ditentukan oleh tanggal, umur kuesioner terbesar sebagai pemecah tanggal seri.
- Umur bulat di luar 0–60 ditolak oleh core KPSP. Batas umur pengukuran ditetapkan di v0.6 (1826 hari).
- Bentuk JSON skor tetap `{questionnaire_age_months, answers:[{item_no, answer}]}`, cocok dengan client Go; respons skor `{yes_count, result}` di dalam amplop umum.
- Bank yang hanya ditranskripsi dari Markdown dan belum memiliki gambar/rubrik serta verifikasi klinis tidak boleh disajikan sebagai kuesioner siap pakai. Format referensi aset gambar pada API belum ditetapkan; jangan menambah field baru sepihak. Sampai lengkap, endpoint questionnaire tetap belum diaktifkan. *(Diganti sebagian oleh v0.7: hanya formulir 15, 18, 24 yang tayang, berlabel.)*

**Indikator pemberian makan** (WHO/UNICEF IYCF 2021, umur 6–23 bulan, v0.4). Definisi MDD, MMF dan EFF sudah dibandingkan dengan WHO/UNICEF 2021 pada Patch 08; perbedaan batas umur harian proyek dicatat di bawah dan belum diubah sepihak.

| Indikator | Kode | Terpenuhi jika |
| --- | --- | --- |
| Keragaman pangan minimum | `mdd` | ≥ 5 dari 8 kelompok (ASI dihitung satu kelompok) |
| Frekuensi makan minimum | `mmf` | menyusu: ≥ 2 kali makan (6–8 bulan) atau ≥ 3 kali (9–23 bulan); tidak menyusu: ≥ 4 kali makan + susu, minimal 1 di antaranya makan |
| Konsumsi telur atau daging | `eff` | `eggs` atau `flesh_foods` ada |

**Penegasan implementasi IYCF (Patch 08, kontrak v0.5 draf).**
- Definisi: [WHO/UNICEF 2021](https://www.who.int/publications/i/item/9789240018389), [MMF WHO](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/minimum-meal-frequency-6-23-months), dan [indikator UNICEF](https://data.unicef.org/topic/nutrition/diets/).
- Umur pada recall_date tetap mengikuti skema proyek: 6 ≤ hari/30,4375 <24 (hari 183–730). Rumus survei WHO memakai 183 ≤ hari <730; ada selisih satu hari di batas atas, sehingga jangan mengklaim kelayakan umur persis sama dengan WHO. Perhitungan MMF memakai umur pada tanggal recall, bukan as_of.
- Hitung kelompok pangan unik; ASI menambah satu. `milk_feed_count=null` dihitung nol untuk MMF sesuai konvensi frekuensi hilang, bukan bukti pasti tidak ada konsumsi. Nilai itu tidak otomatis mencentang dairy. MMF bukan indikator minimum susu atau minimum acceptable diet; EFF khusus eggs/flesh_foods, bukan dairy.
- Jendela evaluasi 14 tanggal adalah as_of−13 sampai as_of, selaras query backend. Tujuh tanggal untuk NO_RECENT_FOOD_RECALL adalah as_of−6 sampai as_of. Gunakan maksimal tiga catatan terbaru; dua kegagalan yang tersedia sudah cukup untuk yellow, tanpa harus menunggu catatan ketiga. Kegagalan tunggal hanya info bila terbaru gagal. Pola yellow dapat tetap ada setelah satu hari terbaru membaik.
- `diet` memakai catatan terbaru dalam jendela, atau null bila tidak ada; di luar umur sasaran pada as_of tidak ada evaluasi/reasons diet aktif. Data historis tidak dihapus. Catatan berumur 7–13 hari dapat menghasilkan pola dan NO_RECENT_FOOD_RECALL bersamaan.
- Tingkat akhir tetap alasan tertinggi dari pertumbuhan/KPSP-history dan diet. Format API tidak berubah; ketiga indikator bukan diagnosis, penilaian porsi/energi atau bukti sebab stunting.

**Verifikasi sebelum v1.0**

- [ ] Ambil tabel LMS WHO (wfa, lhfa, wfl, wfh, hcfa; laki-laki dan perempuan; per hari) atau pasang pygrowup
- [ ] Cocokkan tabel klasifikasi di atas dengan teks Permenkes No. 2 Tahun 2020
- [ ] Ketik butir KPSP per umur dari pedoman SDIDTK
- [ ] Uji engine dengan minimal 5 kasus yang hasilnya dibandingkan dengan WHO Anthro

* [x] Bandingkan definisi MDD/MMF/EFF dengan WHO/UNICEF IYCF 2021; selisih kelayakan umur dicatat, belum dinyatakan identik

## Logika peringatan dini

Tingkat peringatan anak = tingkat tertinggi dari semua kode alasan yang aktif pada pengukuran terakhir: `red` > `yellow` > `green`. Engine hanya mengembalikan kode dan angkanya; Go menerjemahkan kode menjadi kalimat bahasa Indonesia dari satu file statis `messages.id.json`.

| Kode alasan | Tingkat | Pemicu | Tindakan untuk orang tua |
| --- | --- | --- | --- |
| `SEVERELY_STUNTED` | red | `lhfa` < −3 | ke Puskesmas minggu ini |
| `STUNTED` | red | −3 ≤ `lhfa` < −2 | ke Puskesmas, bawa riwayat pengukuran |
| `SEVERELY_WASTED` | red | `wfl`/`wfh` < −3 | ke Puskesmas segera |
| `WASTED` | red | −3 ≤ `wfl`/`wfh` < −2 | ke Puskesmas minggu ini |
| `SEVERELY_UNDERWEIGHT` | red | `wfa` < −3 | ke Puskesmas minggu ini |
| `WEIGHT_NOT_GAINING_2X` | red | berat tidak naik dua bulan berturut-turut (2T) | rujuk lewat Posyandu |
| `KPSP_DEVIATION` | red | hasil KPSP `penyimpangan` | rujuk untuk pemeriksaan perkembangan |
| `PROJECTED_STUNTING` | yellow | `lhfa` saat ini ≥ −2, tetapi garis tren dari ≥ 3 titik dalam 6 bulan terakhir menembus −2 dalam 90 hari | perbaiki MPASI (protein hewani), ukur ulang bulan depan |
| `CROSSING_DOWN` | yellow | `wfa` atau `lhfa` turun ≥ 0,67 SD dibanding pengukuran 60–120 hari sebelumnya | perbaiki MPASI, ukur ulang bulan depan |
| `WEIGHT_NOT_GAINING` | yellow | kenaikan berat bulan ini di bawah Kenaikan Berat Minimal (KBM) menurut umur (1T) | perbaiki MPASI, timbang lagi bulan depan |
| `UNDERWEIGHT` | yellow | −3 ≤ `wfa` < −2 | konsultasi ke kader/bidan |
| `OVERWEIGHT` | yellow | `wfl`/`wfh` > +2 | konsultasi ke kader/bidan |
| `KPSP_DOUBTFUL` | yellow | hasil KPSP `meragukan` | stimulasi di rumah, ulangi KPSP 2 minggu lagi |
| `IMPLAUSIBLE_VALUE` | info | nilai kena flag WHO | ukur ulang; titik ini diabaikan dari tren |
| `HOME_MEASUREMENT` | info | `source` = `home` | hasil kurang akurat, konfirmasi di Posyandu |
| `NO_RECENT_LENGTH` | info | tidak ada panjang/tinggi dalam 90 hari terakhir | status stunting tidak dapat dinilai |

Kode `info` tidak menaikkan tingkat. Bila tidak ada kode `yellow` atau `red`, tingkatnya `green`. Label tampilan: `green` = "Aman", `yellow` = "Perlu perhatian", `red` = "Segera periksakan".

Tiga catatan desain:

- `PROJECTED_STUNTING` adalah perkiraan statistik, bukan diagnosis; UI wajib menulisnya sebagai "diperkirakan".
- Tabel KBM diambil dari Buku KIA. Sebelum tabel itu diketik, pakai aturan sementara: kenaikan ≤ 0 g = tidak naik.
- Tren hanya memakai pengukuran yang lolos validasi dan tidak kena flag.

**Kode alasan pola makan (v0.4).** Dinilai dari catatan makan 14 hari terakhir. Satu hari yang buruk hanya `info`; pola yang berulang menjadi `yellow`. Tingkat anak tetap mengikuti aturan alasan tertinggi.

| Kode alasan | Tingkat | Pemicu | Tindakan untuk orang tua |
| --- | --- | --- | --- |
| `NO_ANIMAL_SOURCE_FOOD` | yellow / info | `eff` gagal di ≥ 2 dari 3 catatan terakhir (yellow), atau hanya di catatan terakhir (info) | kartu protein hewani |
| `LOW_DIET_DIVERSITY` | yellow / info | aturan yang sama untuk `mdd` | kartu keragaman MPASI |
| `LOW_MEAL_FREQUENCY` | yellow / info | aturan yang sama untuk `mmf` | kartu frekuensi makan |
| `NO_RECENT_FOOD_RECALL` | info | anak 6–23 bulan tanpa catatan makan dalam 7 hari terakhir | ajakan mengisi Catatan Makan Kemarin |

Bila kode pola makan muncul bersamaan dengan `CROSSING_DOWN`, `WEIGHT_NOT_GAINING`, atau `PROJECTED_STUNTING`, layar status menampilkan keduanya berdampingan. Itulah cerita demo: berat tidak naik, dan penyebab yang mungkin terlihat.

## API publik (frontend ↔ Go)

Frontend hanya berbicara dengan Go di `http://localhost:8080/api/v1`. MVP tanpa login: satu akun orang tua demo di-seed. Go mengizinkan CORS dari `http://localhost:5173`.

| Metode | Path | Fungsi |
| --- | --- | --- |
| GET | `/children` | daftar anak (bentuk `Child`); tingkat peringatan per anak diambil dari `/children/{id}/status` (v0.6) |
| POST | `/children` | tambah anak |
| GET | `/children/{id}` | detail anak |
| GET | `/children/{id}/status` | evaluasi terkini: tingkat, z-score, kode alasan, KPSP berikutnya |
| GET | `/children/{id}/measurements` | riwayat pengukuran, terbaru dulu |
| POST | `/children/{id}/measurements` | tambah pengukuran; response = pengukuran + status baru |
| DELETE | `/children/{id}/measurements/{mid}` | hapus pengukuran salah input |
| GET | `/children/{id}/growth?indicator=lhfa` | titik kurva anak + garis acuan WHO; `indicator` = `wfa`, `lhfa`, `wfl_wfh`, `hcfa` |
| GET | `/children/{id}/kpsp/next` | kuesioner KPSP yang jatuh tempo beserta butirnya |
| POST | `/children/{id}/kpsp` | kirim jawaban KPSP; response = `KpspResult` |
| GET | `/children/{id}/kpsp` | riwayat KPSP |

Contoh di bawah menunjukkan bentuk, bukan hasil hitungan; angkanya karangan.

**GET `/children/{id}/status`**

```json
{
  "data": {
    "child_id": "9b1d0c2e-0000-4000-8000-000000000001",
    "as_of": "2026-01-15",
    "age_days": 320,
    "age_months": 10.5,
    "level": "yellow",
    "level_label": "Perlu perhatian",
    "latest": {
      "measurement_id": "…",
      "measured_at": "2026-01-15",
      "weight_kg": 8.1,
      "length_height_cm": 70.2,
      "position": "recumbent",
      "z": { "wfa": -1.42, "lhfa": -1.71, "wfl_wfh": -0.62, "hcfa": null },
      "classification": { "wfa": "normal", "lhfa": "normal", "wfl_wfh": "normal" }
    },
    "reasons": [
      {
        "code": "CROSSING_DOWN",
        "level": "yellow",
        "title": "Berat badan turun dari jalurnya",
        "message": "Dalam dua bulan terakhir berat badan Anisa tumbuh lebih lambat dari seharusnya…",
        "evidence": { "indicator": "wfa", "from_z": -0.71, "to_z": -1.42, "from_date": "2025-11-14", "to_date": "2026-01-15" }
      }
    ],
    "next_kpsp": { "questionnaire_age_months": 9, "due": true }
  },
  "error": null
}
```

**POST `/children/{id}/measurements`**

```json
{
  "measured_at": "2026-01-15",
  "weight_kg": 8.1,
  "length_height_cm": 70.2,
  "position": "recumbent",
  "head_circumference_cm": null,
  "source": "posyandu",
  "note": null
}
```

Response 201: `{ "data": { "measurement": { … }, "status": { …bentuk sama dengan /status… } }, "error": null }`.

**GET `/children/{id}/growth?indicator=lhfa`**

```json
{
  "data": {
    "indicator": "lhfa",
    "sex": "female",
    "x_unit": "days",
    "points": [
      { "measurement_id": "…", "measured_at": "2026-01-15", "x": 320, "value": 70.2, "z": -1.71, "flagged": false }
    ],
    "reference": {
      "x": [0, 30, 60],
      "sd_neg3": [44.2, 48.0, 51.0],
      "sd_neg2": [45.4, 49.4, 52.4],
      "median": [49.1, 53.7, 57.1],
      "sd_pos2": [52.9, 57.6, 61.1],
      "sd_pos3": [54.7, 59.5, 63.0]
    }
  },
  "error": null
}
```

Untuk `wfl_wfh`, `x_unit` = `"cm"` dan `x` berisi panjang/tinggi badan, bukan umur. Garis acuan cukup sampai umur anak + 6 bulan.

**GET `/children/{id}/kpsp/next`** → `{ "questionnaire_age_months": 9, "due": true, "items": [ { "item_no": 1, "aspect": "gerak_kasar", "question": "…" } ] }`. Nilai `aspect`: `gerak_kasar`, `gerak_halus`, `bicara_bahasa`, `sosialisasi_kemandirian`.

**POST `/children/{id}/kpsp`** → body `{ "questionnaire_age_months": 9, "answered_at": "2026-01-15", "answers": [ { "item_no": 1, "answer": true } ] }` (tepat 10 butir).

**GET `/guides?category=mpasi&age_months=9`** (v0.3) → kartu panduan statis untuk GiziCerdas (`category` = `mpasi`) dan Stimulasi Pintar (`category` = `stimulasi`, opsional `aspect`). Isinya disimpan Go di `guides.id.json`, disalin dari Buku KIA dan pedoman SDIDTK dengan sumber per kartu.

```json
{
  "data": [
    {
      "id": "mpasi-9-11-protein",
      "category": "mpasi",
      "age_from_months": 9,
      "age_to_months": 11,
      "aspect": null,
      "title": "…",
      "body": "…",
      "source": "Buku KIA, Kemenkes",
      "related_codes": ["CROSSING_DOWN", "WEIGHT_NOT_GAINING"]
    }
  ],
  "error": null
}
```

`related_codes` dipakai frontend untuk menampilkan kartu yang relevan di bawah peringatan. Laporan untuk Posyandu tidak butuh endpoint baru: halaman laporan merakit data dari `/children/{id}`, `/status`, `/measurements`, `/growth`, dan `/kpsp`.

**POST `/children/{id}/food-recalls`** (v0.4) → body `{ "recall_date": "2026-01-14", "breastfed": true, "food_groups": ["grains_roots_tubers", "vita_fruits_veg"], "meal_count": 3, "milk_feed_count": null }`; response 201 `{ "data": { "food_recall": { … }, "status": { … } }, "error": null }`.

**GET `/children/{id}/food-recalls`** → catatan 14 hari terakhir, terbaru dulu.

Response `/status` mendapat field tambahan `diet` (null bila belum ada catatan): `{ "recall_date": "2026-01-14", "group_count": 3, "mdd": false, "mmf": true, "eff": false }`.

## API internal engine (Go ↔ Python)

Engine adalah layanan FastAPI tanpa status di `http://localhost:8001/engine/v1`. Go selalu mengirim riwayat lengkap satu anak; engine menghitung lalu lupa. Go memanggil dengan batas waktu 3 detik; bila gagal, Go membalas frontend dengan `ENGINE_UNAVAILABLE`.

| Metode | Path | Fungsi |
| --- | --- | --- |
| POST | `/growth/evaluate` | z-score, klasifikasi, flag per pengukuran + tingkat dan kode alasan |
| GET | `/reference?indicator=lhfa&sex=female&x_from=0&x_to=500` | garis acuan WHO (−3, −2, median, +2, +3 SD); `indicator` = `wfa`, `lhfa`, `hcfa`, `wfl`, `wfh` (v0.7) |
| GET | `/kpsp/questionnaire?age_months=15` | butir KPSP umur jadwal itu beserta `review_status` (v0.7) |
| POST | `/kpsp/score` | hitung `yes_count` dan `result` |
| GET | `/health` | `{ "status": "ok", "who_tables_loaded": true }` |

**POST `/growth/evaluate`** — request:

```json
{
  "as_of": "2026-01-15",
  "child": { "sex": "female", "birth_date": "2025-03-01" },
  "measurements": [
    {
      "id": "…",
      "measured_at": "2026-01-15",
      "weight_kg": 8.1,
      "length_height_cm": 70.2,
      "position": "recumbent",
      "head_circumference_cm": null,
      "source": "posyandu"
    }
  ],
  "kpsp_results": [
    { "questionnaire_age_months": 6, "answered_at": "2025-09-02", "result": "sesuai" }
  ]
}
```

Response (angka karangan):

```json
{
  "data": {
    "per_measurement": [
      {
        "id": "…",
        "age_days": 320,
        "corrected_length_cm": 70.2,
        "z": { "wfa": -1.42, "lhfa": -1.71, "wfl_wfh": -0.62, "hcfa": null },
        "classification": { "wfa": "normal", "lhfa": "normal", "wfl_wfh": "normal" },
        "flags": []
      }
    ],
    "level": "yellow",
    "reasons": [
      {
        "code": "CROSSING_DOWN",
        "level": "yellow",
        "evidence": { "indicator": "wfa", "from_z": -0.71, "to_z": -1.42, "from_date": "2025-11-14", "to_date": "2026-01-15" }
      }
    ],
    "next_kpsp": { "questionnaire_age_months": 9, "due": true }
  },
  "error": null
}
```

Engine tidak mengembalikan kalimat untuk orang tua. Go menambahkan `title` dan `message` dari `messages.id.json` berdasarkan `code`, lalu mengisi nama anak ke dalam kalimat.

`wfl_wfh` berarti BB/PB untuk umur < 731 hari dan BB/TB untuk ≥ 731 hari; engine yang memilih. `flags` berisi kode `info` per titik, misalnya `IMPLAUSIBLE_VALUE`.

Sejak v0.4, request `/growth/evaluate` menyertakan `food_recalls` (catatan 14 hari terakhir, bentuk `FoodRecall` tanpa `id` dan `child_id`), dan response menyertakan `diet` dengan bentuk yang sama seperti di `/status`. Kode alasan pola makan dihitung di engine bersama kode lainnya.

Engine wajib punya tes pytest untuk: rumus LMS, koreksi posisi, setiap kode alasan minimal satu kasus, dan pembulatan umur KPSP.

## Penegasan v0.6

**Batas umur pengukuran: 1826 hari.** Angka 1856 di versi sebelumnya berasal dari konvensi umur bulan penuh pada Pedoman SDIDTK 2022 (hlm. 91: setelah 3 bulan, plotting memakai *completed months*). Dengan konvensi itu, anak 60 bulan 0–30 hari masih "60 bulan" dan dibaca dari baris 60 bulan tabel bulanan; ⌊61 × 30,4375⌋ = 1856. Engine memakai tabel WHO harian yang berakhir di hari 1826, jadi hari 1827–1856 tidak punya baris LMS. Proyek tidak mengekstrapolasi dan tidak memetakan hari ke baris bulanan tanpa sumber, maka batasnya disamakan dengan tabel: Go menolak pengukuran > 1826 hari dengan `VALIDATION_ERROR`, engine juga menolak dengan 422, dan garis acuan kurva berhenti di 1826. Sasaran aplikasi (6–24 bulan) tidak terdampak. Memakai baris hari 1826 untuk hari 1827–1856 sesuai konvensi bulan penuh adalah pengembangan setelah MVP dan butuh keputusan pemilik kontrak.

**`GET /children` tanpa ringkasan.** Kontrak tidak pernah mendefinisikan bentuk ringkasan, jadi endpoint ini hanya mengembalikan daftar `Child`; tingkat peringatan dibaca dari `/status` per anak, seperti yang sudah dilakukan frontend.

**Mode `AUTH_MODE=otp_dummy` di luar kontrak.** Endpoint `/api/v1/auth/*` serta error `UNAUTHORIZED` (401) dan `RATE_LIMITED` (429) adalah ekstensi pengujian backend, aktif hanya bila `AUTH_MODE=otp_dummy`, dan didokumentasikan di `backend/AUTH_TESTING.md`. Frontend dan demo tidak memakainya; Go saat demo wajib berjalan dalam mode bawaan (`demo`). Login tetap peta jalan setelah MVP.

**Isu terbuka: garis acuan `wfl_wfh`.** *(Diselesaikan di v0.7.)* `GET /reference` tidak bisa memilih tabel BB/PB atau BB/TB tanpa umur, sehingga engine membalas 503 dan kurva BB/PB-TB belum tersedia. Z-score dan klasifikasi `wfl_wfh` pada `/status` tidak terdampak. Usulan setelah demo: Go memilih tabel dari umur anak (< 731 hari = `wfl`, selainnya `wfh`) dan memanggil engine dengan nilai indikator itu; perubahan ini menambah nilai enum di API internal dan butuh persetujuan pemilik kontrak.

## Penegasan v0.7

Disetujui Zena, 7 November 2026. Kedua perubahan berlaku sesudah H+9 atas keputusan pemilik kontrak.

**KPSP tayang terbatas.** Engine `GET /kpsp/questionnaire?age_months=N` (N harus umur jadwal; selain itu 422) mengembalikan `{ "questionnaire_age_months": N, "review_status": "...", "items": [...] }`. `review_status` = `transcription_unreviewed` untuk formulir 15, 18, dan 24 bulan, satu-satunya formulir tanpa butir bergambar menurut `engine/data/kpsp/questionnaires.json`; `items` berisi 10 butir transkripsi apa adanya. Untuk umur jadwal lain `review_status` = `unavailable` dan `items` = `[]`. Daftar umur tayang tercatat di `source.runtime_ages`; engine menolak bank (503) bila umur tayang memuat butir bergambar.

Publik `GET /children/{id}/kpsp/next` menambah dua field: `review_status` (diteruskan dari engine) dan `review_label` (kalimat dari Go, ditampilkan frontend apa adanya). `items` boleh kosong bila `review_status` = `unavailable`; frontend lalu hanya menampilkan `review_label`. Jadwal, skor, dan `POST /children/{id}/kpsp` tidak berubah.

**Kurva BB/PB-TB.** Enum `indicator` pada `GET /reference` internal menjadi `wfa`, `lhfa`, `hcfa`, `wfl`, `wfh`; `wfl_wfh` tidak lagi diterima engine (422). Untuk `wfl`/`wfh`, `x_from`/`x_to` adalah cm bulat dan respons memakai grid 0,1 cm tabel WHO; di luar domain tabel (`wfl` 45–110, `wfh` 65–120) engine membalas 503 tanpa ekstrapolasi. Go memilih `wfl` bila umur anak hari ini < 731 hari, selainnya `wfh`, dan meminta seluruh domain tabel itu. API publik tetap `indicator=wfl_wfh`, `x_unit` = `"cm"`.

Batas yang diketahui: anak ≥ 731 hari yang punya pengukuran sebelum 731 hari tetap digambar di atas garis BB/TB; z-score titik itu sendiri tetap dihitung engine dengan tabel yang benar.

## Demo, batas cakupan, dan jadwal

Demo harus menunjukkan satu hal: sistem menangkap perlambatan pertumbuhan sebelum anak menjadi stunted.

**Skenario demo** (data di-seed, nama fiktif)

| Anak | Cerita | Tingkat yang diharapkan |
| --- | --- | --- |
| Anisa, perempuan | normal sampai umur 9 bulan, berat stagnan di bulan 10 dan 11 saat MPASI kurang protein | `yellow` di bulan 10, `red` (2T) di bulan 11, sementara `lhfa` masih ≥ −2 |
| Bima, laki-laki | tumbuh di jalurnya | `green` |
| Citra, perempuan | sudah pendek sejak lama | `red` (`STUNTED`), contoh kasus yang terlambat |

Angka pengukurannya disusun setelah engine jadi dan dicek dengan engine itu sendiri, bukan dikarang di slide.

**Di luar cakupan MVP** (cukup disebut di slide sebagai pengembangan lanjutan): login dan banyak pengguna, dashboard kader, peta sebaran, LLM penjelas, koreksi umur prematur, pengukuran lewat kamera, notifikasi push, integrasi data Posyandu sungguhan.

Jika waktu tersisa, LLM penjelas masuk sebagai `POST /children/{id}/explain`. Ia hanya menerima output `/growth/evaluate` dan tidak pernah menghitung atau memutuskan tingkat.

**Titik periksa** (H = jam sejak mulai)

1. H+1 — kontrak v1.0 dibekukan; monorepo dan `docker-compose` menjalankan tiga layanan kosong.
2. H+4 — `/growth/evaluate` lolos tes; Go CRUD + database jalan; frontend punya layar daftar anak, input pengukuran, dan status dengan data tiruan.
3. H+7 — alur ujung ke ujung tersambung; grafik kurva dan KPSP tampil.
4. H+9 — fitur dibekukan; sisanya hanya perbaikan bug.
5. H+10 — data demo di-seed; gladi alur demo pertama.
6. H+11 — slide dan laporan, masing-masing menulis bagiannya.
7. H+12 — gladi akhir; rekam video demo sebagai cadangan.
