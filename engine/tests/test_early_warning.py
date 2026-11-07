"""Project-rule fixtures, not clinical reference measurements.

Patch 05 supplies independently tested z-scores. Mocking that boundary isolates
calendar, trend and reason aggregation; an authentic end-to-end test is below.
"""

from copy import deepcopy
from datetime import date, timedelta
import unittest
from unittest.mock import patch
from uuid import uuid4

from app.core.anthropometry import classify, is_implausible
from app.core.early_warning import evaluate_early_warning
from app.core.who_tables import WHOTables, WHO_DATA_DIR, TABLE_SPECS, load_who_tables
from app.schemas.growth import GrowthEvaluateRequest


class EarlyWarningTests(unittest.TestCase):
    def evaluate(self, entries, *, as_of=None, kpsp=None):
        measurements, points = [], []
        for i, entry in enumerate(entries):
            day = entry["day"]
            z = {"wfa": entry.get("wfa", 0), "lhfa": entry.get("lhfa", 0), "wfl_wfh": entry.get("wfl_wfh", 0), "hcfa": None}
            flagged = entry.get("flagged", False) or any(is_implausible(indicator, score) for indicator, score in z.items() if indicator != "hcfa" and score is not None)
            identity = str(uuid4())
            measurements.append(dict(id=identity, measured_at=day.isoformat(), weight_kg=entry.get("weight", 8 + i * .1), source=entry.get("source", "posyandu"), length_height_cm=70 if z["lhfa"] is not None else None, position="recumbent" if z["lhfa"] is not None else None))
            points.append(dict(id=identity, age_days=(day-date(2023,1,1)).days, corrected_length_cm=70 if z["lhfa"] is not None else None, z=z, classification={indicator: None if flagged or z[indicator] is None else classify(indicator,z[indicator]) for indicator in ("wfa","lhfa","wfl_wfh")}, flags=["IMPLAUSIBLE_VALUE"] if flagged else []))
        request = GrowthEvaluateRequest(as_of=as_of or max((e["day"] for e in entries), default=date(2024,1,1)), child=dict(sex="female",birth_date="2023-01-01"), measurements=measurements,kpsp_results=kpsp or [],food_recalls=[])
        before = deepcopy(request.model_dump())
        with patch("app.core.early_warning.evaluate_measurements",return_value=points):
            result = evaluate_early_warning(request,WHOTables({}))
        self.assertEqual(request.model_dump(),before)
        self.assertEqual(result["per_measurement"], points)
        return result

    def codes(self, result):
        return [reason["code"] for reason in result["reasons"]]

    def test_every_current_classification_reason(self):
        cases=[("lhfa",-3.1,"SEVERELY_STUNTED","red"),("lhfa",-2.5,"STUNTED","red"),("wfl_wfh",-3.1,"SEVERELY_WASTED","red"),("wfl_wfh",-2.5,"WASTED","red"),("wfa",-3.1,"SEVERELY_UNDERWEIGHT","red"),("wfa",-2.5,"UNDERWEIGHT","yellow"),("wfl_wfh",2.5,"OVERWEIGHT","yellow"),("wfl_wfh",3.1,"OVERWEIGHT","yellow")]
        for indicator,z,code,level in cases:
            with self.subTest(code=code,z=z):
                r=self.evaluate([dict(day=date(2024,5,1),**{indicator:z})])
                self.assertIn(code,self.codes(r)); self.assertEqual(r["level"],level)

    def test_normal_is_green(self):
        r=self.evaluate([dict(day=date(2024,5,1))])
        self.assertEqual(r["level"],"green");self.assertEqual(r["reasons"],[])

    def test_home_info_does_not_raise_level(self):
        r=self.evaluate([dict(day=date(2024,5,1),source="home")])
        self.assertEqual(self.codes(r),["HOME_MEASUREMENT"]);self.assertEqual(r["level"],"green")

    def test_implausible_latest_does_not_fall_back_to_older_red(self):
        r=self.evaluate([dict(day=date(2024,4,1),lhfa=-3.5),dict(day=date(2024,5,1),lhfa=-7,source="home")])
        self.assertEqual(set(self.codes(r)),{"IMPLAUSIBLE_VALUE","HOME_MEASUREMENT"})
        self.assertEqual(r["level"],"green")

    def test_monthly_one_t(self):
        r=self.evaluate([dict(day=date(2024,4,15),weight=9),dict(day=date(2024,5,15),weight=9)])
        self.assertIn("WEIGHT_NOT_GAINING",self.codes(r));self.assertEqual(r["level"],"yellow")

    def test_monthly_two_t_replaces_one_t(self):
        r=self.evaluate([dict(day=date(2024,m,15),weight=9) for m in (3,4,5)])
        self.assertIn("WEIGHT_NOT_GAINING_2X",self.codes(r));self.assertNotIn("WEIGHT_NOT_GAINING",self.codes(r));self.assertEqual(r["level"],"red")

    def test_same_month_repeats_are_not_monthly_periods(self):
        r=self.evaluate([dict(day=date(2024,5,d),weight=9) for d in (1,10,20)])
        self.assertFalse(any(c.startswith("WEIGHT_NOT_GAINING") for c in self.codes(r)))

    def test_latest_valid_point_represents_each_month(self):
        r=self.evaluate([dict(day=date(2024,4,1),weight=10),dict(day=date(2024,4,30),weight=9),dict(day=date(2024,5,1),weight=9),dict(day=date(2024,5,4),weight=9.2)])
        self.assertFalse(any(c.startswith("WEIGHT_NOT_GAINING") for c in self.codes(r)))

    def test_month_gap_prevents_comparison(self):
        r=self.evaluate([dict(day=date(2024,3,1),weight=9),dict(day=date(2024,5,1),weight=9)])
        self.assertNotIn("WEIGHT_NOT_GAINING",self.codes(r))

    def test_month_gap_breaks_two_t(self):
        r=self.evaluate([dict(day=date(2024,m,1),weight=9) for m in (1,3,4)])
        self.assertIn("WEIGHT_NOT_GAINING",self.codes(r));self.assertNotIn("WEIGHT_NOT_GAINING_2X",self.codes(r))

    def test_calendar_year_rollover(self):
        r=self.evaluate([dict(day=date(2023,12,31),weight=9),dict(day=date(2024,1,1),weight=9)])
        self.assertIn("WEIGHT_NOT_GAINING",self.codes(r))

    def test_flagged_month_does_not_form_two_t(self):
        r=self.evaluate([dict(day=date(2024,m,1),weight=9,flagged=(m==4)) for m in (3,4,5)])
        self.assertFalse(any(c.startswith("WEIGHT_NOT_GAINING") for c in self.codes(r)))

    def test_positive_gain_breaks_two_t(self):
        r=self.evaluate([dict(day=date(2024,m,1),weight=w) for m,w in ((3,8),(4,9),(5,9))])
        self.assertIn("WEIGHT_NOT_GAINING",self.codes(r));self.assertNotIn("WEIGHT_NOT_GAINING_2X",self.codes(r))

    def test_crossing_inclusive_time_and_score_boundaries(self):
        now=date(2024,6,1)
        for days,delta,expected in ((59,.67,False),(60,.67,True),(120,.67,True),(121,.67,False),(90,.6699,False)):
            with self.subTest(days=days,delta=delta):
                r=self.evaluate([dict(day=now-timedelta(days=days),wfa=0),dict(day=now,wfa=-delta)])
                self.assertEqual("CROSSING_DOWN" in self.codes(r),expected)

    def test_crossing_both_indicators_have_separate_evidence(self):
        r=self.evaluate([dict(day=date(2024,3,1),wfa=0,lhfa=0),dict(day=date(2024,6,1),wfa=-1,lhfa=-1)])
        evidence=[x["evidence"]["indicator"] for x in r["reasons"] if x["code"]=="CROSSING_DOWN"]
        self.assertEqual(set(evidence),{"wfa","lhfa"})

    def test_flagged_history_excluded_from_crossing(self):
        r=self.evaluate([dict(day=date(2024,3,1),wfa=2,flagged=True),dict(day=date(2024,6,1),wfa=0)])
        self.assertNotIn("CROSSING_DOWN",self.codes(r))

    def test_projected_stunting(self):
        now=date(2024,6,1)
        r=self.evaluate([dict(day=now-timedelta(days=d),lhfa=z) for d,z in ((120,-.4),(60,-1),(0,-1.6))])
        self.assertIn("PROJECTED_STUNTING",self.codes(r));self.assertEqual(r["level"],"yellow")

    def test_projection_requires_three_valid_points(self):
        now=date(2024,6,1)
        entries=[dict(day=now-timedelta(days=d),lhfa=z) for d,z in ((120,-.4),(60,-1),(0,-1.6))]
        for changed in (entries[1:], [entries[0]|dict(flagged=True),*entries[1:]]):
            self.assertNotIn("PROJECTED_STUNTING",self.codes(self.evaluate(changed)))

    def test_projection_not_for_existing_stunting(self):
        now=date(2024,6,1)
        r=self.evaluate([dict(day=now-timedelta(days=d),lhfa=z) for d,z in ((120,-1),(60,-1.6),(0,-2.2))])
        self.assertNotIn("PROJECTED_STUNTING",self.codes(r));self.assertIn("STUNTED",self.codes(r))

    def test_projection_flat_or_rising(self):
        now=date(2024,6,1)
        for zs in ((-1,-1,-1),(-1.6,-1,-.4)):
            r=self.evaluate([dict(day=now-timedelta(days=d),lhfa=z) for d,z in zip((120,60,0),zs)])
            self.assertNotIn("PROJECTED_STUNTING",self.codes(r))

    def test_projection_horizon_boundary(self):
        now=date(2024,6,1)
        for zs,expected in (((.1,-.5,-1.1),True),((.11,-.49,-1.09),False)):
            r=self.evaluate([dict(day=now-timedelta(days=d),lhfa=z) for d,z in zip((120,60,0),zs)])
            self.assertEqual("PROJECTED_STUNTING" in self.codes(r),expected)

    def test_projection_uses_calendar_six_month_window(self):
        now=date(2024,8,31)
        r=self.evaluate([dict(day=date(2024,2,28),lhfa=-.4),dict(day=date(2024,6,1),lhfa=-1),dict(day=now,lhfa=-1.6)])
        self.assertNotIn("PROJECTED_STUNTING",self.codes(r))

    def test_no_recent_length_90_day_boundary(self):
        now=date(2024,6,1)
        for days,expected in ((90,False),(91,True)):
            r=self.evaluate([dict(day=now-timedelta(days=days)),dict(day=now,lhfa=None)],as_of=now)
            self.assertEqual("NO_RECENT_LENGTH" in self.codes(r),expected)

    def test_flagged_length_is_not_recent_valid_length(self):
        r=self.evaluate([dict(day=date(2024,5,1),flagged=True)])
        self.assertIn("NO_RECENT_LENGTH",self.codes(r))

    def test_latest_kpsp_outcome_controls_reason(self):
        history=[dict(questionnaire_age_months=9,answered_at="2024-04-01",result="penyimpangan"),dict(questionnaire_age_months=12,answered_at="2024-05-01",result="meragukan")]
        r=self.evaluate([],as_of=date(2024,6,1),kpsp=history)
        self.assertIn("KPSP_DOUBTFUL",self.codes(r));self.assertNotIn("KPSP_DEVIATION",self.codes(r));self.assertEqual(r["level"],"yellow")

    def test_kpsp_deviation_overrides_info(self):
        r=self.evaluate([],kpsp=[dict(questionnaire_age_months=9,answered_at="2023-12-01",result="penyimpangan")])
        self.assertIn("KPSP_DEVIATION",self.codes(r));self.assertEqual(r["level"],"red")

    def test_empty_history_has_no_fabricated_zscore(self):
        r=self.evaluate([])
        self.assertEqual(r["per_measurement"],[]);self.assertEqual(r["level"],"green");self.assertEqual(self.codes(r),["NO_RECENT_LENGTH"])

    def test_input_order_does_not_change_reasons(self):
        entries=[dict(day=date(2024,m,1),weight=9) for m in (3,4,5)]
        first=self.evaluate(entries);second=self.evaluate(list(reversed(entries)))
        self.assertEqual(first["reasons"],second["reasons"]);self.assertEqual(first["level"],second["level"])


@unittest.skipUnless(all((WHO_DATA_DIR / spec.filename).is_file() for spec in TABLE_SPECS.values()),"Install the five official WHO tables")
class EarlyWarningIntegrationTests(unittest.TestCase):
    def test_authentic_who_point_produces_severe_stunting_reason(self):
        # WHO's male day-44, 50-cm LHFA case, as verified in Patch 05.
        request=GrowthEvaluateRequest(as_of="2020-02-14",child=dict(sex="male",birth_date="2020-01-01"),measurements=[dict(id=str(uuid4()),measured_at="2020-02-14",weight_kg=4.5,length_height_cm=50,position="recumbent",source="posyandu")],kpsp_results=[],food_recalls=[])
        result=evaluate_early_warning(request,load_who_tables())
        self.assertEqual(result["level"],"red")
        self.assertIn("SEVERELY_STUNTED",[r["code"] for r in result["reasons"]])


if __name__=="__main__":
    unittest.main()
