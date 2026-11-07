"""KPSP scoring and strict local bank loader; no invented questionnaire text.

Age components follow the team's SDIDTK 2022 Markdown (30-day borrowing).
The user confirmed rounding upward at exactly 16 remaining days. Questionnaire
text was transcribed, but runtime delivery stays blocked pending figure review.
"""

import json
from datetime import date
from pathlib import Path

from app.schemas.kpsp import KpspQuestionnaire, KpspScoreRequest, SCHEDULE
from app.schemas.growth import GrowthEvaluateRequest

_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "kpsp"
_RULES = json.loads((_DIRECTORY / "rules.json").read_text(encoding="utf-8"))


def score_kpsp(request: KpspScoreRequest) -> dict:
    yes_count = sum(item.answer for item in request.answers)
    result = next(band["result"] for band in _RULES["score_bands"] if yes_count >= band["min_yes"])
    return {"yes_count": yes_count, "result": result}


def round_kpsp_months(completed_months: int, remainder_days: int) -> int:
    """Contract v0.5 draft: round upward from exactly 16 remaining days."""
    if type(completed_months) is not int or completed_months < 0:
        raise ValueError("completed_months harus bilangan bulat tidak negatif")
    if type(remainder_days) is not int or not 0 <= remainder_days <= _RULES["borrow_month_days"]:
        raise ValueError("remainder_days harus bilangan bulat 0 sampai 30")
    return completed_months + int(remainder_days >= _RULES["round_up_from_days"])


def select_kpsp_age(rounded_months: int) -> int | None:
    """Closest scheduled age not older than the child; None below first age.

    An age beyond the project's supported schedule is rejected rather than
    silently extending screening beyond scope.
    """
    if type(rounded_months) is not int or not 0 <= rounded_months <= max(SCHEDULE):
        raise ValueError("umur di luar cakupan KPSP proyek")
    return max((age for age in SCHEDULE if age <= rounded_months), default=None)


def kpsp_age_components(birth_date: date, as_of: date) -> tuple[int, int]:
    """SDIDTK 2022 p117: borrow 30 days and 12 months, no preterm correction.

    This is distinct from growth display age (days / 30.4375). In particular,
    do not substitute real previous-month length or anniversary clamping.
    """
    if type(birth_date) is not date or type(as_of) is not date or as_of < birth_date:
        raise ValueError("Tanggal KPSP tidak valid atau sebelum tanggal lahir")
    months = (as_of.year - birth_date.year) * 12 + as_of.month - birth_date.month
    days = as_of.day - birth_date.day
    if days < 0:
        days += _RULES["borrow_month_days"]
        months -= 1
    return months, days


def next_kpsp(request: GrowthEvaluateRequest) -> dict:
    """Project schedule (3..60), not a claim all forms are routine SDIDTK visits.

    Below 3 rounded months: upcoming 3-month form, not due. A completed normal
    target moves to the next scheduled age, not due until age-eligible. At the
    terminal age keep 60/not due. A doubtful latest result repeats its previous
    form at 14 days, following SDIDTK p119; deviation stays not due because the
    guideline calls for referral, not automatic self-rescreening.
    """
    months, days = kpsp_age_components(request.child.birth_date, request.as_of)
    target = select_kpsp_age(round_kpsp_months(months, days))
    if target is None:
        return {"questionnaire_age_months": min(SCHEDULE), "due": False}
    if not request.kpsp_results:
        return {"questionnaire_age_months": target, "due": True}
    latest = max(request.kpsp_results, key=lambda item: (item.answered_at, item.questionnaire_age_months))
    if latest.result == "meragukan":
        return {"questionnaire_age_months": latest.questionnaire_age_months,
                "due": (request.as_of - latest.answered_at).days >= _RULES["repeat_after_days"]}
    if latest.result == "penyimpangan":
        return {"questionnaire_age_months": latest.questionnaire_age_months, "due": False}
    completed = any(item.questionnaire_age_months == target and item.result == "sesuai" for item in request.kpsp_results)
    if completed:
        following = min((age for age in SCHEDULE if age > target), default=target)
        return {"questionnaire_age_months": following, "due": False}
    return {"questionnaire_age_months": target, "due": True}


def load_kpsp_bank(path: Path = _DIRECTORY / "questionnaires.json", *, for_review: bool = False) -> dict[int, KpspQuestionnaire]:
    """Require attribution and a complete 14-age bank supplied/verified by team.

    Format: {source: {title, url, verified_on}, questionnaires: [{...}]}.
    Missing data is a failure, never a synthetic fallback. Runtime load requires
    visual/clinical verification metadata; only explicit for_review=True opens
    unverified transcription. Metadata is an audit record, not automatic proof.
    """
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {"source", "questionnaires"}:
            raise ValueError("Format bank KPSP tidak cocok")
        source = data["source"]
        if not isinstance(source, dict) or any(not isinstance(source.get(key), str) or not source[key].strip() for key in ("title", "url", "verified_on")):
            raise ValueError("Sumber bank KPSP wajib dicatat")
        if not isinstance(data["questionnaires"], list):
            raise ValueError("questionnaires harus daftar")
        bank = {}
        for item in data["questionnaires"]:
            questionnaire = KpspQuestionnaire.model_validate(item)
            age = questionnaire.questionnaire_age_months
            if age in bank:
                raise ValueError("Umur kuesioner duplikat")
            bank[age] = questionnaire
        if set(bank) != set(SCHEDULE):
            raise ValueError("Bank KPSP belum lengkap untuk seluruh umur kontrak")
        if not for_review and (source.get("visual_assets_status") != "verified" or source.get("clinical_review_status") != "verified"):
            raise ValueError("Bank KPSP belum siap tayang: verifikasi gambar dan isi klinis belum lengkap")
        return bank
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise ValueError(f"Bank KPSP tidak tersedia atau tidak valid: {exc}") from exc
