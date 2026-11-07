"""Pure WHO growth arithmetic (no HTTP, persistence, or clinical classification).

Based on WHO/anthro, pinned upstream commit
b776d8a12b1c97369c748b561159fd2ec4f4db58:
  R/z-score-helper.R (compute_zscore, compute_zscore_adjusted, adjust_lenhei)
  R/z-score-weight-for-lenhei.R (linear interpolation of LMS parameters).

These functions do not classify or return diagnoses. Inputs to clinical APIs
must be validated against authentic WHO references and the project contract.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from math import exp, expm1, isfinite, log

from app.core.who_tables import LMS, TABLE_SPECS, WHODataError, WHOTables


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{label} harus berupa angka")
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{label} bukan angka yang valid") from exc
    if not isfinite(number):
        raise ValueError(f"{label} harus berupa angka terhingga")
    return number


def _checked_lms(lms: LMS) -> tuple[float, float, float]:
    if not isinstance(lms, LMS):
        raise ValueError("Parameter LMS tidak valid")
    l = _finite_number(lms.l, "L")
    m = _finite_number(lms.m, "M")
    s = _finite_number(lms.s, "S")
    if m <= 0 or s <= 0:
        raise ValueError("Parameter M dan S wajib positif")
    return l, m, s


def lms_zscore(measurement: float, lms: LMS) -> float:
    """Raw LMS z-score, including the logarithmic limit L == 0.

    Returns full precision. Rounding to two decimals belongs at the API edge,
    not inside the computation or risk comparisons.
    """
    x = _finite_number(measurement, "Pengukuran")
    l, m, s = _checked_lms(lms)
    if x <= 0:
        raise ValueError("Pengukuran harus positif")
    ratio_log = log(x / m)
    try:
        result = ratio_log / s if l == 0 else expm1(l * ratio_log) / (l * s)
    except (OverflowError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("LMS di luar domain numerik") from exc
    if not isfinite(result):
        raise ValueError("Hasil LMS tidak terhingga")
    return result


def lms_value_at_z(z: float, lms: LMS) -> float:
    """Inverse LMS, e.g. standard reference lines at -3/-2/0/+2/+3 SD."""
    score = _finite_number(z, "Z-score")
    l, m, s = _checked_lms(lms)
    base = 1 + l * s * score
    if l != 0 and base <= 0:
        raise ValueError("Z-score di luar domain parameter LMS")
    try:
        result = m * (exp(score * s) if l == 0 else base ** (1 / l))
    except (OverflowError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("Invers LMS di luar domain numerik") from exc
    if not isfinite(result) or result <= 0:
        raise ValueError("Hasil invers LMS tidak valid")
    return result


def restricted_lms_zscore(measurement: float, lms: LMS) -> float:
    """WHO adjusted/restricted LMS for weight-related indicators (wfa/wfl/wfh).

    Outside +/-3 SD, continue *linearly in measurements*, using the width
    of the adjoining 2-to-3 SD interval, as in WHO Anthro's compute_zscore_adjusted.
    Non-weight indicators (lhfa, hcfa) must call lms_zscore instead.
    """
    raw = lms_zscore(measurement, lms)
    if -3 <= raw <= 3:
        return raw
    x = _finite_number(measurement, "Pengukuran")
    if raw > 3:
        x3 = lms_value_at_z(3, lms)
        x2 = lms_value_at_z(2, lms)
        width = x3 - x2
        if width <= 0:
            raise ValueError("Lebar interval WHO +2/+3 tidak valid")
        return 3 + (x - x3) / width
    xneg3 = lms_value_at_z(-3, lms)
    xneg2 = lms_value_at_z(-2, lms)
    width = xneg2 - xneg3
    if width <= 0:
        raise ValueError("Lebar interval WHO -3/-2 tidak valid")
    return -3 + (x - xneg3) / width


def correct_length_height_cm(
    age_days: int, length_height_cm: float, position: str
) -> float:
    """Project CONTRACT v0.4: recumbent below day 731, standing from 731.

    This project contract does not include WHO Anthro's separate <9-month
    standing-measurement quality flag; decide that rule before API integration.
    """
    if isinstance(age_days, bool) or not isinstance(age_days, int) or age_days < 0:
        raise ValueError("Umur harus bilangan hari yang tidak negatif")
    measured = _finite_number(length_height_cm, "Panjang/tinggi")
    if measured <= 0:
        raise ValueError("Panjang/tinggi harus positif")
    if position not in ("recumbent", "standing"):
        raise ValueError("Posisi ukur wajib recumbent atau standing")
    if age_days < 731 and position == "standing":
        return measured + 0.7
    if age_days >= 731 and position == "recumbent":
        return measured - 0.7
    return measured


def interpolate_length_lms(
    tables: WHOTables, indicator: str, sex: str, length_height_cm: float
) -> LMS:
    """Linearly interpolate WHO LMS rows on the 0.1-cm grid.

    Matches the WHO Anthro R weighting method for WFL/WFH; no extrapolation.
    Kept as a separate primitive pending team approval of precision policy.
    """
    if indicator not in ("wfl", "wfh"):
        raise ValueError("Interpolasi hanya untuk wfl atau wfh")
    if isinstance(length_height_cm, bool):
        raise WHODataError("Koordinat WHO tidak valid")
    try:
        x = Decimal(str(length_height_cm)) * 10
    except (InvalidOperation, ValueError) as exc:
        raise WHODataError("Koordinat WHO tidak valid") from exc
    if not x.is_finite():
        raise WHODataError("Koordinat WHO tidak valid")
    spec = TABLE_SPECS[indicator]
    if x < spec.min_index or x > spec.max_index:
        raise WHODataError("Koordinat di luar tabel referensi WHO")
    floor_index = int(x.to_integral_value(rounding=ROUND_FLOOR))
    lower = tables.lookup(indicator, sex, Decimal(floor_index) / 10)
    if x == floor_index:  # Includes exact maximum; no out-of-bounds upper lookup.
        return lower
    upper = tables.lookup(indicator, sex, Decimal(floor_index + 1) / 10)
    fraction = float(x - floor_index)
    return LMS(
        l=lower.l + fraction * (upper.l - lower.l),
        m=lower.m + fraction * (upper.m - lower.m),
        s=lower.s + fraction * (upper.s - lower.s),
    )
