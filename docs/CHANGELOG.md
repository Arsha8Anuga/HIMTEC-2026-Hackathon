# Changelog

Entri terbaru di atas. Catat setiap perubahan yang memengaruhi orang lain: kontrak, PRD, API,
skema database, port, variabel lingkungan, atau aturan kerja. Perubahan kecil di dalam folder
sendiri cukup ditulis di pesan commit.

Format satu baris:

```
- HH:MM · <area atau versi> · <siapa> · <apa yang berubah> · [MERUSAK] · <siapa yang harus menyesuaikan>
```

Tandai `[MERUSAK]` bila mengganti nama, mengubah tipe, atau menghapus field/endpoint.

## 2026-11-07

- 10:03 · backend · tim backend · hasil uji di laptop Windows: kendala dependensi `github.com/lib/pq`/`go.sum` telah teratasi setelah penataan modul (`go mod tidy`); startup sempat terhenti karena `DATABASE_URL` belum terisi, lalu layanan berhasil menerima HTTP di `localhost:8080`; akses `GET /api/v1/` mengembalikan `NOT_FOUND` karena bukan route terdaftar (perilaku yang diharapkan). Belum ada bukti uji CRUD maupun evaluasi Python end-to-end · — · backend: lanjutkan tes `GET/POST /children` serta koneksi engine; frontend: gunakan route lengkap di bawah `/api/v1`

- 09:39 · backend · tim backend · implementasi Go API + migrasi PostgreSQL + client HTTP Python, pesan Indonesia dan seed identitas fiktif; panduan resmi dan verifikasi bentuk respons engine masih dibutuhkan · — · Zena: konfirmasi score/reference dan isi panduan; frontend: integrasi endpoint yang sudah tersedia

- 09:25 · docs · Zena · semua dokumen dipindah ke `docs/` (README, CONTRACT, PRD, CHANGELOG, HANDOFF); hanya AGENTS.md dan CLAUDE.md di akar · — · semua: perbarui rujukan path
- 08:50 · kontrak v0.4 + PRD v0.2 · Zena · fitur Catatan Makan Kemarin: entitas `FoodRecall`, `POST/GET /children/{id}/food-recalls`, field `diet` di `/status`, `food_recalls` di `/growth/evaluate`, kode alasan `NO_ANIMAL_SOURCE_FOOD`, `LOW_DIET_DIVERSITY`, `LOW_MEAL_FREQUENCY`, `NO_RECENT_FOOD_RECALL` · — · backend: tabel + endpoint; frontend: layar catatan makan; engine: indikator IYCF
- 08:37 · docs · Zena · menambah AGENTS.md, CLAUDE.md, CHANGELOG.md, HANDOFF.md · — · semua: baca AGENTS.md
- 08:31 · kontrak v0.3 · Zena · menambah `GET /api/v1/guides` untuk kartu GiziCerdas dan Stimulasi; PRD v0.1 ditulis · — · backend: siapkan `guides.id.json`; frontend: layar Panduan
- 08:29 · kontrak v0.2 · Zena · jaringan demo: engine di laptop Zena, Go membaca `ENGINE_URL` · — · backend
- 08:10 · kontrak v0.1 · Zena · draf awal kontrak · — · semua
