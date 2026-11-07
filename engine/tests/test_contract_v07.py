"""Contract v0.7: labelled KPSP forms 15/18/24 and wfl/wfh reference curves."""

import json
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.growth_math import lms_value_at_z
from app.core.kpsp import load_kpsp_bank, runtime_questionnaire
from app.core.who_tables import WHO_DATA_DIR, WHO_SOURCE_BLOBS, load_who_tables
from app.main import create_app
from app.schemas.kpsp import SCHEDULE

BANK = WHO_DATA_DIR.parents[0] / "kpsp" / "questionnaires.json"


@pytest.fixture
def client():
    with TestClient(create_app(), raise_server_exceptions=False) as value:
        yield value


@pytest.fixture
def tables():
    if not all((WHO_DATA_DIR / name).is_file() for name in WHO_SOURCE_BLOBS):
        pytest.skip("Official WHO files are not installed")
    return load_who_tables()


def test_runtime_ages_are_exactly_the_picture_free_forms_chosen():
    source = json.loads(BANK.read_text(encoding="utf-8"))["source"]
    assert source["runtime_ages"] == [15, 18, 24]
    assert not any(source["image_dependent_items"].get(str(age)) for age in source["runtime_ages"])


@pytest.mark.parametrize("age", [15, 18, 24])
def test_runtime_form_served_verbatim_with_label(client, age):
    body = client.get(f"/engine/v1/kpsp/questionnaire?age_months={age}").json()
    assert body["error"] is None
    data = body["data"]
    assert data["review_status"] == "transcription_unreviewed"
    assert data["items"] == [item.model_dump() for item in load_kpsp_bank(BANK, for_review=True)[age].items]


@pytest.mark.parametrize("age", sorted(set(SCHEDULE) - {15, 18, 24}))
def test_other_forms_have_no_items(client, age):
    data = client.get(f"/engine/v1/kpsp/questionnaire?age_months={age}").json()["data"]
    assert data == {"questionnaire_age_months": age, "review_status": "unavailable", "items": []}


@pytest.mark.parametrize("query", ["age_months=7", "age_months=0", "age_months=x", ""])
def test_questionnaire_rejects_unscheduled_age(client, query):
    response = client.get("/engine/v1/kpsp/questionnaire?" + query)
    assert response.status_code == 422 and response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_runtime_age_with_picture_items_is_refused(tmp_path, client, monkeypatch):
    data = json.loads(BANK.read_text(encoding="utf-8"))
    data["source"]["runtime_ages"] = [9, 15]  # form 9 item 1 depends on a picture
    path = tmp_path / "bank.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        runtime_questionnaire(15, path)
    monkeypatch.setattr("app.api.evaluation.runtime_questionnaire", lambda age: runtime_questionnaire(age, path))
    response = client.get("/engine/v1/kpsp/questionnaire?age_months=15")
    assert response.status_code == 503 and response.json()["error"]["code"] == "ENGINE_UNAVAILABLE"


@pytest.mark.parametrize("indicator,lo,hi", [("wfl", 45, 47), ("wfh", 65, 66), ("wfl", 109, 110), ("wfh", 119, 120)])
def test_length_reference_uses_native_tenth_cm_grid(client, tables, indicator, lo, hi):
    data = client.get(f"/engine/v1/reference?indicator={indicator}&sex=male&x_from={lo}&x_to={hi}").json()["data"]
    assert data["x"] == [round(lo + i / 10, 1) for i in range((hi - lo) * 10 + 1)]
    for i, x in enumerate(data["x"]):
        lms = tables.lookup(indicator, "male", Decimal(str(x)))
        assert data["median"][i] == lms_value_at_z(0, lms)
        assert data["sd_neg2"][i] == lms_value_at_z(-2, lms)
