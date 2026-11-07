"""HTTP protocol, real WHO calculations, and explicit unavailable domains."""

from copy import deepcopy
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.growth_math import lms_value_at_z
from app.core.who_tables import WHO_DATA_DIR, WHO_SOURCE_BLOBS, WHODataError, load_who_tables
from app.main import create_app


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as value:
        yield value


@pytest.fixture
def tables():
    if not all((WHO_DATA_DIR / name).is_file() for name in WHO_SOURCE_BLOBS):
        pytest.skip("Official WHO files are not installed")
    return load_who_tables()


def payload():
    return {
        "as_of": "2026-01-15",
        "child": {"sex": "female", "birth_date": "2025-03-01"},
        "measurements": [], "kpsp_results": [], "food_recalls": [],
    }


def score_payload(count):
    return {"questionnaire_age_months": 9,
            "answers": [{"item_no": i, "answer": i <= count} for i in range(1, 11)]}


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == code
    assert "detail" not in body


@pytest.mark.parametrize("count,result", [(10, "sesuai"), (9, "sesuai"), (8, "meragukan"), (7, "meragukan"), (6, "penyimpangan"), (0, "penyimpangan")])
def test_score_bands_work_without_who_or_questionnaire_bank(client, count, result):
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not needed")):
        response = client.post("/engine/v1/kpsp/score", json=score_payload(count))
    assert response.status_code == 200
    assert response.json() == {"data": {"yes_count": count, "result": result}, "error": None}


@pytest.mark.parametrize("change", ["duplicate", "short", "boolean_number", "invalid_age", "extra"])
def test_invalid_score_rejected(client, change):
    body = score_payload(10)
    if change == "duplicate":
        body["answers"][-1]["item_no"] = 1
    elif change == "short":
        body["answers"].pop()
    elif change == "boolean_number":
        body["answers"][0]["answer"] = 1
    elif change == "invalid_age":
        body["questionnaire_age_months"] = 10
    else:
        body["answered_at"] = "2026-01-15"
    assert_error(client.post("/engine/v1/kpsp/score", json=body), 422, "VALIDATION_ERROR")


def test_registered_routes_v07(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/engine/v1/health", "/engine/v1/growth/evaluate", "/engine/v1/kpsp/score",
                          "/engine/v1/kpsp/questionnaire", "/engine/v1/reference"}


def test_bad_body_validation_does_not_depend_on_who_files(client):
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.post("/engine/v1/growth/evaluate", json={})
    assert_error(response, 422, "VALIDATION_ERROR")
    assert "child" in response.json()["error"]["fields"]


def test_missing_or_corrupt_tables_are_not_a_green_result(client):
    with patch("app.api.evaluation.verified_tables", side_effect=WHODataError("private/path/test")):
        response = client.post("/engine/v1/growth/evaluate", json=payload())
    assert_error(response, 503, "ENGINE_UNAVAILABLE")
    assert "private/path" not in response.text


def test_unexpected_exception_is_sanitized(client):
    with patch("app.api.evaluation.verified_tables", side_effect=RuntimeError("private-data")):
        response = client.post("/engine/v1/growth/evaluate", json=payload())
    assert_error(response, 500, "INTERNAL")
    assert "private-data" not in response.text


@pytest.mark.parametrize("query", ["indicator=bad&sex=female&x_from=0&x_to=10", "indicator=lhfa&sex=other&x_from=0&x_to=10", "indicator=lhfa&sex=female&x_from=1.5&x_to=10", "indicator=lhfa&sex=female&x_from=-1&x_to=10", "indicator=lhfa&sex=female&x_from=10&x_to=9", "indicator=lhfa&sex=female&x_from=0", "indicator=wfl_wfh&sex=female&x_from=50&x_to=60"])
def test_reference_validation_without_data(client, query):
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.get("/engine/v1/reference?" + query)
    assert_error(response, 422, "VALIDATION_ERROR")


@pytest.mark.parametrize("indicator,to", [("wfl", 111), ("wfl", 44), ("wfh", 64), ("wfh", 121), ("wfa", 1856)])
def test_unsupported_reference_domain_never_guesses_or_extrapolates(client, indicator, to):
    start = to if indicator in ("wfl", "wfh") else 0
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.get(f"/engine/v1/reference?indicator={indicator}&sex=female&x_from={start}&x_to={to}")
    assert_error(response, 503, "ENGINE_UNAVAILABLE")


