# Pantau Tumbuh Kembang Anak

Aplikasi untuk orang tua balita: catat pengukuran sepulang Posyandu, lihat posisi anak di kurva WHO,
terima peringatan dini sebelum stunting terjadi, isi skrining perkembangan (KPSP) dan catatan makan,
lalu tahu apa yang harus dilakukan. Dibuat untuk HIMTEC 2026.

> Aplikasi ini **alat skrining, bukan diagnosis**. Setiap peringatan merah merujuk ke Posyandu/Puskesmas.

## Baca dulu

| Berkas | Isi |
| --- | --- |
| [AGENTS.md](AGENTS.md) | aturan kerja untuk manusia dan semua asisten AI |
| [docs/CONTRACT.md](docs/CONTRACT.md) | protokol komunikasi: data, API publik, API engine (sumber kebenaran) |
| [docs/PRD.md](docs/PRD.md) | apa yang dibangun dan kapan dianggap selesai |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | setiap perubahan yang memengaruhi orang lain |
| [docs/HANDOFF.md](docs/HANDOFF.md) | serah terima per peran dan status integrasi |

## Arsitektur

```
Frontend (Vue, :5173) ──HTTP──> Backend Go (:8080/api/v1) ──HTTP──> Engine Python (:8001/engine/v1)
                                       │                                   │
                                  PostgreSQL (:5432)              tabel WHO, KPSP, IYCF
```

Frontend hanya bicara dengan Go. Hanya Go yang memanggil engine. Engine tidak menyimpan status.

## Menjalankan

Salin variabel lingkungan dulu:

```bash
cp .env.example .env    # dari akar repo; isi ENGINE_URL dengan IP laptop yang menjalankan engine
```

**Engine** (laptop Zena):

```bash
cd engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001
pytest                  # wajib lulus sebelum push
```

**Backend** (laptop teman):

```bash
cd backend
go run ./cmd/server
```

**Diagnostik engine** (dari backend/):

```bash
go run ./cmd/check-engine
```

Health berhasil tidak berarti endpoint evaluasi siap. Pada snapshot ini main.py engine masih hanya mendaftarkan health; Go melaporkan route yang belum ada melalui diagnostik OpenAPI. Backend CRUD/login tetap dapat berjalan. Pengujian fixture lokal tersedia di backend/testing/README.md; tidak ada fallback medis otomatis.

**Frontend dan Docker:** frontend masih kerangka folder; package.json/aplikasi Vite dan konfigurasi Compose belum tersedia pada snapshot ini. Perintah npm/Docker untuk seluruh stack adalah rencana, belum langkah yang dapat dijalankan. Gunakan API Go melalui PowerShell sampai aplikasi frontend dan Compose disediakan.

**Mode OTP lokal:** set AUTH_MODE=otp_dummy di terminal Go sebelum startup. Gunakan Authorization Bearer saat menguji data anak; panduan lengkap di backend/AUTH_TESTING.md. Mode demo default tetap tersedia. Tidak ada email/SMS nyata pada OTP dummy.

## Tim

| Peran | Folder |
| --- | --- |
| Full stack + AI engine (Zena) | `engine/`, `docs/` |
| Backend | `backend/` |
| Desain + frontend | `frontend/` |

## Sumber standar

Standar Pertumbuhan Anak WHO 2006 · Permenkes No. 2 Tahun 2020 tentang Standar Antropometri Anak ·
Pedoman SDIDTK Kemenkes (KPSP) · Indikator IYCF WHO/UNICEF 2021 · Buku KIA Kemenkes.
