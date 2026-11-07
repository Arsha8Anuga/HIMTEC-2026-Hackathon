"""HTTP adapters for the existing stateless cores; no clinical fallback."""

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Query
from fastapi.exceptions import RequestValidationError

from app.core.growth_math import lms_value_at_z
from app.core.iycf import evaluate_growth_and_diet
from app.core.kpsp import next_kpsp, score_kpsp
from app.core.who_tables import TABLE_SPECS, WHODataError, WHOTables, load_who_tables
from app.schemas.common import Envelope
from app.schemas.growth import GrowthEvaluateRequest, Sex
from app.schemas.kpsp import KpspScoreRequest

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


@router.get("/reference", response_model=Envelope[dict])
def reference(
    indicator: Literal["wfa", "lhfa", "hcfa", "wfl_wfh"],
    sex: Sex,
    x_from: int = Query(ge=0),
    x_to: int = Query(ge=0),
):
    if x_to < x_from:
        invalid_field(("query", "x_to"), "x_to harus lebih besar atau sama dengan x_from")
    if indicator == "wfl_wfh":
        # The contract supplies neither age nor position to distinguish WFL
        # from WFH. Do not concatenate incompatible curves or guess a table.
        raise WHODataError("Pemilihan WFL/WFH pada referensi belum ditetapkan dalam kontrak")
    spec = TABLE_SPECS[indicator]
    if x_from < spec.min_index or x_to > spec.max_index:
        raise WHODataError("Rentang yang diminta melampaui tabel WHO yang tersedia; tidak ada ekstrapolasi")
    tables = verified_tables()
    result = {key: [] for key in ("x", "sd_neg3", "sd_neg2", "median", "sd_pos2", "sd_pos3")}
    for day in range(x_from, x_to + 1):
        lms = tables.lookup(indicator, sex, day)
        result["x"].append(day)
        for key, z in (("sd_neg3", -3), ("sd_neg2", -2), ("median", 0), ("sd_pos2", 2), ("sd_pos3", 3)):
            result[key].append(lms_value_at_z(z, lms))
    return {"data": result, "error": None}
