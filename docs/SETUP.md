# Menjalankan aplikasi dari nol

Panduan ini membawa satu laptop Windows yang bersih sampai aplikasi bisa dipakai di peramban:
engine Python → PostgreSQL → backend Go → frontend Vue. Setiap langkah punya pemeriksaan;
jangan lanjut sebelum pemeriksaannya lolos. Bagian akhir menjelaskan mode demo dua laptop.

Perintah ditulis untuk PowerShell. Di Linux/macOS, ganti `curl.exe` dengan `curl`,
`copy` dengan `cp`, dan aktivasi venv dengan `source .venv/bin/activate`.

## 0. Prasyarat

| Perangkat | Versi | Catatan |
| --- | --- | --- |
| Git | apa saja | |
| Python | 3.10 atau lebih baru | centang "Add python.exe to PATH" saat instalasi |
| Go | 1.22 atau lebih baru | |
| Node.js | 20 LTS atau lebih baru | |
| PostgreSQL | 13 atau lebih baru (disarankan 16) | catat kata sandi user `postgres`; `psql` ada di `C:\Program Files\PostgreSQL\16\bin` |

Internet hanya dibutuhkan saat persiapan (unduh dependensi dan tabel WHO). Setelah itu semuanya jalan tanpa internet.

```powershell
git clone https://github.com/Arsha8Anuga/HIMTEC-2026-Hackathon.git
cd HIMTEC-2026-Hackathon
copy .env.example .env
```

Buka `.env` di akar repo, lalu isi:

```
DATABASE_URL=postgres://postgres:KATA_SANDI@localhost:5432/tumbuh?sslmode=disable
ENGINE_URL=http://127.0.0.1:8001/engine/v1
CORS_ORIGIN=http://localhost:5173
```

## 1. Engine Python

```powershell
cd engine
python -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass   # hanya bila Activate.ps1 diblokir
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/fetch_who_tables.py          # sekali saja, butuh internet
python -m pytest -q                         # harus lulus semua
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Periksa** (terminal lain):

```powershell
curl.exe http://127.0.0.1:8001/engine/v1/health
```

Harus `"who_tables_loaded": true`. Bila `false`, tabel WHO belum terunduh atau rusak; ulangi `fetch_who_tables.py`.
Biarkan terminal engine tetap terbuka.

## 2. Database PostgreSQL

```powershell
psql -U postgres -c "CREATE DATABASE tumbuh"
```

Tabel tidak dibuat manual; Go membuatnya sendiri di langkah berikut.

## 3. Backend Go

**Wajib dijalankan dari dalam folder `backend/`.** Path migrasi dan `data/` bersifat relatif;
dari folder lain server langsung berhenti dengan `open migrations/001_init.sql: no such file`.

```powershell
cd backend
go test ./...
go run ./cmd/server
```

Log yang benar memuat tiga baris ini (urutannya boleh berbeda):

```
AUTH_MODE=demo: tanpa login ...
Health engine OK ...
Backend Go siap pada http://localhost:8080/api/v1 ...
```

Jangan mengisi `AUTH_MODE=otp_dummy`. Mode itu ekstensi pengujian di luar kontrak, dan frontend
akan menerima 401 di setiap halaman.

Setelah server pertama kali berjalan, isi anak demo dan pengukurannya (terminal lain, dari `backend/`).
Jalankan keduanya **pada hari yang sama**, berurutan:

```powershell
psql -U postgres -d tumbuh -f migrations/002_seed_children.sql
psql -U postgres -d tumbuh -f migrations/005_seed_demo_measurements.sql
```

**Periksa:**

```powershell
curl.exe http://localhost:8080/api/v1/children
go run ./cmd/check-engine
```

Yang pertama harus menampilkan Anisa, Bima, dan Citra; di peramban statusnya merah, hijau, merah. Yang kedua harus melaporkan
keempat route engine ada (sejak kontrak v0.7 termasuk `GET /kpsp/questionnaire`).

## 4. Frontend Vue

Vite membaca `.env` dari folder `frontend/`, bukan dari akar repo.

```powershell
cd frontend
copy .env.example .env      # isinya VITE_API_URL=http://localhost:8080/api/v1
npm install
npm run dev
```

Buka **http://localhost:5173**, bukan `127.0.0.1:5173`. Go hanya mengizinkan origin yang persis sama
dengan `CORS_ORIGIN`; alamat lain membuat semua permintaan ditolak peramban.

Alamat halaman memakai `#`, misalnya `http://localhost:5173/#/children/<id>/growth`.

