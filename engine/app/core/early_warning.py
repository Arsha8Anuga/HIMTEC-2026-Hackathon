"""Stateless growth warnings, CONTRACT v0.4 + user's calendar-month policy.

Only returns codes/evidence; Go owns parent-facing text. IYCF remains Patch 08.
No endpoint is registered. Call after schema validation and verified WHO load.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal
import json
from math import fsum
from pathlib import Path

from app.core.growth_evaluation import evaluate_measurements
from app.core.who_tables import WHOTables
from app.schemas.growth import GrowthEvaluateRequest

_RULES = json.loads((Path(__file__).resolve().parents[2] / "data" / "early_warning.json").read_text(encoding="utf-8"))


def _reason(code: str, evidence: dict) -> dict:
    return {"code": code, "level": _RULES["levels"][code], "evidence": evidence}


def _month_index(day: date) -> int:
    return (day.year - 1) * 12 + day.month - 1


def _months_before(day: date, months: int) -> date:
    index = max(0, _month_index(day) - months)
    year, month = index // 12 + 1, index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def _pair_evidence(old, new, indicator=None):
    evidence = {"from_date": old[0].measured_at.isoformat(), "to_date": new[0].measured_at.isoformat()}
    if indicator is not None:
        evidence.update(indicator=indicator, from_z=old[1]["z"][indicator], to_z=new[1]["z"][indicator])
    return evidence


def _monthly_weight_reason(valid, latest):
    # Calendar months, not an inferred 30-day interval. Same-month repeats
    # are collapsed only for 1T/2T; no points are removed from other analyses.
    monthly = {_month_index(m.measured_at): (m, p) for m, p in valid}
    month = _month_index(latest[0].measured_at)
    previous = monthly.get(month - 1)
    if previous is None:
        return None

    def not_gaining(a, b):
        gain = (Decimal(str(b[0].weight_kg)) - Decimal(str(a[0].weight_kg))) * 1000
        return gain <= Decimal(str(_RULES["temporary_weight_gain_limit_g"]))

    if not not_gaining(previous, latest):
        return None
    earlier = monthly.get(month - 2)
    if earlier is not None and not_gaining(earlier, previous):
        return _reason("WEIGHT_NOT_GAINING_2X", _pair_evidence(earlier, latest))
    return _reason("WEIGHT_NOT_GAINING", _pair_evidence(previous, latest))


def _crossing_reasons(valid, latest):
    rules = _RULES["crossing"]
    result = []
    for indicator in ("wfa", "lhfa"):
        current = latest[1]["z"][indicator]
        if current is None:
            continue
        candidates = [
            pair for pair in valid
            if rules["min_days"] <= (latest[0].measured_at - pair[0].measured_at).days <= rules["max_days"]
            and pair[1]["z"][indicator] is not None
            and Decimal(str(pair[1]["z"][indicator])) - Decimal(str(current)) >= Decimal(str(rules["drop_z"]))
        ]
        if candidates:
            # Any qualifying comparison activates the rule. Choose the largest
            # observed drop as evidence, latest date breaks ties deterministically.
            previous = max(candidates, key=lambda pair: (pair[1]["z"][indicator], pair[0].measured_at))
            result.append(_reason("CROSSING_DOWN", _pair_evidence(previous, latest, indicator)))
    return result


def _projection_reason(valid, latest, as_of):
    rules = _RULES["projection"]
    current = latest[1]["z"]["lhfa"]
    if current is None or current < rules["cutoff_z"]:
        return None
    cutoff = _months_before(as_of, rules["history_months"])
    pairs = [pair for pair in valid if cutoff <= pair[0].measured_at <= as_of and pair[1]["z"]["lhfa"] is not None]
    if len(pairs) < rules["min_points"]:
        return None
    xs = [(pair[0].measured_at - as_of).days for pair in pairs]
    ys = [pair[1]["z"]["lhfa"] for pair in pairs]
    mean_x, mean_y = fsum(xs) / len(xs), fsum(ys) / len(ys)
    denominator = fsum((x - mean_x) ** 2 for x in xs)
    if denominator == 0:
        return None
    slope = fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denominator
    if slope >= 0:
        return None
    intercept = mean_y - slope * mean_x
    crossing_days = (rules["cutoff_z"] - intercept) / slope
    if not 0 < crossing_days <= rules["horizon_days"]:
        return None
    horizon = min(rules["horizon_days"], (date.max - as_of).days)
    return _reason("PROJECTED_STUNTING", {
        "indicator": "lhfa", "from_z": current, "to_z": intercept + slope * horizon,
        "from_date": latest[0].measured_at.isoformat(), "to_date": (as_of + timedelta(days=horizon)).isoformat(),
    })


def evaluate_early_warning(request: GrowthEvaluateRequest, tables: WHOTables) -> dict:
    """Growth/KPSP-history reasons only; incomplete public evaluation until IYCF.

    Latest implausible measurement is reported, never replaced by an older
    apparently normal point. All flagged history is excluded from all trends.
    Missing months break consecutive-month weight comparisons. Raw WHO domain
    errors propagate from Patch 05 and are not converted to a green result.
    """
    points = evaluate_measurements(request, tables)
    history = sorted(zip(request.measurements, points), key=lambda pair: pair[0].measured_at)
    valid = [pair for pair in history if "IMPLAUSIBLE_VALUE" not in pair[1]["flags"]]
    reasons = []
    if history:
        latest = history[-1]
        measured, evaluated = latest
        if measured.source == "home":
            reasons.append(_reason("HOME_MEASUREMENT", {"to_date": measured.measured_at.isoformat()}))
        if "IMPLAUSIBLE_VALUE" in evaluated["flags"]:
            reasons.append(_reason("IMPLAUSIBLE_VALUE", {"to_date": measured.measured_at.isoformat()}))
        else:
            for indicator, mapping in _RULES["classification_reasons"].items():
                code = mapping.get(evaluated["classification"][indicator])
                if code:
                    reasons.append(_reason(code, {"indicator": indicator, "to_z": evaluated["z"][indicator], "to_date": measured.measured_at.isoformat()}))
            weight_reason = _monthly_weight_reason(valid, latest)
            if weight_reason:
                reasons.append(weight_reason)
            reasons.extend(_crossing_reasons(valid, latest))
            projection = _projection_reason(valid, latest, request.as_of)
            if projection:
                reasons.append(projection)
    recent_length = any(pair[1]["z"]["lhfa"] is not None and (request.as_of - pair[0].measured_at).days <= _RULES["recent_length_days"] for pair in valid)
    if not recent_length:
        reasons.append(_reason("NO_RECENT_LENGTH", {"to_date": request.as_of.isoformat()}))
    if request.kpsp_results:
        latest_kpsp = max(request.kpsp_results, key=lambda item: (item.answered_at, item.questionnaire_age_months))
        code = _RULES["kpsp_reasons"].get(latest_kpsp.result)
        if code:
            reasons.append(_reason(code, {"to_date": latest_kpsp.answered_at.isoformat()}))
    level = "red" if any(r["level"] == "red" for r in reasons) else "yellow" if any(r["level"] == "yellow" for r in reasons) else "green"
    return {"per_measurement": points, "level": level, "reasons": reasons}
