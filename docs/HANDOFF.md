# Serah terima

Tulis untuk orang atau asisten AI yang tidak tahu apa-apa tentang pekerjaanmu. Perbarui bagianmu
di setiap titik periksa (H+4, H+7, H+9), saat berpindah tugas, saat menyerahkan pekerjaan ke anggota
lain, dan sebelum membuka sesi AI baru. Ganti isinya, jangan menumpuk riwayat; riwayat ada di
CHANGELOG.md dan git.

Cara membuka sesi AI baru: tempel AGENTS.md, bagian kontrak yang relevan, lalu bagianmu di bawah ini.

---

## Engine — Zena

- **Diperbarui:** 2026-11-07 10:13 WIB (patch ZIP 02)
- **Selesai:** `engine/requirements.txt` (patch 01); fondasi aplikasi FastAPI, router `GET /engine/v1/health`, standar envelope JSON dan error `VALIDATION_ERROR`/`NOT_FOUND`, model Pydantic untuk request `/growth/evaluate` (termasuk `food_recalls` v0.4), 26 tes pytest lulus.
- **Sedang dikerjakan:** fondasi selesai, menunggu implementasi tabel WHO dan kalkulasi pertumbuhan.
- **Belum dimulai:** muat tabel LMS WHO resmi; rumus LMS/restricted LMS; koreksi posisi; klasifikasi Permenkes; seluruh kode alasan; endpoint `/growth/evaluate`, `/reference`, `/kpsp/questionnaire`, `/kpsp/score`; logika IYCF dan uji banding WHO Anthro.
- **Cara menjalankan dan menguji:** `cd engine && python -m pip install -r requirements.txt && python -m pytest -q` (hasil patch ini: `26 passed`); server `python -m uvicorn app.main:app --host 0.0.0.0 --port 8001`; cek `GET /engine/v1/health`.
- **Masalah yang diketahui:** `who_tables_loaded=false` secara sengaja karena tabel WHO resmi belum ada; hanya endpoint health yang diimplementasikan. Kontrak v0.4 masih draf; sumber tabel dan ambang medis wajib diverifikasi sebelum dipakai. Dokumentasi belum menentukan detail request body `/kpsp/score`.
- **Butuh dari orang lain:** penyepakatan kontrak v1.0; backend harus mengirim `food_recalls` sebagai array (boleh kosong) dalam request `/growth/evaluate` sesuai v0.4; konfirmasi skema `/kpsp/score` sebelum kode endpoint dibuat.
- **Langkah berikutnya:** unduh dan catat sumber tabel WHO resmi, tulis loader beserta tes, implementasikan perhitungan LMS, lalu endpoint `/growth/evaluate` beserta tes kasus pembanding WHO Anthro. Semua perubahan dikirim sebagai ZIP, bukan push langsung.

## Backend — (nama)

- **Diperbarui:** HH:MM
- **Selesai:**
- **Sedang dikerjakan:**
- **Belum dimulai:**
- **Cara menjalankan dan menguji:**
- **Masalah yang diketahui:**
- **Butuh dari orang lain:**
- **Langkah berikutnya:**

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

| Endpoint | Go siap | Engine siap | Frontend tersambung |
| --- | --- | --- | --- |
| `GET/POST /children` | | — | |
| `GET /children/{id}/status` | | | |
| `POST /children/{id}/measurements` | | | |
| `GET /children/{id}/growth` | | | |
| `GET /children/{id}/kpsp/next`, `POST /children/{id}/kpsp` | | | |
| `GET /guides` | | — | |
| `GET/POST /children/{id}/food-recalls` | | | |
