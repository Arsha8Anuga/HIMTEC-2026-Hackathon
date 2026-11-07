# Pantau Tumbuh Kembang Anak

Aplikasi untuk orang tua balita: catat pengukuran sepulang Posyandu, lihat posisi anak di kurva WHO,
terima peringatan dini sebelum stunting terjadi, isi skrining perkembangan (KPSP) dan catatan makan,
lalu tahu apa yang harus dilakukan. Dibuat untuk HIMTEC 2026.

> Aplikasi ini **alat skrining, bukan diagnosis**. Setiap peringatan merah merujuk ke Posyandu/Puskesmas.

## Baca dulu

| Berkas | Isi |
| --- | --- |
| [AGENTS.md](../AGENTS.md) | aturan kerja untuk manusia dan semua asisten AI |
| [CONTRACT.md](CONTRACT.md) | protokol komunikasi: data, API publik, API engine (sumber kebenaran) |
| [PRD.md](PRD.md) | apa yang dibangun dan kapan dianggap selesai |
| [CHANGELOG.md](CHANGELOG.md) | setiap perubahan yang memengaruhi orang lain |
| [HANDOFF.md](HANDOFF.md) | serah terima per peran dan status integrasi |

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

**Frontend** (laptop teman):

```bash
cd frontend
npm install
npm run dev             # demo: npm run build && npm run preview
```

**Mode cadangan satu laptop:** `docker-compose up` dengan `ENGINE_URL=http://engine:8001/engine/v1`.

## Tim

| Peran | Folder |
| --- | --- |
| Full stack + AI engine (Zena) | `engine/`, `docs/` |
| Backend | `backend/` |
| Desain + frontend | `frontend/` |

## Sumber standar

Standar Pertumbuhan Anak WHO 2006 · Permenkes No. 2 Tahun 2020 tentang Standar Antropometri Anak ·
Pedoman SDIDTK Kemenkes (KPSP) · Indikator IYCF WHO/UNICEF 2021 · Buku KIA Kemenkes.