**Versi build untuk demo** memakai port 4173 secara bawaan. Supaya CORS tetap cocok, jalankan di port 5173:

```powershell
npm run build
npm run preview -- --port 5173
```

## 5. Alur pemeriksaan di peramban

1. Beranda menampilkan tiga kartu anak dengan label status.
2. Tambah anak → isi nama dan tanggal lahir → Simpan. Halaman berpindah ke ringkasan anak baru.
3. Catat pengukuran → isi berat dan panjang (maksimal 1 angka di belakang koma) → Simpan.
   Ringkasan menampilkan status, nilai terakhir, dan "Hal yang perlu diperhatikan".
4. Kurva → pilih Panjang/tinggi menurut umur dan Berat menurut umur; keduanya menampilkan pita SD dan titik anak.
5. Catatan makan (anak 6–23 bulan) → simpan → ringkasan menampilkan kartu catatan makan.
6. Riwayat → Hapus → konfirmasi → status dihitung ulang.
7. Ringkasan → Buka laporan → Cetak / simpan PDF → periksa tampilan A4.

## Mode demo dua laptop

Engine di laptop Zena; Go, PostgreSQL, dan frontend di laptop teman. Semua tersambung ke hotspot ponsel tim.

Di laptop Zena:

```powershell
ipconfig                    # catat IPv4 adaptor Wi-Fi, mis. 192.168.43.20
New-NetFirewallRule -DisplayName "Engine 8001" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow   # PowerShell admin, sekali saja
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Matikan mode sleep dan pasang charger.

Di laptop teman, ubah `ENGINE_URL` di `.env` akar repo menjadi `http://<IP-laptop-Zena>:8001/engine/v1`,
lalu **mulai ulang** Go. Periksa dari laptop teman:

```powershell
curl.exe http://<IP-laptop-Zena>:8001/engine/v1/health
```

IP berubah setiap hotspot tersambung ulang; ulangi pemeriksaan ini sebelum demo.

Mode cadangan satu laptop: jalankan langkah 1–4 di satu mesin dengan `ENGINE_URL=http://127.0.0.1:8001/engine/v1`.
`docker-compose.yml` belum ada di repo.

## Mengosongkan data (sebelum gladi)

Hentikan Go, lalu:

```powershell
psql -U postgres -c "DROP DATABASE tumbuh"
psql -U postgres -c "CREATE DATABASE tumbuh"
```

Jalankan Go lagi dari `backend/`, kemudian ulangi seed `002_seed_children.sql` dan `005_seed_demo_measurements.sql`.
Lakukan ini **pada hari demo**: umur anak demo dihitung dari tanggal seed.

## Data demo

Semua nama dan angka fiktif. Angka dihitung dari tabel WHO pada z-score sasaran, dibulatkan 0,1,
lalu diperiksa dengan engine asli. Tanggal pengukuran = tanggal lahir + umur bulan.

| Anak | Pengukuran (umur bulan: BB kg / PB cm) | Status |
| --- | --- | --- |
| Anisa, perempuan, 11 bln | 6: 7,3/65,0 · 7: 7,6/66,5 · 8: 7,9/68,0 · 9: 8,2/69,4 · 10: 8,2/70,7 · 11: 8,2/72,0 | hijau sampai 9 bln → kuning (berat tidak naik) di 10 bln → merah (tidak naik dua kali) di 11 bln; PB/U tetap sekitar −0,3 |
| Bima, laki-laki, 13 bln | 9–13 bln, BB 9,1 → 10,1, PB 72,2 → 77,2 | hijau, z sekitar +0,2 |
| Citra, perempuan, 15 bln | 12–15 bln, BB 7,5 → 8,0, PB 67,6 → 70,7 | merah, pendek (PB/U sekitar −2,5) |

Semua anak juga menampilkan info "Belum ada catatan makan terbaru"; itu benar, seed tidak mengisi catatan makan.

