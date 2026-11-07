"""Patch 05 regression tests. Run via pytest or stdlib unittest.

Synthetic LMS rows below are explicitly arithmetic sentinels, never WHO data.
Authentic integration cases are skipped only when the complete data is absent;
present-but-invalid WHO data must fail rather than silently skip.
"""

from copy import deepcopy
from datetime import date, timedelta
from math import inf, nan
import unittest
from uuid import uuid4

from app.core.anthropometry import classify, is_implausible
from app.core.growth_evaluation import evaluate_measurement, evaluate_measurements
from app.core.who_tables import LMS, WHOTables, WHODataError, WHO_DATA_DIR, TABLE_SPECS, load_who_tables
from app.schemas.growth import ChildInput, MeasurementInput, GrowthEvaluateRequest


class ClassificationTests(unittest.TestCase):
    def test_permenkes_boundaries(self):
        cases = {
            "wfa": [(-3.01, "severely_underweight"), (-3, "underweight"), (-2.01, "underweight"), (-2, "normal"), (1, "normal"), (1.01, "overweight_risk")],
            "lhfa": [(-3.01, "severely_stunted"), (-3, "stunted"), (-2.01, "stunted"), (-2, "normal"), (3, "normal"), (3.01, "tall")],
            "wfl_wfh": [(-3.01, "severely_wasted"), (-3, "wasted"), (-2.01, "wasted"), (-2, "normal"), (1, "normal"), (1.01, "overweight_risk"), (2, "overweight_risk"), (2.01, "overweight"), (3, "overweight"), (3.01, "obese")],
        }
        for indicator, pairs in cases.items():
            for score, expected in pairs:
                with self.subTest(indicator=indicator, score=score):
                    self.assertEqual(classify(indicator, score), expected)

    def test_who_flag_boundaries(self):
        for indicator, lower, upper in (("wfa", -6, 5), ("lhfa", -6, 6), ("wfl_wfh", -5, 5)):
            for score, expected in ((lower, False), (upper, False), (lower - .001, True), (upper + .001, True)):
                with self.subTest(indicator=indicator, score=score):
                    self.assertEqual(is_implausible(indicator, score), expected)
                    self.assertEqual(classify(indicator, score) is None, expected)

    def test_no_rounding_before_classification(self):
        self.assertEqual(classify("lhfa", -2.00001), "stunted")
        self.assertTrue(is_implausible("wfa", 5.00001))

    def test_reject_unknown_and_nonfinite_scores(self):
        with self.assertRaises(ValueError):
            classify("hcfa", 0)
        for score in (nan, inf, -inf, True, "0"):
            for function in (classify, is_implausible):
                with self.subTest(score=score, function=function):
                    with self.assertRaises(ValueError):
                        function("wfa", score)


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.child = ChildInput(sex="male", birth_date=date(2020, 1, 1))
        self.point = MeasurementInput(id=uuid4(), measured_at=date(2020, 4, 10), weight_kg=10, length_height_cm=70, position="recumbent", head_circumference_cm=40, source="posyandu")
        # Synthetic format/math fixture, not a reference for clinical use.
        self.tables = WHOTables(rows={
            ("wfa", 1, 100): LMS(1, 10, .1),
            ("lhfa", 1, 100): LMS(1, 70, .1),
            ("wfl", 1, 700): LMS(1, 10, .1),
            ("hcfa", 1, 100): LMS(1, 40, .1),
        })

    def test_all_four_medians_and_contract_shape(self):
        result = evaluate_measurement(self.child, self.point, self.tables)
        self.assertEqual(set(result), {"id", "age_days", "corrected_length_cm", "z", "classification", "flags"})
        self.assertEqual(result["age_days"], 100)
        self.assertEqual(result["z"], dict(wfa=0, lhfa=0, wfl_wfh=0, hcfa=0))
        self.assertEqual(set(result["classification"].values()), {"normal"})
        self.assertEqual(result["flags"], [])

    def test_optional_measurements_stay_null(self):
        point = self.point.model_copy(update={"length_height_cm": None, "position": None, "head_circumference_cm": None})
        result = evaluate_measurement(self.child, point, self.tables)
        self.assertEqual(result["z"], dict(wfa=0, lhfa=None, wfl_wfh=None, hcfa=None))
        self.assertEqual(result["classification"], dict(wfa="normal", lhfa=None, wfl_wfh=None))
        self.assertIsNone(result["corrected_length_cm"])

    def test_one_flag_suppresses_every_classification(self):
        rows = dict(self.tables.rows)
        rows["lhfa", 1, 100] = LMS(1, 100, .01)
        result = evaluate_measurement(self.child, self.point, WHOTables(rows))
        self.assertEqual(result["flags"], ["IMPLAUSIBLE_VALUE"])
        self.assertEqual(result["z"]["wfa"], 0)
        self.assertTrue(all(v is None for v in result["classification"].values()))

    def test_weight_tail_flags_once(self):
        result = evaluate_measurement(self.child, self.point.model_copy(update={"weight_kg": 40}), self.tables)
        self.assertEqual(result["flags"], ["IMPLAUSIBLE_VALUE"])

    def test_position_and_indicator_switch_at_731(self):
        for days, position, original, corrected, indicator in ((730, "standing", 69.3, 70, "wfl"), (731, "recumbent", 70.7, 70, "wfh")):
            with self.subTest(days=days):
                rows = {("wfa", 1, days): LMS(1, 10, .1), ("lhfa", 1, days): LMS(1, 70, .1), (indicator, 1, 700): LMS(1, 10, .1)}
                point = self.point.model_copy(update={"measured_at": self.child.birth_date + timedelta(days=days), "position": position, "length_height_cm": original, "head_circumference_cm": None})
                result = evaluate_measurement(self.child, point, WHOTables(rows))
                self.assertEqual(result["corrected_length_cm"], corrected)
                self.assertEqual(result["z"]["wfl_wfh"], 0)

    def test_domain_and_precision_errors_are_not_hidden(self):
        for length in (40, 70.01, 130):
            with self.subTest(length=length), self.assertRaises(WHODataError):
                evaluate_measurement(self.child, self.point.model_copy(update={"length_height_cm": length}), self.tables)
        for days in (-1, 1827, 1856):
            with self.subTest(days=days), self.assertRaises(ValueError):
                evaluate_measurement(self.child, self.point.model_copy(update={"measured_at": self.child.birth_date + timedelta(days=days)}), self.tables)

    def test_batch_order_empty_history_and_no_mutation(self):
        earlier = self.point.model_copy(update={"id": uuid4(), "measured_at": self.point.measured_at - timedelta(days=1)})
        rows = dict(self.tables.rows)
        for indicator in ("wfa", "lhfa", "hcfa"):
            rows[indicator, 1, 99] = rows[indicator, 1, 100]
        request = GrowthEvaluateRequest(as_of=self.point.measured_at, child=self.child, measurements=[self.point, earlier], kpsp_results=[], food_recalls=[])
        before = deepcopy(request.model_dump())
        result = evaluate_measurements(request, WHOTables(rows))
        self.assertEqual([item["id"] for item in result], [str(self.point.id), str(earlier.id)])
        self.assertEqual(request.model_dump(), before)
        request.measurements = []
        self.assertEqual(evaluate_measurements(request, self.tables), [])

    def test_full_precision_retained(self):
        result = evaluate_measurement(self.child, self.point.model_copy(update={"weight_kg": 10.01234}), self.tables)
        self.assertNotEqual(result["z"]["wfa"], round(result["z"]["wfa"], 2))


