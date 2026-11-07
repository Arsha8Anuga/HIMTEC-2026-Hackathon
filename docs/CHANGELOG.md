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

- 09:25 · docs · Zena · semua dokumen dipindah ke `docs/` (README, CONTRACT, PRD, CHANGELOG, HANDOFF); hanya AGENTS.md dan CLAUDE.md di akar · — · semua: perbarui rujukan path
- 08:50 · kontrak v0.4 + PRD v0.2 · Zena · fitur Catatan Makan Kemarin: entitas `FoodRecall`, `POST/GET /children/{id}/food-recalls`, field `diet` di `/status`, `food_recalls` di `/growth/evaluate`, kode alasan `NO_ANIMAL_SOURCE_FOOD`, `LOW_DIET_DIVERSITY`, `LOW_MEAL_FREQUENCY`, `NO_RECENT_FOOD_RECALL` · — · backend: tabel + endpoint; frontend: layar catatan makan; engine: indikator IYCF
- 08:37 · docs · Zena · menambah AGENTS.md, CLAUDE.md, CHANGELOG.md, HANDOFF.md · — · semua: baca AGENTS.md
- 08:31 · kontrak v0.3 · Zena · menambah `GET /api/v1/guides` untuk kartu GiziCerdas dan Stimulasi; PRD v0.1 ditulis · — · backend: siapkan `guides.id.json`; frontend: layar Panduan
- 08:29 · kontrak v0.2 · Zena · jaringan demo: engine di laptop Zena, Go membaca `ENGINE_URL` · — · backend
- 08:10 · kontrak v0.1 · Zena · draf awal kontrak · — · semua
