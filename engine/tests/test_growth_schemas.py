"""Contract v0.4 schema tests; never fabricate WHO/KPSP reference values."""

from copy import deepcopy
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.growth import GrowthEvaluateRequest


@pytest.fixture()
def payload() -> dict:
    return {
        "as_of": "2026-01-15",
        "child": {"sex": "female", "birth_date": "2025-03-01"},
        "measurements": [
            {
                "id": "9b1d0c2e-0000-4000-8000-000000000001",
                "measured_at": "2026-01-15",
                "weight_kg": 8.1,
                "length_height_cm": 70.2,
                "position": "recumbent",
                "head_circumference_cm": None,
                "source": "posyandu",
            }
        ],
        "kpsp_results": [
            {
                "questionnaire_age_months": 9,
                "answered_at": "2025-12-01",
                "result": "sesuai",
            }
        ],
        "food_recalls": [
            {
                "recall_date": "2026-01-14",
                "breastfed": True,
                "food_groups": ["eggs", "grains_roots_tubers"],
                "meal_count": 3,
                "milk_feed_count": None,
            }
        ],
    }


def test_valid_v04_request(payload: dict) -> None:
    data = GrowthEvaluateRequest.model_validate(payload)
    assert data.child.sex == "female"
    assert len(data.measurements) == 1
    assert data.food_recalls[0].food_groups == ["eggs", "grains_roots_tubers"]
    assert data.model_dump(mode="json")["measurements"][0]["id"] == payload["measurements"][0]["id"]


def test_food_recalls_list_is_required_by_v04(payload: dict) -> None:
    del payload["food_recalls"]
    with pytest.raises(ValidationError, match="food_recalls"):
        GrowthEvaluateRequest.model_validate(payload)


def test_no_undocumented_fields(payload: dict) -> None:
    payload["child"]["age_months"] = 10.5
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        GrowthEvaluateRequest.model_validate(payload)


def test_position_required_with_length(payload: dict) -> None:
    payload["measurements"][0].pop("position")
    with pytest.raises(ValidationError, match="position wajib"):
        GrowthEvaluateRequest.model_validate(payload)


def test_length_may_be_missing_without_position(payload: dict) -> None:
    measurement = payload["measurements"][0]
    measurement.pop("length_height_cm")
    measurement.pop("position")
    assert GrowthEvaluateRequest.model_validate(payload).measurements[0].position is None


@pytest.mark.parametrize(
    ("field", "invalid"),
    [("weight_kg", 0.4), ("weight_kg", 40.1), ("weight_kg", "8.1"),
     ("length_height_cm", 39.9), ("head_circumference_cm", 61)],
)
def test_measurement_ranges_and_number_types(payload: dict, field: str, invalid: object) -> None:
    payload["measurements"][0][field] = invalid
    with pytest.raises(ValidationError):
        GrowthEvaluateRequest.model_validate(payload)


def test_future_measurement_relative_to_as_of(payload: dict) -> None:
    payload["measurements"][0]["measured_at"] = "2026-01-16"
    with pytest.raises(ValidationError, match="setelah as_of"):
        GrowthEvaluateRequest.model_validate(payload)


def test_measurement_cannot_precede_birth(payload: dict) -> None:
    payload["measurements"][0]["measured_at"] = "2025-02-28"
    with pytest.raises(ValidationError, match="sebelum birth_date"):
        GrowthEvaluateRequest.model_validate(payload)


def test_as_of_cannot_precede_birth(payload: dict) -> None:
    payload["as_of"] = "2025-02-28"
    with pytest.raises(ValidationError, match="as_of tidak boleh"):
        GrowthEvaluateRequest.model_validate(payload)


def test_invalid_food_groups_rejected(payload: dict) -> None:
    payload["food_recalls"][0]["food_groups"] = ["unverified_food_group"]
    with pytest.raises(ValidationError, match="food_groups"):
        GrowthEvaluateRequest.model_validate(payload)


def test_meal_count_outside_contract_range_rejected(payload: dict) -> None:
    payload["food_recalls"][0]["meal_count"] = 11
    with pytest.raises(ValidationError, match="meal_count"):
        GrowthEvaluateRequest.model_validate(payload)


def test_kpsp_outcome_enum_is_limited(payload: dict) -> None:
    payload["kpsp_results"][0]["result"] = "diagnosed"
    with pytest.raises(ValidationError, match="result"):
        GrowthEvaluateRequest.model_validate(payload)


def test_recalls_may_be_empty(payload: dict) -> None:
    payload["food_recalls"] = []
    assert GrowthEvaluateRequest.model_validate(payload).food_recalls == []


def test_recalls_cannot_be_after_as_of(payload: dict) -> None:
    payload["food_recalls"][0]["recall_date"] = "2026-01-16"
    with pytest.raises(ValidationError, match="recall_date"):
        GrowthEvaluateRequest.model_validate(payload)


