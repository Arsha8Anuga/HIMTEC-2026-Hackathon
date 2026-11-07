# AGENTS.md — aturan untuk manusia dan asisten AI di repo ini

Berlaku untuk semua asisten AI di tim (ChatGPT/Codex dan Claude) dan untuk kita bertiga.
Pengguna ChatGPT di web: tempel berkas ini, ditambah bagian kontrak yang relevan, di awal setiap sesi baru.

## Proyek

Aplikasi pemantau tumbuh kembang anak untuk HIMTEC 2026 (13 jam, 3 orang).
Aplikasi ini **alat skrining, bukan diagnosis**. Setiap peringatan merah merujuk ke Posyandu/Puskesmas.

## Sumber kebenaran

1. **Kontrak** (bentuk data dan API): `docs/CONTRACT.md`
2. **PRD** (apa yang dibangun dan kapan dianggap selesai): `docs/PRD.md`

Keduanya diekspor dari dokumen tim: https://claude.ai/artifact/UBPUY3UnFEi8tj1v7NJpgk
(tab pertama = kontrak, tab "PRD"). Setiap kali versi kontrak naik, Zena mengekspor ulang
keduanya ke `docs/` dan mencatatnya di `docs/CHANGELOG.md`.

Semua dokumen proyek ada di `docs/`; hanya README.md, AGENTS.md, dan CLAUDE.md yang tinggal di akar repo.

Jika kode berbeda dengan kontrak, **kodenya yang salah**. Jika kontrak tidak menjawab, tanya di grup. Jangan menebak.

## Kepemilikan folder

| Folder / berkas | Pemilik | Catatan |
| --- | --- | --- |
| `engine/` | Zena | Python FastAPI, tanpa status |
| `backend/` | Backend | Go API, PostgreSQL, `messages.id.json`, `guides.id.json`, seed |
| `frontend/` | Desain + frontend | Vue 3 + Vite + TS + Tailwind + shadcn-vue |
| `docs/`, `AGENTS.md`, `CLAUDE.md` | Zena | |
| `docs/CHANGELOG.md`, `docs/HANDOFF.md` | semua | setiap orang menulis bagiannya sendiri |

Jangan mengubah folder milik orang lain. Butuh perubahan di sana? Minta lewat grup.

## Aturan keras

1. Jangan menambah field, endpoint, nilai enum, atau kode alasan yang tidak ada di kontrak.
2. Jangan menulis angka medis (tabel LMS WHO, ambang klasifikasi, butir KPSP, tabel KBM) dari ingatan model AI.
   Angka hanya dibaca dari berkas di `engine/data/` yang sumber resminya tercatat.
3. Frontend tidak menyusun kalimat medis. Semua teks untuk orang tua datang dari backend.
4. Engine tidak menyentuh database dan tidak menyimpan status. Go selalu mengirim riwayat lengkap.
5. Alamat layanan dibaca dari variabel lingkungan (`ENGINE_URL`, `VITE_API_URL`), tidak pernah di-hardcode.
6. Tidak ada CDN saat aplikasi berjalan: huruf, ikon, dan pustaka dibundel. Demo harus jalan tanpa internet.
7. Setiap perubahan yang memengaruhi orang lain dicatat di `docs/CHANGELOG.md` dalam commit yang sama.
   Perubahan kontrak menaikkan versi dan harus disetujui Zena.
8. Setelah H+9: hanya perbaikan bug, tidak ada fitur baru.

## Menjalankan

| Layanan | Port | Mesin saat demo |
| --- | --- | --- |
| Frontend | 5173 | laptop teman |
| Backend Go | 8080 (`/api/v1`) | laptop teman |
| PostgreSQL | 5432 | laptop teman |
| Engine Python | 8001 (`/engine/v1`), bind `0.0.0.0` | laptop Zena |

Semua laptop tersambung ke hotspot ponsel tim. Mode cadangan satu laptop: `docker compose up` (lihat `docs/SETUP.md`)
dengan `ENGINE_URL=http://engine:8001/engine/v1`.

## Konvensi

- Pesan commit: `<area>: <ringkasan>`, dengan `area` = `engine` | `backend` | `frontend` | `docs`.
- Commit kecil dan sering. `git pull --rebase` sebelum push.
- JSON memakai snake_case; tanggal `YYYY-MM-DD`; satuan kg dan cm (detail di kontrak).
- Engine: FastAPI, Pydantic, pytest. Setiap kode alasan punya minimal satu tes.

## Serah terima

Perbarui bagianmu di `docs/HANDOFF.md` ketika: mencapai titik periksa (H+4, H+7, H+9), berpindah tugas,
menyerahkan pekerjaan ke anggota lain, atau membuka sesi AI baru karena sesi lama terlalu panjang.