**Memperagakan peringatan dini secara langsung:** di Riwayat Anisa, catat tanggal dua pengukuran
terakhir, lalu hapus keduanya; status kembali hijau. Catat pengukuran ulang dengan tanggal yang sama,
satu per satu: BB 8,2 / PB 70,7 / LK 44,2 / Posyandu → kuning; BB 8,2 / PB 72,0 / LK 44,6 / Posyandu → merah.
Alur ini sudah diuji lewat Go dengan engine asli.

**Memeriksa ulang angka seed** setelah engine atau aturan berubah (dari `engine/`):

```powershell
python scripts/verify_demo_seed.py --days 30
```

Harus berakhir `0 kegagalan`.

## Batas yang diketahui (kontrak v0.7)

| Gejala | Penyebab | Sikap saat demo |
| --- | --- | --- |
| Halaman Perkembangan hanya menampilkan "Kuesioner untuk umur ini belum tersedia di aplikasi…" | hanya formulir 15, 18, 24 bulan yang tayang (tanpa butir bergambar) | peragakan KPSP dengan Citra (15 bulan); Anisa (formulir 9) dan Bima (formulir 12) menampilkan label ini |
| Formulir KPSP berlabel "Transkripsi … belum ditinjau klinis" | butir diketik ulang dari pedoman SDIDTK 2022, belum ditinjau tenaga kesehatan | sebut terus terang saat demo |
| Kurva BB/PB sumbu x mulai dari 0 cm | skala sumbu grafik frontend | tidak mengganggu; garis acuan mulai 45 cm |
| Halaman Panduan kosong | `guides.id.json` belum diisi | tidak ditampilkan |

## Mode satu laptop (Docker Compose)

Cadangan bila hotspot gagal. **Bangun image saat masih ada internet**; setelah itu `up` berjalan tanpa internet.
Tabel WHO tidak masuk image, jadi jalankan `python scripts/fetch_who_tables.py` di `engine/` lebih dulu.

```powershell
docker compose build
docker compose up -d
docker compose exec db psql -U postgres -d tumbuh -f /seed/002_seed_children.sql
docker compose exec db psql -U postgres -d tumbuh -f /seed/005_seed_demo_measurements.sql
```

Buka **http://localhost:5173**. Go di dalam Compose memakai `ENGINE_URL=http://engine:8001/engine/v1` dan
PostgreSQL `db`; PostgreSQL lokal di port 5432 tidak dipakai dan tidak bentrok (port db tidak dibuka ke luar).
Reset data: `docker compose down -v`, lalu `up` dan seed ulang pada hari demo.

Status: berkas ini belum pernah dijalankan utuh di mesin pembuat (registry Docker tidak terjangkau di sana);
perintah yang sama di dalam image sudah diuji tanpa Docker. Coba sekali di laptop demo sebelum gladi.

## Masalah umum

| Gejala | Penyebab | Perbaikan |
| --- | --- | --- |
| Go: `open migrations/001_init.sql` | Go dijalankan dari luar `backend/` | `cd backend` lalu jalankan ulang |
| Go: `DATABASE_URL wajib diisi` | `.env` akar belum dibuat | `copy .env.example .env` di akar repo |
| Go: `tidak dapat memakai port 8080` | Go lama masih jalan | tutup terminal lama |
| Status: "Perhitungan sementara tidak tersedia" | engine mati atau `ENGINE_URL` salah | periksa `/health` engine dari laptop Go |
| Frontend: "Layanan belum dapat dihubungi" | CORS (alamat bukan `localhost:5173`) atau Go mati | buka `http://localhost:5173`, cek Go |
| Frontend: "Alamat layanan belum diatur" | `frontend/.env` belum ada | salin `.env.example` di `frontend/`, mulai ulang `npm run dev` |
| `/health` engine `who_tables_loaded: false` | tabel WHO belum diunduh | `python scripts/fetch_who_tables.py` saat ada internet |

## Menjalankan semua tes

```powershell
cd engine;   python -m pytest -q
cd backend;  go test ./...
cd frontend; $env:CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"; npm test
```

Tes frontend memakai API tiruan, jadi tidak butuh Go atau engine.
