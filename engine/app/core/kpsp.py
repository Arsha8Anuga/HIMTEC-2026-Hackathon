"""KPSP scoring and strict local bank loader; no invented questionnaire text.

Calendar-to-age and next_kpsp/due are intentionally not guessed. Only the
literal contract rounding primitive is supplied while the day-16 conflict is
pending. No router is registered by this preparatory patch.
"""

import json
from pathlib import Path

from app.schemas.kpsp import KpspQuestionnaire, KpspScoreRequest, SCHEDULE

_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "kpsp"
_RULES = json.loads((_DIRECTORY / "rules.json").read_text(encoding="utf-8"))


def score_kpsp(request: KpspScoreRequest) -> dict:
    yes_count = sum(item.answer for item in request.answers)
    result = next(band["result"] for band in _RULES["score_bands"] if yes_count >= band["min_yes"])
    return {"yes_count": yes_count, "result": result}


def round_kpsp_months(completed_months: int, remainder_days: int) -> int:
    """Literal CONTRACT v0.4 (>16). Accept already calculated age components.

    Does not assume days/30.4375 is appropriate for clinical KPSP age. This
    primitive must not be wired to a public schedule until the team resolves
    exactly 16 days and specifies the calendar-to-components calculation.
    """
    if type(completed_months) is not int or completed_months < 0:
        raise ValueError("completed_months harus bilangan bulat tidak negatif")
    if type(remainder_days) is not int or not 0 <= remainder_days <= 30:
        raise ValueError("remainder_days harus bilangan bulat 0 sampai 30")
    return completed_months + int(remainder_days > _RULES["round_up_after_days"])


def select_kpsp_age(rounded_months: int) -> int | None:
    """Closest scheduled age not older than the child; None below first age.

    An age beyond the project's supported schedule is rejected rather than
    silently extending screening beyond scope.
    """
    if type(rounded_months) is not int or not 0 <= rounded_months <= max(SCHEDULE):
        raise ValueError("umur di luar cakupan KPSP proyek")
    return max((age for age in SCHEDULE if age <= rounded_months), default=None)


def load_kpsp_bank(path: Path = _DIRECTORY / "questionnaires.json") -> dict[int, KpspQuestionnaire]:
    """Require attribution and a complete 14-age bank supplied/verified by team.

    Format: {source: {title, url, verified_on}, questionnaires: [{...}]}.
    Missing data is a failure, never a synthetic fallback. Schema validation
    checks structure only; it does not establish clinical authenticity.
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
        return bank
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise ValueError(f"Bank KPSP tidak tersedia atau tidak valid: {exc}") from exc
