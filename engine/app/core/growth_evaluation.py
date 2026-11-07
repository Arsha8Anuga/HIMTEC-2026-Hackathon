"""Patch 05: core per-measurement evaluation; no endpoint/status/trend yet.

    Full precision is retained for downstream risk comparisons. Formatting to
    two decimals belongs to the eventual API edge. Reference domain errors
    propagate; unavailable WHO values must never become fabricated normal data.
"""

from app.core.anthropometry import classify, is_implausible
from app.core.growth_math import correct_length_height_cm, lms_zscore, restricted_lms_zscore
from app.core.who_tables import WHOTables
from app.schemas.growth import ChildInput, GrowthEvaluateRequest, MeasurementInput


def evaluate_measurement(child: ChildInput, measurement: MeasurementInput, tables: WHOTables) -> dict:
    age_days = (measurement.measured_at - child.birth_date).days
    if age_days < 0:
        raise ValueError("measured_at tidak boleh sebelum birth_date")
    sex = child.sex
    z = {
        "wfa": restricted_lms_zscore(measurement.weight_kg, tables.lookup("wfa", sex, age_days)),
        "lhfa": None,
        "wfl_wfh": None,
        "hcfa": None,
    }
    corrected = None
    if measurement.length_height_cm is not None:
        corrected = correct_length_height_cm(age_days, measurement.length_height_cm, measurement.position)
        z["lhfa"] = lms_zscore(corrected, tables.lookup("lhfa", sex, age_days))
        indicator = "wfl" if age_days < 731 else "wfh"
        # Exact lookup follows the current contract's one-decimal input.
        # No silent rounding/interpolation/extrapolation pending team decisions.
        z["wfl_wfh"] = restricted_lms_zscore(measurement.weight_kg, tables.lookup(indicator, sex, corrected))
    if measurement.head_circumference_cm is not None:
        z["hcfa"] = lms_zscore(measurement.head_circumference_cm, tables.lookup("hcfa", sex, age_days))
    flagged = any(is_implausible(indicator, z[indicator]) for indicator in ("wfa", "lhfa", "wfl_wfh") if z[indicator] is not None)
    classification = {
        indicator: None if flagged or z[indicator] is None else classify(indicator, z[indicator])
        for indicator in ("wfa", "lhfa", "wfl_wfh")
    }
    return {
        "id": str(measurement.id),
        "age_days": age_days,
        "corrected_length_cm": corrected,
        "z": z,
        "classification": classification,
        "flags": ["IMPLAUSIBLE_VALUE"] if flagged else [],
    }


def evaluate_measurements(request: GrowthEvaluateRequest, tables: WHOTables) -> list[dict]:
    """Evaluate all validated history in input order, with no state or mutation.

    Future trend code must exclude points containing IMPLAUSIBLE_VALUE. The
    caller loads authentic WHO tables once and shares them across this batch.
    """
    return [evaluate_measurement(request.child, point, tables) for point in request.measurements]
