"""HTTP adapters for the existing stateless cores; no clinical fallback."""

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.growth_math import lms_value_at_z
from app.core.iycf import evaluate_growth_and_diet
from app.core.kpsp import next_kpsp, runtime_questionnaire, score_kpsp
from app.core.who_tables import TABLE_SPECS, WHODataError, WHOTables, load_who_tables
from app.schemas.common import Envelope
from app.schemas.growth import GrowthEvaluateRequest, Sex
from app.schemas.kpsp import SCHEDULE, KpspScoreRequest

router = APIRouter()


def verified_tables() -> WHOTables:
    # Reverify the five local files on each request, including after setup or
    # replacement. No network access, cached patient state, or test fallback.
    return load_who_tables()


def invalid_field(location: tuple, message: str) -> None:
    raise RequestValidationError([
        {"loc": location, "msg": message, "type": "value_error"}
    ])


@router.post("/growth/evaluate", response_model=Envelope[dict])
def evaluate(payload: GrowthEvaluateRequest):
    for index, point in enumerate(payload.measurements):
        for field in ("length_height_cm", "head_circumference_cm"):
            value = getattr(point, field)
            if value is not None and Decimal(str(value)) * 10 % 1:
                invalid_field(("body", "measurements", index, field), "Ukuran cm harus pada grid 0,1 cm sesuai kontrak")
    try:
        schedule = next_kpsp(payload)
    except ValueError:
        invalid_field(("body", "as_of"), "Umur bulat KPSP pada as_of harus dalam cakupan 0–60 bulan")
    result = evaluate_growth_and_diet(payload, verified_tables())
    result["next_kpsp"] = schedule
    # Classifications, flags and warning decisions above use full precision.
    # Only serialised z-scores (including evidence) use contract precision.
    for point in result["per_measurement"]:
        point["z"] = {key: None if value is None else round(value, 2) for key, value in point["z"].items()}
    for reason in result["reasons"]:
        for key in ("from_z", "to_z"):
            if key in reason["evidence"]:
                reason["evidence"][key] = round(reason["evidence"][key], 2)
    return {"data": result, "error": None}


@router.post("/kpsp/score", response_model=Envelope[dict])
def score(payload: KpspScoreRequest):
    return {"data": score_kpsp(payload), "error": None}


@router.get("/kpsp/questionnaire", response_model=Envelope[dict])
def questionnaire(age_months: int):
    if age_months not in SCHEDULE:
        invalid_field(("query", "age_months"), "age_months harus salah satu umur jadwal KPSP pada kontrak")
    try:
        return {"data": runtime_questionnaire(age_months), "error": None}
    except ValueError:
        return JSONResponse(status_code=503, content={"data": None, "error": {
            "code": "ENGINE_UNAVAILABLE", "message": "Bank KPSP lokal tidak tersedia atau tidak valid", "fields": None}})


@router.get("/reference", response_model=Envelope[dict])
def reference(
    indicator: Literal["wfa", "lhfa", "hcfa", "wfl", "wfh"],
    sex: Sex,
    x_from: int = Query(ge=0),
    x_to: int = Query(ge=0),
):
    """x is age in days (wfa, lhfa, hcfa) or whole cm (wfl, wfh, contract v0.7).

    Go chooses wfl/wfh from the child's age; the engine never guesses it.
    Length tables are returned on their native 0,1 cm grid.
    """
    if x_to < x_from:
        invalid_field(("query", "x_to"), "x_to harus lebih besar atau sama dengan x_from")
    spec = TABLE_SPECS[indicator]
    step = 1 if spec.axis == "age" else 10
    first, last = x_from * step, x_to * step
    if first < spec.min_index or last > spec.max_index:
        raise WHODataError("Rentang yang diminta melampaui tabel WHO yang tersedia; tidak ada ekstrapolasi")
    tables = verified_tables()
    result = {key: [] for key in ("x", "sd_neg3", "sd_neg2", "median", "sd_pos2", "sd_pos3")}
    for index in range(first, last + 1):
        x = index if step == 1 else Decimal(index) / 10
        lms = tables.lookup(indicator, sex, x)
        result["x"].append(x if step == 1 else float(x))
        for key, z in (("sd_neg3", -3), ("sd_neg2", -2), ("median", 0), ("sd_pos2", 2), ("sd_pos3", 3)):
            result[key].append(lms_value_at_z(z, lms))
    return {"data": result, "error": None}
