"""IYCF-style project screening from validated 24-hour recall history.

No portion/energy adequacy inference, diagnosis or parent-facing text. Survey
indicators are adapted to the project contract; see attributed local rules.
"""

import json
from pathlib import Path

from app.core.early_warning import evaluate_early_warning
from app.core.who_tables import WHOTables
from app.schemas.growth import ChildInput, FoodRecallInput, GrowthEvaluateRequest

_RULES = json.loads((Path(__file__).resolve().parents[2] / "data" / "iycf" / "rules.json").read_text(encoding="utf-8"))


def _age_months(child: ChildInput, on_date) -> float:
    return (on_date - child.birth_date).days / _RULES["age"]["days_per_month"]


def _eligible(age_months: float) -> bool:
    return _RULES["age"]["min_months"] <= age_months < _RULES["age"]["max_months_exclusive"]


def evaluate_food_recall(child: ChildInput, recall: FoodRecallInput) -> dict:
    """One recall, using age ON recall_date; field names match contract diet.

    Count distinct groups. Milk frequencies do not imply an unchecked dairy
    group, and animal-source-food here is eggs/flesh, not the dairy checkbox.
    MMF is independent of the separate WHO minimum milk frequency indicator.
    """
    age = _age_months(child, recall.recall_date)
    if not _eligible(age):
        raise ValueError("umur pada recall_date harus 6 sampai kurang dari 24 bulan")
    groups = set(recall.food_groups)
    group_count = len(groups) + int(recall.breastfed)
    rules = _RULES["mmf"]
    if recall.breastfed:
        minimum = rules["young_breastfed_min_meals"] if age < rules["older_breastfed_from_months"] else rules["older_breastfed_min_meals"]
        mmf = recall.meal_count >= minimum
    else:
        milk = recall.milk_feed_count if recall.milk_feed_count is not None else 0
        mmf = recall.meal_count >= rules["non_breastfed_min_solid_meals"] and recall.meal_count + milk >= rules["non_breastfed_min_feeds"]
    return {
        "recall_date": recall.recall_date.isoformat(),
        "group_count": group_count,
        "mdd": group_count >= _RULES["mdd_min_groups"],
        "mmf": mmf,
        "eff": bool(groups.intersection(_RULES["eff_food_groups"])),
    }


def evaluate_diet(request: GrowthEvaluateRequest) -> dict:
    """Latest eligible recall in last 14 calendar dates plus project reasons.

    Age at as_of controls whether diet warnings apply now; age on each recall
    controls indicator computation. Windows include as_of: age in days <N.
    Repeated failures in up to three last records may raise yellow even when
    the newest record improved; a single failure only matters if newest fails.
    """
    if not _eligible(_age_months(request.child, request.as_of)):
        return {"diet": None, "reasons": []}
    recalls = sorted((item for item in request.food_recalls if 0 <= (request.as_of - item.recall_date).days < _RULES["history_days"]), key=lambda item: item.recall_date, reverse=True)
    results = [evaluate_food_recall(request.child, item) for item in recalls]
    recent = results[:_RULES["pattern_last_records"]]
    reasons = []
    for metric, code in _RULES["reason_codes"].items():
        failures = sum(not row[metric] for row in recent)
        repeated = failures >= _RULES["pattern_min_failures"]
        if repeated or (recent and not recent[0][metric]):
            reasons.append({"code": code, "level": "yellow" if repeated else "info", "evidence": {
                "indicator": metric, "from_date": recent[-1]["recall_date"] if repeated else recent[0]["recall_date"], "to_date": recent[0]["recall_date"],
            }})
    if not recalls or (request.as_of - recalls[0].recall_date).days >= _RULES["recent_days"]:
        reasons.append({"code": _RULES["missing_reason"], "level": "info", "evidence": {"to_date": request.as_of.isoformat()}})
    return {"diet": results[0] if results else None, "reasons": reasons}


def evaluate_growth_and_diet(request: GrowthEvaluateRequest, tables: WHOTables) -> dict:
    """Compose Patch 06 and diet without replacing growth evidence or levels.

    Still not a complete public response (next_kpsp is added during endpoint
    integration). WHO errors propagate; no fake fallback or endpoint here.
    """
    growth = evaluate_early_warning(request, tables)
    diet = evaluate_diet(request)
    reasons = growth["reasons"] + diet["reasons"]
    level = "red" if any(r["level"] == "red" for r in reasons) else "yellow" if any(r["level"] == "yellow" for r in reasons) else "green"
    return {**growth, "diet": diet["diet"], "reasons": reasons, "level": level}