def test_reference_missing_data(client):
    with patch("app.api.evaluation.verified_tables", side_effect=WHODataError("missing")):
        response = client.get("/engine/v1/reference?indicator=lhfa&sex=female&x_from=0&x_to=10")
    assert_error(response, 503, "ENGINE_UNAVAILABLE")


@pytest.mark.parametrize("indicator", ["wfa", "lhfa", "hcfa"])
@pytest.mark.parametrize("sex", ["male", "female"])
def test_reference_matches_real_who_and_includes_both_endpoints(client, tables, indicator, sex):
    response = client.get(f"/engine/v1/reference?indicator={indicator}&sex={sex}&x_from=10&x_to=12")
    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"x", "sd_neg3", "sd_neg2", "median", "sd_pos2", "sd_pos3"}
    assert data["x"] == [10, 11, 12]
    for key, z in [("sd_neg3", -3), ("sd_neg2", -2), ("median", 0), ("sd_pos2", 2), ("sd_pos3", 3)]:
        assert data[key] == [lms_value_at_z(z, tables.lookup(indicator, sex, day)) for day in data["x"]]


def test_reference_terminal_day_is_available(client, tables):
    response = client.get("/engine/v1/reference?indicator=lhfa&sex=male&x_from=1826&x_to=1826")
    assert response.status_code == 200
    assert response.json()["data"]["x"] == [1826]


def test_complete_evaluation_real_who_diet_history_and_schedule(client, tables):
    body = payload()
    days = (date.fromisoformat(body["as_of"]) - date.fromisoformat(body["child"]["birth_date"])).days
    body["measurements"] = [{
        "id": "9b1d0c2e-0000-4000-8000-000000000001", "measured_at": body["as_of"],
        "weight_kg": tables.lookup("wfa", "female", days).m,
        "length_height_cm": round(tables.lookup("lhfa", "female", days).m, 1),
        "position": "recumbent", "source": "posyandu",
    }]
    body["food_recalls"] = [{"recall_date": d, "breastfed": True, "food_groups": [], "meal_count": 0} for d in ["2026-01-14", "2026-01-15"]]
    original = deepcopy(body)
    response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200, response.text
    assert body == original
    data = response.json()["data"]
    assert set(data) == {"per_measurement", "level", "reasons", "next_kpsp", "diet"}
    assert data["level"] == "yellow"
    assert data["next_kpsp"] == {"questionnaire_age_months": 9, "due": True}
    assert data["diet"] == {"recall_date": "2026-01-15", "group_count": 1, "mdd": False, "mmf": False, "eff": False}
    assert data["per_measurement"][0]["z"]["wfa"] == 0.0
    assert {r["code"] for r in data["reasons"]} == {"NO_ANIMAL_SOURCE_FOOD", "LOW_DIET_DIVERSITY", "LOW_MEAL_FREQUENCY"}
    assert all(set(r) == {"code", "level", "evidence"} for r in data["reasons"])


def test_rounding_occurs_after_classification(client, tables):
    body = payload()
    days = (date.fromisoformat(body["as_of"]) - date.fromisoformat(body["child"]["birth_date"])).days
    body["measurements"] = [{"id": "9b1d0c2e-0000-4000-8000-000000000001", "measured_at": body["as_of"], "weight_kg": lms_value_at_z(-1.9999, tables.lookup("wfa", "female", days)), "source": "posyandu"}]
    response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200
    data = response.json()["data"]
    point = data["per_measurement"][0]
    assert point["z"]["wfa"] == -2.0
    assert point["classification"]["wfa"] == "normal"
    assert "UNDERWEIGHT" not in {r["code"] for r in data["reasons"]}


def test_empty_measurements_still_evaluate_kpsp_and_diet(client, tables):
    body = payload()
    body["kpsp_results"] = [{"questionnaire_age_months": 9, "answered_at": "2026-01-14", "result": "penyimpangan"}]
    response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["per_measurement"] == []
    assert data["level"] == "red"
    assert data["diet"] is None
    assert data["next_kpsp"] == {"questionnaire_age_months": 9, "due": False}


def test_measurement_outside_who_domain_does_not_return_partial_success(client, tables):
    body = payload()
    body["as_of"] = (date.fromisoformat(body["child"]["birth_date"]) + timedelta(days=1827)).isoformat()
    body["measurements"] = [{"id": "9b1d0c2e-0000-4000-8000-000000000001", "measured_at": body["as_of"], "weight_kg": 18.0, "source": "posyandu"}]
    # Kontrak v0.6: umur > 1826 hari melanggar input, bukan gangguan engine.
    assert_error(client.post("/engine/v1/growth/evaluate", json=body), 422, "VALIDATION_ERROR")


