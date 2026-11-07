"""WHO indicator boundaries and contract-specific pattern/window tests."""

from copy import deepcopy
from datetime import date, timedelta
import unittest
from unittest.mock import patch
from uuid import uuid4

from pydantic import ValidationError
from app.core.iycf import evaluate_diet, evaluate_food_recall, evaluate_growth_and_diet
from app.core.who_tables import WHOTables, WHODataError, WHO_DATA_DIR, TABLE_SPECS, load_who_tables
from app.schemas.growth import ChildInput, FoodRecallInput, GrowthEvaluateRequest

BIRTH = date(2024,1,1)
TODAY = date(2024,11,7)
GROUPS = ["grains_roots_tubers","pulses_nuts_seeds","eggs","vita_fruits_veg"]


def recall(days_ago=0, **changes):
    return dict(recall_date=(TODAY-timedelta(days=days_ago)).isoformat(),breastfed=True,food_groups=list(GROUPS),meal_count=3,milk_feed_count=None) | changes


def request(recalls=(), **changes):
    return GrowthEvaluateRequest.model_validate(dict(as_of=TODAY.isoformat(),child=dict(sex="female",birth_date=BIRTH.isoformat()),measurements=[],kpsp_results=[],food_recalls=list(recalls)) | changes)


def daily(age_days=300, **changes):
    item=FoodRecallInput.model_validate(recall(recall_date=(BIRTH+timedelta(days=age_days)).isoformat(),**changes))
    return evaluate_food_recall(ChildInput(sex="female",birth_date=BIRTH),item)


class DailyIYCFTests(unittest.TestCase):
    def test_contract_shape(self):
        result=daily()
        self.assertEqual(set(result),{"recall_date","group_count","mdd","mmf","eff"})
        self.assertTrue(result["mdd"]);self.assertTrue(result["mmf"]);self.assertTrue(result["eff"])

    def test_mdd_five_of_eight_boundary(self):
        self.assertEqual(daily(food_groups=GROUPS)["group_count"],5)
        self.assertTrue(daily(food_groups=GROUPS)["mdd"])
        self.assertFalse(daily(food_groups=GROUPS[:-1])["mdd"])

    def test_duplicate_groups_never_inflate_mdd(self):
        result=daily(food_groups=["eggs"]*7)
        self.assertEqual(result["group_count"],2);self.assertFalse(result["mdd"])

    def test_non_breastfed_has_no_breast_milk_group(self):
        self.assertEqual(daily(breastfed=False,food_groups=GROUPS)["group_count"],4)
        self.assertFalse(daily(breastfed=False,food_groups=GROUPS)["mdd"])

    def test_breastfeeding_switch_at_nine_months(self):
        self.assertTrue(daily(273,meal_count=2)["mmf"])
        self.assertFalse(daily(274,meal_count=2)["mmf"])
        self.assertTrue(daily(274,meal_count=3)["mmf"])

    def test_young_breastfed_minimum_two(self):
        self.assertFalse(daily(183,meal_count=1)["mmf"])
        self.assertTrue(daily(183,meal_count=2)["mmf"])

    def test_extra_milk_does_not_replace_breastfed_meals(self):
        self.assertFalse(daily(300,meal_count=1,milk_feed_count=10)["mmf"])

    def test_non_breastfed_four_total_with_solid_feed(self):
        self.assertTrue(daily(breastfed=False,meal_count=1,milk_feed_count=3)["mmf"])
        self.assertFalse(daily(breastfed=False,meal_count=1,milk_feed_count=2)["mmf"])
        self.assertFalse(daily(breastfed=False,meal_count=0,milk_feed_count=4)["mmf"])

    def test_mmf_is_not_minimum_milk_feeding_frequency(self):
        self.assertTrue(daily(breastfed=False,meal_count=4,milk_feed_count=0)["mmf"])

    def test_missing_optional_milk_scored_zero(self):
        self.assertFalse(daily(breastfed=False,meal_count=3,milk_feed_count=None)["mmf"])
        self.assertTrue(daily(breastfed=False,meal_count=4,milk_feed_count=None)["mmf"])

    def test_milk_count_does_not_invent_dairy_checkbox(self):
        self.assertEqual(daily(breastfed=False,meal_count=1,milk_feed_count=3,food_groups=[])["group_count"],0)

    def test_eff_eggs_or_flesh_but_not_dairy(self):
        for groups,expected in ((["eggs"],True),(["flesh_foods"],True),(["dairy"],False),([],False)):
            with self.subTest(groups=groups):self.assertEqual(daily(food_groups=groups)["eff"],expected)

    def test_age_boundaries_follow_project_schema(self):
        for days,valid in ((182,False),(183,True),(730,True),(731,False)):
            with self.subTest(days=days):
                if valid:self.assertIn("mdd",daily(days))
                else:
                    with self.assertRaises(ValueError):daily(days)


