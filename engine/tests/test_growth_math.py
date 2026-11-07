"""Patch 04: WHO numerical algorithms + reference cases, with no fabricated tables.

Official WHO Anthro R code / cases from pinned commit:
https://github.com/WorldHealthOrganization/anthro/tree/b776d8a12b1c97369c748b561159fd2ec4f4db58
R/z-score-helper.R, R/z-score-weight-for-lenhei.R and tests/testthat/*.R.
Reference rows are explicitly attributed and used only as test fixtures.
"""

from decimal import Decimal
from math import exp, log

import pytest

from app.core.growth_math import (
    correct_length_height_cm,
    interpolate_length_lms,
    lms_value_at_z,
    lms_zscore,
    restricted_lms_zscore,
)
from app.core.who_tables import LMS, WHODataError, WHOTables


def test_lms_median_zero_and_standard_deviations() -> None:
    params = LMS(0.5, 10.0, 0.1)  # Synthetic math parameters only.
    for z in (-3, -2, -1, 0, 1, 2, 3):
        assert lms_zscore(lms_value_at_z(z, params), params) == pytest.approx(z, abs=1e-12)


def test_l_zero_logarithmic_limit() -> None:
    params = LMS(0, 10, 0.2)
    assert lms_zscore(10 * exp(0.4), params) == pytest.approx(2.0, abs=1e-12)
    assert lms_value_at_z(-2, params) == pytest.approx(10 * exp(-0.4))


def test_small_nonzero_l_is_numerically_stable() -> None:
    params = LMS(1e-12, 10.0, 0.2)
    assert lms_zscore(11.0, params) == pytest.approx(log(1.1) / 0.2, abs=1e-10)


def test_who_official_length_for_age_reference_case() -> None:
    # WHO: lenanthro.txt male day 44 => L=1, M=56.4833, S=0.03492
    # WHO anthro/tests/testthat/test-zscore-length-for-age.R: 50 cm at day 44.
    score = lms_zscore(50, LMS(1.0, 56.4833, 0.03492))
    assert round(score, 2) == -3.29


def test_who_official_weight_for_age_reference_case() -> None:
    # WHO weianthro.txt female day 1522: L=-0.3387 M=16.433 S=0.14051
    # WHO anthro/tests/testthat/test-zscore-weight-for-age.R:
    # female at day 1522, weight 17 kg -> 0.24.
    score = restricted_lms_zscore(17.0, LMS(-0.3387, 16.433, 0.14051))
    assert round(score, 2) == 0.24


def test_who_official_high_weight_case_is_flagged_above_five() -> None:
    # WHO weianthro.txt female day 1: L=0.3259, M=3.1957, S=0.14578;
    # official R test uses weight 10.37 kg and expects flag (>+5).
    z = restricted_lms_zscore(10.37, LMS(0.3259, 3.1957, 0.14578))
    assert z > 5


@pytest.mark.parametrize("score", (-3.0, -2.5, 0.0, 2.5, 3.0))
def test_restricted_matches_lms_inside_three_sd(score: float) -> None:
    params = LMS(-0.3521, 7.0, 0.08)  # Synthetic math-only parameters.
    x = lms_value_at_z(score, params)
    assert restricted_lms_zscore(x, params) == pytest.approx(score, abs=1e-12)


def test_restricted_continuation_above_three() -> None:
    params = LMS(-0.3521, 7.0, 0.08)
    x2 = lms_value_at_z(2, params)
    x3 = lms_value_at_z(3, params)
    assert restricted_lms_zscore(x3 + (x3 - x2), params) == pytest.approx(4.0)
    assert restricted_lms_zscore(x3 + (x3 - x2) / 2, params) == pytest.approx(3.5)


def test_restricted_continuation_below_minus_three() -> None:
    params = LMS(-0.3521, 7.0, 0.08)
    xm2 = lms_value_at_z(-2, params)
    xm3 = lms_value_at_z(-3, params)
    assert restricted_lms_zscore(xm3 - (xm2 - xm3), params) == pytest.approx(-4.0)


def test_adjusted_is_not_raw_in_extreme_tail() -> None:
    params = LMS(-0.3521, 7.0, 0.08)
    x3 = lms_value_at_z(3, params)
    far_right = x3 * 1.5
    assert restricted_lms_zscore(far_right, params) != pytest.approx(lms_zscore(far_right, params))


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf"), True, "12"])
def test_measurement_rejected_when_invalid(bad) -> None:
    with pytest.raises(ValueError):
        lms_zscore(bad, LMS(1, 10, 0.1))
    with pytest.raises(ValueError):
        restricted_lms_zscore(bad, LMS(1, 10, 0.1))