def test_precision_validation_runs_before_who_load(client):
    body = payload()
    body["measurements"] = [{"id": "9b1d0c2e-0000-4000-8000-000000000001", "measured_at": body["as_of"], "weight_kg": 8.0, "length_height_cm": 70.21, "position": "recumbent", "source": "posyandu"}]
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.post("/engine/v1/growth/evaluate", json=body)
    assert_error(response, 422, "VALIDATION_ERROR")
    assert "measurements.0.length_height_cm" in response.json()["error"]["fields"]


def test_as_of_outside_kpsp_scope_has_validation_error(client):
    body = payload()
    body["as_of"] = "2031-01-15"
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.post("/engine/v1/growth/evaluate", json=body)
    assert_error(response, 422, "VALIDATION_ERROR")
    assert "as_of" in response.json()["error"]["fields"]


@pytest.mark.parametrize("days,position,length", [
    (100, "recumbent", 44.9),
    (730, "standing", 109.4),
    (731, "standing", 64.9),
    (731, "recumbent", 65.6),
    (1000, "standing", 120.1),
])
def test_measurement_domain_error_identifies_history_point(client, days, position, length):
    from uuid import uuid4

    body = payload()
    birth = date.fromisoformat(body["child"]["birth_date"])
    day = (birth + timedelta(days=days)).isoformat()
    body["as_of"] = day
    measurement_id = str(uuid4())
    body["measurements"] = [{
        "id": measurement_id, "measured_at": day, "weight_kg": 8.0,
        "length_height_cm": length, "position": position, "source": "posyandu",
    }]
    # Domain input validation must not depend on installed reference files.
    with patch("app.api.evaluation.verified_tables", side_effect=AssertionError("not reached")):
        response = client.post("/engine/v1/growth/evaluate", json=body)
    assert_error(response, 422, "VALIDATION_ERROR")
    error = response.json()["error"]
    assert day in error["message"] and measurement_id in error["message"]
    assert "measurements.0.length_height_cm" in error["fields"]


@pytest.mark.parametrize("days,position,length,corrected", [
    (100, "recumbent", 45.0, 45.0),
    (730, "standing", 44.3, 45.0),
    (730, "standing", 109.3, 110.0),
    (731, "standing", 65.0, 65.0),
    (731, "recumbent", 65.7, 65.0),
    (731, "recumbent", 120.7, 120.0),
])
def test_measurement_domain_boundaries_use_corrected_length(client, days, position, length, corrected):
    from uuid import uuid4
    from app.core.who_tables import LMS, WHOTables

    body = payload()
    birth = date.fromisoformat(body["child"]["birth_date"])
    day = (birth + timedelta(days=days)).isoformat()
    body["as_of"] = day
    body["measurements"] = [{
        "id": str(uuid4()), "measured_at": day, "weight_kg": 8.0,
        "length_height_cm": length, "position": position, "source": "posyandu",
    }]
    indicator = "wfl" if days < 731 else "wfh"
    # Arithmetic sentinels, not clinical reference values.
    tables = WHOTables({
        ("wfa", 2, days): LMS(1, 8, .1),
        ("lhfa", 2, days): LMS(1, corrected, .1),
        (indicator, 2, round(corrected * 10)): LMS(1, 8, .1),
    })
    with patch("app.api.evaluation.verified_tables", return_value=tables):
        response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200
    assert response.json()["data"]["per_measurement"][0]["corrected_length_cm"] == corrected


def test_legacy_domain_error_clears_after_correcting_history(client, tables):
    from uuid import uuid4

    body = payload()
    body["child"]["birth_date"] = "2025-01-01"
    bad_id = str(uuid4())
    body["measurements"] = [
        {"id": bad_id, "measured_at": "2025-01-02", "weight_kg": 3.0,
         "length_height_cm": 40.0, "position": "recumbent", "source": "posyandu"},
        {"id": str(uuid4()), "measured_at": "2025-01-03", "weight_kg": 3.1,
         "length_height_cm": 50.0, "position": "recumbent", "source": "posyandu"},
    ]
    with patch("app.api.evaluation.verified_tables", return_value=tables):
        response = client.post("/engine/v1/growth/evaluate", json=body)
        assert_error(response, 422, "VALIDATION_ERROR")
        assert bad_id in response.json()["error"]["message"]
        body["measurements"][0]["length_height_cm"] = 50.0
        response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200
    assert len(response.json()["data"]["per_measurement"]) == 2
