"""Classification/flag thresholds read from attributed local data, never HTTP."""

import json
from math import isfinite
from pathlib import Path

_RULES = json.loads((Path(__file__).resolve().parents[2] / "data" / "anthropometry.json").read_text(encoding="utf-8"))


def _check_score(indicator: str, score: float) -> None:
    if indicator not in _RULES["classification"]:
        raise ValueError("Indikator klasifikasi tidak dikenal")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not isfinite(score):
        raise ValueError("Z-score harus berupa angka terhingga")


def is_implausible(indicator: str, score: float) -> bool:
    _check_score(indicator, score)
    lower, upper = _RULES["plausibility"][indicator]
    return score < lower or score > upper


def classify(indicator: str, score: float) -> str | None:
    """Unrounded score; equality at each limit follows Permenkes 2/2020.

    None means implausible, not normal. HCFA is intentionally not classified.
    """
    if is_implausible(indicator, score):
        return None
    for band in _RULES["classification"][indicator]:
        upper = band["upper"]
        if upper is None or score < upper or (band["inclusive"] and score == upper):
            return band["value"]
    raise ValueError("Data klasifikasi tidak lengkap")