@pytest.mark.parametrize("params", [LMS(0.3, 0, 0.1), LMS(1, 10, 0), LMS(float("nan"), 10, 0.1), LMS(1, float("inf"), 0.1)])
def test_reject_invalid_lms(params: LMS) -> None:
    with pytest.raises(ValueError):
        lms_zscore(10, params)
    with pytest.raises(ValueError):
        lms_value_at_z(2, params)


def test_inversion_rejects_undefined_domain() -> None:
    with pytest.raises(ValueError, match="domain"):
        lms_value_at_z(-100, LMS(1, 10, 0.1))


@pytest.mark.parametrize("age, position, expected", [
    (730, "recumbent", 80.0),
    (730, "standing", 80.7),
    (731, "standing", 80.0),
    (731, "recumbent", 79.3),
    (0, "standing", 80.7),
    (1000, "recumbent", 79.3),
])
def test_position_correction_at_boundary(age: int, position: str, expected: float) -> None:
    assert correct_length_height_cm(age, 80.0, position) == pytest.approx(expected)


@pytest.mark.parametrize("age, position, measured, corrected, indicator", [
    (730, "standing", 79.9, 80.6, "wfl"),
    (731, "recumbent", 80.1, 79.4, "wfh"),
])
def test_position_correction_can_feed_exact_who_lookup(age, position, measured, corrected, indicator) -> None:
    # Synthetic sentinel tests grid compatibility, not clinical accuracy.
    sentinel = LMS(1, 10, 0.1)
    index = int(Decimal(str(corrected)) * 10)
    tables = WHOTables(rows={(indicator, 1, index): sentinel})
    value = correct_length_height_cm(age, measured, position)
    assert value == corrected
    assert tables.lookup(indicator, "male", value) == sentinel


@pytest.mark.parametrize("age, position, measured, expected", [
    (730, "standing", 79.91, 80.61),
    (731, "recumbent", 80.11, 79.41),
])
def test_position_correction_does_not_quantise_precise_inputs(age, position, measured, expected) -> None:
    assert correct_length_height_cm(age, measured, position) == expected


@pytest.mark.parametrize("bad_age, bad_pos, bad_measure", [
    (-1, "standing", 80),
    (True, "standing", 80),
    (12.5, "standing", 80),
    (500, "unknown", 80),
    (500, "standing", 0),
    (500, "recumbent", float("nan")),
])
def test_reject_invalid_position_inputs(bad_age, bad_pos, bad_measure) -> None:
    with pytest.raises(ValueError):
        correct_length_height_cm(bad_age, bad_measure, bad_pos)


def test_who_length_interpolation_official_rows() -> None:
    # WHO wflanthro.txt male at 60.5 and 60.6 cm, authentic LMS rows.
    rows = {
        ("wfl", 1, 605): LMS(-0.3521, 6.1284, 0.08324),
        ("wfl", 1, 606): LMS(-0.3521, 6.1556, 0.08321),
        ("wfh", 1, 1200): LMS(-0.3521, 22.353, 0.09424),
    }
    tables = WHOTables(rows=rows)
    interpolation = interpolate_length_lms(tables, "wfl", "male", Decimal("60.55"))
    assert interpolation.l == pytest.approx(-0.3521)
    assert interpolation.m == pytest.approx(6.142)
    assert interpolation.s == pytest.approx(0.083225)
    assert restricted_lms_zscore(interpolation.m, interpolation) == pytest.approx(0, abs=1e-12)
    assert interpolate_length_lms(tables, "wfl", "male", 60.5) == rows["wfl", 1, 605]
    # At the top of a reference grid, interpolation must not request max+.1
    assert interpolate_length_lms(tables, "wfh", "male", 120) == rows["wfh", 1, 1200]


@pytest.mark.parametrize("indicator, sex, length", [
    ("wfl", "male", 44.9),
    ("wfh", "female", 120.01),
    ("wfa", "male", 60),
    ("wfl", "male", float("nan")),
    ("wfl", "male", True),
])
def test_interpolation_rejects_invalid_axes(indicator, sex, length) -> None:
    with pytest.raises((WHODataError, ValueError)):
        interpolate_length_lms(WHOTables(rows={}), indicator, sex, length)