def test_measured_age_cannot_exceed_who_scope(payload: dict) -> None:
    payload["food_recalls"], payload["kpsp_results"] = [], []
    measured = date.fromisoformat(payload["measurements"][0]["measured_at"])
    payload["child"]["birth_date"] = (measured - timedelta(days=1826)).isoformat()
    GrowthEvaluateRequest.model_validate(payload)  # hari 1826 = batas tabel WHO, diterima
    payload["child"]["birth_date"] = (measured - timedelta(days=1827)).isoformat()
    with pytest.raises(ValidationError, match="1826"):
        GrowthEvaluateRequest.model_validate(payload)


def test_food_recall_allows_optional_created_at_from_history(payload: dict) -> None:
    payload["food_recalls"][0]["created_at"] = "2026-01-15T09:00:00+07:00"
    assert GrowthEvaluateRequest.model_validate(payload).food_recalls[0].created_at is not None


def test_measurement_uuid_must_be_v4(payload: dict) -> None:
    payload["measurements"][0]["id"] = "9b1d0c2e-0000-1000-8000-000000000001"
    with pytest.raises(ValidationError, match="id"):
        GrowthEvaluateRequest.model_validate(payload)


@pytest.mark.parametrize("answered_at", ["2025-02-28", "2026-01-16"])
def test_kpsp_history_must_be_between_birth_and_as_of(payload: dict, answered_at: str) -> None:
    payload["kpsp_results"][0]["answered_at"] = answered_at
    with pytest.raises(ValidationError, match="answered_at"):
        GrowthEvaluateRequest.model_validate(payload)


def test_food_recall_cannot_precede_birth(payload: dict) -> None:
    payload["food_recalls"][0]["recall_date"] = "2025-02-28"
    with pytest.raises(ValidationError, match="sebelum birth_date"):
        GrowthEvaluateRequest.model_validate(payload)


@pytest.mark.parametrize("age_days, valid", [(182, False), (183, True), (730, True), (731, False)])
def test_food_recall_age_boundaries_use_contract_months(payload: dict, age_days: int, valid: bool) -> None:
    # CONTRACT v0.4: months = days / 30.4375; eligibility is [6, 24).
    birth = date(2024, 1, 1)
    payload["child"]["birth_date"] = birth.isoformat()
    payload["as_of"] = "2026-01-15"
    payload["measurements"] = []
    payload["kpsp_results"] = []
    payload["food_recalls"][0]["recall_date"] = (birth + timedelta(days=age_days)).isoformat()
    if valid:
        # Child is already older than 24 months at as_of; only recall age matters.
        assert GrowthEvaluateRequest.model_validate(payload).food_recalls
    else:
        with pytest.raises(ValidationError, match="umur pada recall_date"):
            GrowthEvaluateRequest.model_validate(payload)


def test_measurement_ids_must_be_unique_even_on_distinct_dates(payload: dict) -> None:
    duplicate = deepcopy(payload["measurements"][0])
    duplicate["measured_at"] = "2026-01-14"
    payload["measurements"].append(duplicate)
    with pytest.raises(ValidationError, match="id pengukuran tidak boleh duplikat"):
        GrowthEvaluateRequest.model_validate(payload)


def test_measurement_dates_must_be_unique_even_with_distinct_ids(payload: dict) -> None:
    duplicate = deepcopy(payload["measurements"][0])
    duplicate["id"] = "9b1d0c2e-0000-4000-8000-000000000002"
    payload["measurements"].append(duplicate)
    with pytest.raises(ValidationError, match="satu pengukuran per tanggal"):
        GrowthEvaluateRequest.model_validate(payload)


def test_food_recall_dates_must_be_unique(payload: dict) -> None:
    payload["food_recalls"].append(deepcopy(payload["food_recalls"][0]))
    with pytest.raises(ValidationError, match="satu catatan makan per tanggal"):
        GrowthEvaluateRequest.model_validate(payload)


def test_distinct_unsorted_history_is_preserved(payload: dict) -> None:
    earlier = deepcopy(payload["measurements"][0])
    earlier.update(id="9b1d0c2e-0000-4000-8000-000000000002", measured_at="2026-01-14")
    payload["measurements"].append(earlier)
    earlier_recall = deepcopy(payload["food_recalls"][0])
    earlier_recall["recall_date"] = "2026-01-13"
    payload["food_recalls"].append(earlier_recall)
    data = GrowthEvaluateRequest.model_validate(payload)
    assert [m.measured_at.isoformat() for m in data.measurements] == ["2026-01-15", "2026-01-14"]
    assert [r.recall_date.isoformat() for r in data.food_recalls] == ["2026-01-14", "2026-01-13"]