class DietPatternTests(unittest.TestCase):
    def bad(self,days=0):return recall(days,food_groups=[],meal_count=0)
    def codes(self,r):return {item["code"]:item["level"] for item in r["reasons"]}

    def test_one_bad_day_is_only_info(self):
        result=evaluate_diet(request([self.bad()]))
        self.assertEqual(self.codes(result),{"NO_ANIMAL_SOURCE_FOOD":"info","LOW_DIET_DIVERSITY":"info","LOW_MEAL_FREQUENCY":"info"})

    def test_each_reason_maps_to_its_own_indicator(self):
        cases=[(recall(food_groups=["grains_roots_tubers","pulses_nuts_seeds","dairy","vita_fruits_veg"]),"NO_ANIMAL_SOURCE_FOOD"),(recall(food_groups=["eggs"]),"LOW_DIET_DIVERSITY"),(recall(meal_count=2),"LOW_MEAL_FREQUENCY")]
        for row,code in cases:
            with self.subTest(code=code):self.assertEqual(self.codes(evaluate_diet(request([row]))),{code:"info"})

    def test_two_bad_records_raise_yellow(self):
        result=evaluate_diet(request([self.bad(),self.bad(1)]))
        self.assertTrue(all(reason["level"]=="yellow" for reason in result["reasons"]))
        self.assertEqual(len(result["reasons"]),3)

    def test_two_of_three_bad_still_active_after_one_good_day(self):
        result=evaluate_diet(request([recall(),self.bad(1),self.bad(2)]))
        self.assertTrue(result["diet"]["mdd"])
        self.assertTrue(all(reason["level"]=="yellow" for reason in result["reasons"]))

    def test_only_last_three_records_count(self):
        result=evaluate_diet(request([recall(),recall(1),recall(2),self.bad(3),self.bad(4)]))
        self.assertEqual(result["reasons"],[])

    def test_single_older_failure_is_not_a_current_reason(self):
        self.assertEqual(evaluate_diet(request([recall(),self.bad(1)]))["reasons"],[])

    def test_fourteen_calendar_dates_match_go(self):
        inside=evaluate_diet(request([self.bad(13)]))
        outside=evaluate_diet(request([self.bad(14)]))
        self.assertIsNotNone(inside["diet"])
        self.assertIsNone(outside["diet"])
        self.assertEqual(self.codes(outside),{"NO_RECENT_FOOD_RECALL":"info"})

    def test_seven_calendar_dates_boundary(self):
        self.assertNotIn("NO_RECENT_FOOD_RECALL",self.codes(evaluate_diet(request([recall(6)]))))
        self.assertIn("NO_RECENT_FOOD_RECALL",self.codes(evaluate_diet(request([recall(7)]))))

    def test_stale_pattern_and_missing_recent_record_coexist(self):
        result=evaluate_diet(request([self.bad(7),self.bad(8)]))
        self.assertEqual(self.codes(result)["NO_ANIMAL_SOURCE_FOOD"],"yellow")
        self.assertEqual(self.codes(result)["NO_RECENT_FOOD_RECALL"],"info")

    def test_empty_history(self):
        result=evaluate_diet(request())
        self.assertIsNone(result["diet"]);self.assertEqual(self.codes(result),{"NO_RECENT_FOOD_RECALL":"info"})

    def test_current_age_outside_scope_suppresses_diet(self):
        for age in (182,731):
            r=request(as_of=(BIRTH+timedelta(days=age)).isoformat())
            self.assertEqual(evaluate_diet(r),{"diet":None,"reasons":[]})

    def test_old_eligible_recall_does_not_warn_after_current_age_ends(self):
        row=recall(recall_date=(BIRTH+timedelta(days=730)).isoformat(),food_groups=[],meal_count=0)
        r=request([row],as_of=(BIRTH+timedelta(days=731)).isoformat())
        self.assertEqual(evaluate_diet(r),{"diet":None,"reasons":[]})

    def test_recall_age_used_for_mmf_not_current_age(self):
        now=BIRTH+timedelta(days=274)
        row=recall(recall_date=(BIRTH+timedelta(days=273)).isoformat(),meal_count=2)
        result=evaluate_diet(request([row],as_of=now.isoformat()))
        self.assertTrue(result["diet"]["mmf"])

    def test_unsorted_history_and_input_are_preserved(self):
        r=request([self.bad(2),recall(),recall(1)]);before=deepcopy(r.model_dump())
        result=evaluate_diet(r)
        self.assertEqual(result["diet"]["recall_date"],TODAY.isoformat())
        self.assertEqual(r.model_dump(),before)

    def test_duplicate_dates_cannot_inflate_pattern(self):
        with self.assertRaises(ValidationError):request([self.bad(),self.bad()])

    def test_future_dates_are_rejected_by_request_schema(self):
        with self.assertRaises(ValidationError):request([recall(-1)])


