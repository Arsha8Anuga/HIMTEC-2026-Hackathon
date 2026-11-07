# Backend Go + PostgreSQL — HIMTEC 2026

Mengikuti `docs/CONTRACT.md` v0.4. Fokus: API publik di `:8080/api/v1`, PostgreSQL `:5432`, dan komunikasi HTTP/JSON ke Python FastAPI melalui `ENGINE_URL`. Engine tidak membaca PostgreSQL. **Alat skrining, bukan diagnosis.**

## Persyaratan (Windows)

1. Go 1.22 atau lebih baru (`go version`).
2. PostgreSQL 13 atau lebih baru (`psql --version` bila tersedia) yang berjalan di port **5432**.
3. Saat pertama kali: internet untuk mengunduh driver Go `github.com/lib/pq` (setelah terunduh, demo dapat offline).
4. Akses hotspot ke laptop Zena yang menjalankan engine FastAPI port **8001**. Untuk menjalankan CRUD saja, engine boleh belum menyala, tetapi endpoint status/growth/KPSP akan mengembalikan 503.

## Langkah menjalankan (PowerShell)

Dari **akar repo**:

```powershell
Copy-Item .env.example .env
notepad .env
```

Contoh isi variabel yang **perlu disesuaikan dengan laptop** (jangan meng-commit `.env`):

```dotenv
DATABASE_URL=postgres://postgres:ISI_PASSWORD_POSTGRES@localhost:5432/tumbuh?sslmode=disable
ENGINE_URL=http://IP_LAPTOP_ZENA:8001/engine/v1
CORS_ORIGIN=http://localhost:5173
```

Buat database satu kali di pgAdmin (Databases → Create → Database → `tumbuh`) **atau** di terminal dengan `psql`:

```powershell
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE tumbuh;"
```

Dari folder `backend/`:

```powershell
cd backend
go mod download
go run ./cmd/server
```

Pada startup, Go otomatis menjalankan `migrations/001_init.sql` (idempoten). Server mendengarkan `0.0.0.0:8080` sehingga frontend pada hotspot yang sama dapat mengakses alamat IP laptop backend. Jangan mengubah port/route tanpa kesepakatan kontrak.

## Uji cepat

Buka PowerShell kedua saat server menyala:

```powershell
# Mendapatkan daftar anak: {"data":[],"error":null} jika kosong
Invoke-RestMethod http://localhost:8080/api/v1/children

# Menambah anak fiktif (ubah tanggal lahir sesuai kebutuhan)
$body = @{name="Anak Demo"; sex="female"; birth_date="2026-01-07"; is_preterm=$false} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/v1/children -ContentType 'application/json' -Body $body
```

Ambil `id` dari respons POST. Untuk menguji status, jalankan engine Python terlebih dulu, lalu:

```powershell
Invoke-RestMethod http://localhost:8080/api/v1/children/ISI_UUID/status
```

**Menguji koneksi langsung ke engine:**

```powershell
Invoke-RestMethod http://IP_LAPTOP_ZENA:8001/engine/v1/health
```

Jika gagal, cek IP hotspot, firewall Windows pada laptop Zena, dan bind engine `0.0.0.0:8001`.

## Skema dan data

- `migrations/001_init.sql`: tabel `children`, `measurements`, `kpsp_results`, `food_recalls`, constraint, relasi FK, indeks.
- `migrations/002_seed_children.sql`: **opsional**, hanya nama/identitas anak fiktif, tanpa nilai medis. Untuk menjalankan: `psql -U postgres -d tumbuh -f migrations/002_seed_children.sql` dari folder `backend/`.
- `data/messages.id.json`: teks Indonesia untuk seluruh kode alasan di kontrak (isi dari tindakan pada kontrak; tetap perlu ditinjau tim medis).
- `data/guides.id.json`: **sengaja `[]`** sampai Zena menyediakan kartu yang disalin dan disitasi dari Buku KIA/SDIDTK. Tidak boleh mengarang panduan medis.

### API yang disediakan

| Metode | Path (`/api/v1` +) | Keterangan |
| --- | --- | --- |
| GET / POST | `/children` | Daftar dan tambah anak |
| GET | `/children/{id}` | Detail anak |
| GET | `/children/{id}/status` | Status engine dengan teks Indonesia |
| GET / POST | `/children/{id}/measurements` | Riwayat dan input pengukuran |
| DELETE | `/children/{id}/measurements/{mid}` | Hapus pengukuran |
| GET | `/children/{id}/growth?indicator=lhfa` | Titik kurva dan acuan engine |
| GET | `/children/{id}/kpsp/next` | Jadwal dan pertanyaan dari engine |
| GET / POST | `/children/{id}/kpsp` | Riwayat dan skor KPSP dari engine |
| GET | `/guides?category=mpasi&age_months=9` | Kartu panduan yang diizinkan |
| GET / POST | `/children/{id}/food-recalls` | Catatan makan / status |

Semua balasan menggunakan `{ "data": ..., "error": null }`, atau `{ "data": null, "error": {"code": ..., "message": ...} }`. Kode error mengikuti kontrak: `VALIDATION_ERROR` (422), `NOT_FOUND` (404), `ENGINE_UNAVAILABLE` (503), `INTERNAL` (500).

## Catatan integrasi penting

- **Bentuk ringkasan `GET /children` belum dicontohkan secara eksplisit dalam kontrak.** Implementasi sekarang hanya mengembalikan daftar objek `Child` tanpa menambah field baru. Minta Zena membekukan bentuk ringkasan sebelum menambahnya.
- **Body `POST /engine/v1/kpsp/score` dan respons lengkap `GET /engine/v1/reference` belum dicontohkan dalam kontrak**. Implementasi mengikuti field yang sudah disebut di kontrak dan harus dicocokkan dengan engine Python milik Zena.
- `POST /measurements` dan `POST /food-recalls` **menyimpan data dahulu**, lalu meminta evaluasi Python. Bila Python tidak tersedia, data tetap tersimpan tetapi permintaan membalas HTTP 503 seperti kontrak/PRD; gunakan GET riwayat untuk memastikan data sudah masuk (jangan kirim ulang secara membabi buta).
- Pastikan **driver Go sudah terunduh sebelum demo tanpa internet**. `go mod download` lalu `go run ./cmd/server` sekali sebelum hotspot diputus dari internet.
- Tidak ada login (MVP sesuai PRD). Gunakan data fiktif saja selama demo, jangan data asli anak.

## Tes

```powershell
go test ./...
```

Tes unit tidak memerlukan PostgreSQL aktif; alur database dan engine yang sebenarnya tetap perlu dites di laptop tim. Jangan gunakan hasil tes unit untuk mengklaim z-score/KPSP sudah tervalidasi secara medis.
