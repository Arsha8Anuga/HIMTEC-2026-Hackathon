"""Reproducible transcription of the team's supplied SDIDTK Markdown.

No clinical text is generated: join wrapped source lines, remove page furniture
and formatting fences, map printed aspect labels to contract enums. Images are
absent from this Markdown; the resulting bank is blocked for runtime delivery.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

_RULES = json.loads((Path(__file__).resolve().parents[1] / "data" / "kpsp" / "rules.json").read_text(encoding="utf-8"))
AGES = tuple(_RULES["schedule_months"])
ITEM_COUNT = _RULES["answer_count"]
ASPECTS = {"Gerak kasar": "gerak_kasar", "Gerak halus": "gerak_halus", "Bicara dan bahasa": "bicara_bahasa", "Sosialisasi dan kemandirian": "sosialisasi_kemandirian"}
HEADING = re.compile(r"^Kuesioner Pra Skrining Perkembangan \(KPSP\) (?:Bayi|Anak) Umur (\d+) Bulan\s*$", re.M)
ITEM = re.compile(r"^(\d{1,2})\s*\n?\.\s*", re.M)
ASPECT = re.compile(r"Gerak\s+kasar|Gerak\s+halus|Bicara\s+dan\s+bahasa|Sosialisasi\s+dan\s+kemandirian")


def transcribe(path: Path) -> dict:
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig")
    headings = list(HEADING.finditer(text))
    bank, page_ranges, visuals, equipment = [], {}, {}, {}
    for index, heading in enumerate(headings):
        age = int(heading.group(1))
        if age not in AGES:
            continue
        if any(q["questionnaire_age_months"] == age for q in bank):
            raise ValueError(f"Duplicate source form: {age}")
        body = text[heading.end():headings[index + 1].start() if index + 1 < len(headings) else len(text)]
        cleaned = []
        pages = []
        # Printed page immediately preceding the heading.
        preceding_pages = re.findall(r"^\d{2,3}\s*$", text[:heading.start()], re.M)
        if preceding_pages:
            pages.append(int(preceding_pages[-1]))
        for line in body.splitlines():
            stripped = line.strip()
            if re.fullmatch(r"\d{3}", stripped):
                pages.append(int(stripped)); continue
            if not stripped or stripped.startswith("```"):
                continue
            if stripped in ("PEDOMAN PELAKSANAAN", "Stimulasi, Deteksi, dan Intervensi Dini Tumbuh Kembang Anak di Tingkat Pelayanan Kesehatan Dasar"):
                continue
            if stripped.startswith(("Lihat algoritme", "Perinci untuk aspek")):
                continue
            if stripped.startswith("o "):
                equipment.setdefault(str(age), []).append(stripped); continue
            cleaned.append(stripped)
        body = "\n".join(cleaned)
        starts = list(ITEM.finditer(body))
        if [int(m.group(1)) for m in starts] != list(range(1, ITEM_COUNT + 1)):
            raise ValueError(f"Source must contain items 1..10 in order: age {age}")
        items = []
        for i, match in enumerate(starts):
            item_body = body[match.end():starts[i + 1].start() if i + 1 < len(starts) else len(body)]
            aspects = list(ASPECT.finditer(item_body))
            if len(aspects) != 1:
                raise ValueError(f"Ambiguous/missing aspect: age {age}, item {i+1}")
            aspect = aspects[0]
            question = re.sub(r"\s+", " ", item_body[:aspect.start()] + item_body[aspect.end():]).strip()
            if not question:
                raise ValueError("Empty question")
            items.append({"item_no": i+1, "aspect": ASPECTS[re.sub(r"\s+", " ", aspect.group())], "question": question})
            if re.search(r"seperti (?:pada )?gambar|gambar (?:di (?:bawah|atas)|kedua garis|ini)|contoh|garis seperti ini|Jawaban [‘']Ya[’']\s*:", question, re.I):
                visuals.setdefault(str(age), []).append(i+1)
        # The final page number precedes the NEXT heading, so it belongs to
        # that form. Keep only the current form's observed printed pages.
        if index + 1 < len(headings) and len(pages) > 1:
            pages.pop()
        page_ranges[str(age)] = sorted(set(pages))
        bank.append({"questionnaire_age_months": age, "items": items})
    if {q["questionnaire_age_months"] for q in bank} != set(AGES):
        raise ValueError("Source does not contain every contract age")
    return {"source": {
        "title": "Pedoman Pelaksanaan SDIDTK, revisi 23 Agustus 2022 — transkripsi Markdown unggahan tim",
        "url": "https://apgpaud.org/wp-content/uploads/2023/02/BUKU-PEDOMAN-SDIDTK-revisi-23082022.pdf",
        "verified_on": "2026-11-07", "input_filename": Path(path).name,
        "input_sha256": sha256(raw).hexdigest(),
        "visual_assets_status": "missing", "clinical_review_status": "text_transcription_only",
        "image_dependent_items": visuals, "observed_printed_pages": page_ranges,
        "equipment_source_lines": equipment,
        "note": "140 questions transcribed from user-provided text. No original figures available; runtime delivery is blocked pending visual and clinical verification. Ages 66/72 excluded by project scope."
    }, "questionnaires": sorted(bank, key=lambda q: q["questionnaire_age_months"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    bank = transcribe(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Transcribed {len(bank['questionnaires'])} forms, 140 items; runtime blocked: images missing")