class GrowthDietCompositionTests(unittest.TestCase):
    def evaluate(self,rows,level="green",reasons=()):
        growth={"per_measurement":[],"level":level,"reasons":list(reasons)}
        original=deepcopy(growth)
        with patch("app.core.iycf.evaluate_early_warning",return_value=growth):
            result=evaluate_growth_and_diet(request(rows),WHOTables({}))
        self.assertEqual(growth,original)
        return result

    def test_one_bad_day_keeps_green(self):
        self.assertEqual(self.evaluate([recall(food_groups=[],meal_count=0)])["level"],"green")

    def test_repeated_bad_days_raise_yellow(self):
        self.assertEqual(self.evaluate([recall(food_groups=[],meal_count=0),recall(1,food_groups=[],meal_count=0)])["level"],"yellow")

    def test_growth_red_is_preserved_with_diet_evidence(self):
        reason={"code":"STUNTED","level":"red","evidence":{"indicator":"lhfa","to_z":-2.5}}
        result=self.evaluate([recall(food_groups=[],meal_count=0)],"red",[reason])
        self.assertEqual(result["level"],"red");self.assertEqual(result["reasons"][0],reason)
        self.assertEqual(len(result["reasons"]),4)

    def test_growth_yellow_is_not_lowered_by_healthy_diet(self):
        reason={"code":"CROSSING_DOWN","level":"yellow","evidence":{}}
        self.assertEqual(self.evaluate([recall()],"yellow",[reason])["level"],"yellow")

    def test_who_failure_does_not_become_green(self):
        with patch("app.core.iycf.evaluate_early_warning",side_effect=WHODataError("missing WHO")):
            with self.assertRaises(WHODataError):evaluate_growth_and_diet(request(),WHOTables({}))


@unittest.skipUnless(all((WHO_DATA_DIR / spec.filename).is_file() for spec in TABLE_SPECS.values()),"Install five official WHO tables")
class IYCFIntegrationTests(unittest.TestCase):
    def test_real_who_growth_and_repeated_diet_warning(self):
        tables=load_who_tables()
        age=(TODAY-BIRTH).days
        weight=tables.lookup("wfa","female",age).m
        length=round(tables.lookup("lhfa","female",age).m,1)
        r=request([recall(food_groups=[],meal_count=0),recall(1,food_groups=[],meal_count=0)],measurements=[dict(id=str(uuid4()),measured_at=TODAY.isoformat(),weight_kg=weight,length_height_cm=length,position="recumbent",source="posyandu")])
        result=evaluate_growth_and_diet(r,tables)
        self.assertEqual(result["level"],"yellow")
        self.assertEqual(len(result["per_measurement"]),1)
        self.assertIn("NO_ANIMAL_SOURCE_FOOD",[row["code"] for row in result["reasons"]])


if __name__=="__main__":unittest.main()