@unittest.skipUnless(all((WHO_DATA_DIR / spec.filename).is_file() for spec in TABLE_SPECS.values()), "Install the five official WHO tables for integration tests")
class AuthenticWHOTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = load_who_tables()  # Present but corrupt data must fail.

    def evaluate(self, sex, days, weight, length=None):
        child = ChildInput(sex=sex, birth_date=date(2020, 1, 1))
        point = MeasurementInput(id=uuid4(), measured_at=child.birth_date + timedelta(days=days), weight_kg=weight, length_height_cm=length, position="recumbent" if length else None, source="posyandu")
        return evaluate_measurement(child, point, self.tables)

    def test_official_length_case(self):
        # WHO test-zscore-length-for-age.R, male day 44, 50cm => -3.29.
        result = self.evaluate("male", 44, 4.5, 50)
        self.assertAlmostEqual(result["z"]["lhfa"], -3.29, delta=.005)
        self.assertEqual(result["classification"]["lhfa"], "severely_stunted")

    def test_official_weight_case(self):
        # WHO test-zscore-weight-for-age.R, female day 1522, 17kg => 0.24.
        self.assertAlmostEqual(self.evaluate("female", 1522, 17)["z"]["wfa"], .24, delta=.005)

    def test_official_extreme_weight_flag(self):
        # Same official WHO test: female day 1, 10.37kg => flag above +5.
        result = self.evaluate("female", 1, 10.37)
        self.assertEqual(result["flags"], ["IMPLAUSIBLE_VALUE"])
        self.assertIsNone(result["classification"]["wfa"])


if __name__ == "__main__":
    unittest.main()
