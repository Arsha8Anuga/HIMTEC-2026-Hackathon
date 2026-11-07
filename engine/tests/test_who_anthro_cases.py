"""F-03: five end-to-end cases against WHO Anthro, |dz| <= 0.01.

Expected z-scores in tests/data/who_anthro_cases.csv were produced by
scripts/who_anthro_cases.R with the WHO anthro R package at the pinned commit
(not typed from memory). Each case goes through POST /engine/v1/growth/evaluate.
"""

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.who_tables import WHO_DATA_DIR, WHO_SOURCE_BLOBS
from app.main import create_app

CASES = list(csv.DictReader((Path(__file__).parent / "data" / "who_anthro_cases.csv").open(encoding="utf-8")))
BIRTH = date(2021, 1, 1)


@pytest.fixture(scope="module")
def client():
    if not all((WHO_DATA_DIR / name).is_file() for name in WHO_SOURCE_BLOBS):
        pytest.skip("Official WHO files are not installed")
    with TestClient(create_app()) as value:
        yield value


def test_there_are_five_cases():
    assert len(CASES) == 5


@pytest.mark.parametrize("case", CASES, ids=[c["case"] for c in CASES])
def test_matches_who_anthro(client, case):
    measured = BIRTH + timedelta(days=int(case["age_days"]))
    body = {
        "as_of": measured.isoformat(),
        "child": {"sex": case["sex"], "birth_date": BIRTH.isoformat()},
        "measurements": [{
            "id": "6f1c2d3e-4b5a-4c6d-8e7f-9a0b1c2d3e4f", "measured_at": measured.isoformat(),
            "weight_kg": float(case["weight_kg"]), "length_height_cm": float(case["length_height_cm"]),
            "position": case["position"], "head_circumference_cm": float(case["head_circumference_cm"]),
            "source": "posyandu",
        }],
        "kpsp_results": [], "food_recalls": [],
    }
    response = client.post("/engine/v1/growth/evaluate", json=body)
    assert response.status_code == 200, response.text
    z = response.json()["data"]["per_measurement"][0]["z"]
    for indicator in ("wfa", "lhfa", "wfl_wfh", "hcfa"):
        expected = float(case[f"z_{indicator}"])
        assert z[indicator] is not None, indicator
        assert abs(z[indicator] - expected) <= 0.01, (indicator, z[indicator], expected)
