"""KPSP core tests; synthetic bank items are format sentinels only."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from pydantic import ValidationError
from app.core.kpsp import load_kpsp_bank, round_kpsp_months, score_kpsp, select_kpsp_age
from app.schemas.kpsp import KpspQuestionnaire, KpspScoreRequest, SCHEDULE


def score_payload(yes=10):
    return {"questionnaire_age_months": 9, "answers": [{"item_no": n, "answer": n <= yes} for n in range(1,11)]}


def fake_bank():
    # NOT clinical content; never written to engine/data or shipped as a bank.
    return {"source": {"title":"TEST FORMAT ONLY", "url":"https://example.invalid/test", "verified_on":"2026-11-07"}, "questionnaires":[{"questionnaire_age_months": age, "items":[{"item_no":n,"aspect":"gerak_kasar","question":f"TEST FORMAT SENTINEL {age}/{n}, NOT CLINICAL"} for n in range(1,11)]} for age in SCHEDULE]}


class KpspScoreTests(unittest.TestCase):
    def test_all_eleven_possible_scores(self):
        for yes in range(11):
            with self.subTest(yes=yes):
                expected="sesuai" if yes>=9 else "meragukan" if yes>=7 else "penyimpangan"
                self.assertEqual(score_kpsp(KpspScoreRequest.model_validate(score_payload(yes))),{"yes_count":yes,"result":expected})

    def test_exactly_ten_items_required(self):
        for count in (0,9,11):
            p=score_payload();p["answers"]=(p["answers"]+[dict(item_no=1,answer=True)])[:count]
            with self.subTest(count=count),self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)

    def test_duplicate_or_out_of_range_item_rejected(self):
        for number in (0,1,11,True,1.0,"1"):
            p=score_payload();p["answers"][-1]["item_no"]=number
            with self.subTest(number=number),self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)

    def test_answers_are_strict_booleans(self):
        for value in (0,1,"true","false",None):
            p=score_payload();p["answers"][0]["answer"]=value
            with self.subTest(value=value),self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)

    def test_schedule_is_strict_and_contract_only(self):
        for age in (0,4,7,72,9.0,"9",True):
            p=score_payload();p["questionnaire_age_months"]=age
            with self.subTest(age=age),self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)

    def test_all_contract_ages_accepted(self):
        for age in SCHEDULE:
            p=score_payload();p["questionnaire_age_months"]=age
            self.assertEqual(score_kpsp(KpspScoreRequest.model_validate(p))["yes_count"],10)

    def test_unknown_fields_rejected(self):
        p=score_payload();p["result"]="sesuai"
        with self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)
        p=score_payload();p["answers"][0]["question"]="extra"
        with self.assertRaises(ValidationError):KpspScoreRequest.model_validate(p)

    def test_scoring_preserves_unsorted_answers(self):
        p=score_payload(7);p["answers"].reverse()
        request=KpspScoreRequest.model_validate(p);before=deepcopy(request.model_dump())
        self.assertEqual(score_kpsp(request),{"yes_count":7,"result":"meragukan"})
        self.assertEqual(request.model_dump(),before)


class KpspAgePrimitiveTests(unittest.TestCase):
    def test_user_confirmed_rounding_boundary(self):
        # User explicitly resolved day 16 upward on 2026-11-07.
        for days,expected in ((0,8),(15,8),(16,9),(17,9),(30,9)):
            self.assertEqual(round_kpsp_months(8,days),expected)

    def test_invalid_age_components(self):
        for months,days in ((-1,0),(True,0),(1.5,0),(8,-1),(8,31),(8,True),(8,16.0)):
            with self.subTest(months=months,days=days),self.assertRaises(ValueError):round_kpsp_months(months,days)

    def test_schedule_selection_between_and_at_ages(self):
        for months,expected in ((0,None),(2,None),(3,3),(5,3),(6,6),(8,6),(9,9),(23,21),(24,24),(29,24),(30,30),(59,54),(60,60)):
            self.assertEqual(select_kpsp_age(months),expected)

    def test_schedule_rejects_outside_scope_and_coercion(self):
        for months in (-1,61,72,True,9.0,"9"):
            with self.subTest(months=months),self.assertRaises(ValueError):select_kpsp_age(months)


class KpspBankTests(unittest.TestCase):
    def read(self,data):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"bank.json";path.write_text(json.dumps(data),encoding="utf-8")
            return load_kpsp_bank(path, for_review=True)

    def test_complete_synthetic_format_can_be_parsed(self):
        bank=self.read(fake_bank())
        self.assertEqual(set(bank),set(SCHEDULE));self.assertTrue(all(len(q.items)==10 for q in bank.values()))

    def test_missing_bank_never_fabricates_questions(self):
        with tempfile.TemporaryDirectory() as folder,self.assertRaises(ValueError):load_kpsp_bank(Path(folder)/"missing.json")

    def test_corrupt_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"bad.json";p.write_text("{",encoding="utf-8")
            with self.assertRaises(ValueError):load_kpsp_bank(p)

    def test_source_metadata_is_required(self):
        for key in ("title","url","verified_on"):
            p=fake_bank();del p["source"][key]
            with self.subTest(key=key),self.assertRaises(ValueError):self.read(p)

    def test_incomplete_or_duplicate_age_bank_rejected(self):
        for duplicate in (False,True):
            p=fake_bank()
            if duplicate:p["questionnaires"][-1]=deepcopy(p["questionnaires"][0])
            else:p["questionnaires"].pop()
            with self.subTest(duplicate=duplicate),self.assertRaises(ValueError):self.read(p)

    def test_duplicate_item_unknown_aspect_and_blank_question_rejected(self):
        for field,value in (("item_no",2),("aspect","other"),("question","   ")):
            p=fake_bank();p["questionnaires"][0]["items"][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.read(p)

    def test_questionnaire_has_no_undocumented_fields(self):
        p=fake_bank()["questionnaires"][0];p["diagnosis"]="normal"
        with self.assertRaises(ValidationError):KpspQuestionnaire.model_validate(p)


if __name__=="__main__":unittest.main()
