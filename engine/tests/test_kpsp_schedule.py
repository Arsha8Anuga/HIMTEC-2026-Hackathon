"""SDIDTK age examples, explicit day-16 policy, and source transcription tests."""

from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from app.core.kpsp import kpsp_age_components, load_kpsp_bank, next_kpsp, round_kpsp_months, select_kpsp_age
from app.schemas.growth import GrowthEvaluateRequest
from scripts.import_kpsp_markdown import transcribe

DATA = Path(__file__).resolve().parents[1] / "data" / "kpsp" / "questionnaires.json"


def request(as_of, history=(), birth="2024-01-01"):
    return GrowthEvaluateRequest(as_of=as_of, child=dict(sex="female", birth_date=birth), measurements=[], kpsp_results=list(history), food_recalls=[])


class KpspScheduleTests(unittest.TestCase):
    def test_guideline_age_example(self):
        self.assertEqual(kpsp_age_components(date(2018,9,25),date(2020,4,15)),(18,20))

    def test_approved_eight_months_sixteen_days(self):
        result=next_kpsp(request("2024-09-17"))
        self.assertEqual(result,dict(questionnaire_age_months=9,due=True))

    def test_fifteen_days_does_not_round(self):
        self.assertEqual(next_kpsp(request("2024-09-16")),dict(questionnaire_age_months=6,due=True))

    def test_30_day_borrow_not_real_month_length(self):
        cases=[(date(2024,1,31),date(2024,2,1),(0,0)),(date(2024,1,31),date(2024,2,29),(0,28)),(date(2024,1,31),date(2024,3,1),(1,0)),(date(2023,12,25),date(2024,1,15),(0,20)),(date(2024,2,29),date(2025,2,28),(11,29))]
        for birth,now,expected in cases:
            with self.subTest(birth=birth,now=now):self.assertEqual(kpsp_age_components(birth,now),expected)

    def test_birth_day_and_prebirth_rejection(self):
        self.assertEqual(kpsp_age_components(date(2024,1,1),date(2024,1,1)),(0,0))
        for birth,now in ((date(2024,1,2),date(2024,1,1)),("2024-01-01",date(2024,1,2)),(datetime(2024,1,1),date(2024,1,2))):
            with self.assertRaises(ValueError):kpsp_age_components(birth,now)

    def test_under_first_age_is_upcoming_not_due(self):
        self.assertEqual(next_kpsp(request("2024-02-01")),dict(questionnaire_age_months=3,due=False))

    def test_rounded_first_age_is_due(self):
        self.assertEqual(next_kpsp(request("2024-03-17")),dict(questionnaire_age_months=3,due=True))

    def test_completed_normal_moves_to_next_form(self):
        history=[dict(questionnaire_age_months=9,answered_at="2024-10-01",result="sesuai")]
        self.assertEqual(next_kpsp(request("2024-11-01",history)),dict(questionnaire_age_months=12,due=False))

    def test_new_age_eligible_is_due(self):
        history=[dict(questionnaire_age_months=9,answered_at="2024-10-01",result="sesuai")]
        self.assertEqual(next_kpsp(request("2025-01-01",history)),dict(questionnaire_age_months=12,due=True))

    def test_doubtful_repeats_same_form_at_two_weeks(self):
        history=[dict(questionnaire_age_months=6,answered_at="2024-09-01",result="meragukan")]
        for day,due in ((14,False),(15,True),(17,True)):
            with self.subTest(day=day):self.assertEqual(next_kpsp(request(date(2024,9,day),history)),dict(questionnaire_age_months=6,due=due))

    def test_deviation_does_not_request_automatic_self_rescreen(self):
        history=[dict(questionnaire_age_months=6,answered_at="2024-09-01",result="penyimpangan")]
        self.assertEqual(next_kpsp(request("2024-10-01",history)),dict(questionnaire_age_months=6,due=False))

    def test_latest_result_supersedes_older_doubtful(self):
        history=[dict(questionnaire_age_months=6,answered_at="2024-09-01",result="meragukan"),dict(questionnaire_age_months=6,answered_at="2024-09-15",result="sesuai")]
        self.assertEqual(next_kpsp(request("2024-09-15",list(reversed(history)))),dict(questionnaire_age_months=9,due=False))

    def test_terminal_age_does_not_invent_66_month_schedule(self):
        history=[dict(questionnaire_age_months=60,answered_at="2029-01-01",result="sesuai")]
        self.assertEqual(next_kpsp(request("2029-01-01",history)),dict(questionnaire_age_months=60,due=False))
        with self.assertRaises(ValueError):next_kpsp(request("2029-01-17"))

    def test_request_is_not_mutated(self):
        r=request("2024-09-17");before=r.model_dump(mode="json")
        next_kpsp(r);self.assertEqual(r.model_dump(mode="json"),before)


class KpspTranscriptionTests(unittest.TestCase):
    def test_shipped_bank_contains_140_real_source_items_in_order(self):
        bank=load_kpsp_bank(for_review=True)
        self.assertEqual(len(bank),14)
        self.assertEqual(sum(len(form.items) for form in bank.values()),140)
        self.assertTrue(bank[3].items[0].question.startswith("Pada saat bayi terlentang"))
        self.assertEqual([i.item_no for i in bank[60].items],list(range(1,11)))
        self.assertFalse(any("TEST FORMAT" in i.question for q in bank.values() for i in q.items))

    def test_incomplete_visuals_block_default_runtime(self):
        with self.assertRaisesRegex(ValueError,"belum siap tayang"):load_kpsp_bank()
        data=json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(data["source"]["visual_assets_status"],"missing")
        self.assertIn(8,data["source"]["image_dependent_items"]["3"])

    def test_review_flag_does_not_skip_structural_validation(self):
        data=json.loads(DATA.read_text(encoding="utf-8"));data["questionnaires"].pop()
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"bank.json";p.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"belum lengkap"):load_kpsp_bank(p,for_review=True)

    def test_attribution_and_image_references_preserved(self):
        data=json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(data["source"]["input_filename"],"BUKU-PEDOMAN-SDIDTK-revisi-23082022.md")
        self.assertRegex(data["source"]["input_sha256"],r"^[a-f0-9]{64}$")
        self.assertEqual(data["source"]["observed_printed_pages"]["3"],[122])
        self.assertEqual(data["source"]["observed_printed_pages"]["9"],[124,125])
        form=next(q for q in data["questionnaires"] if q["questionnaire_age_months"]==21)
        self.assertIn("gambar",form["items"][2]["question"])

    def test_transcriber_handles_wrapped_aspects_and_split_ten(self):
        text=""
        for age in (3,6,9,12,15,18,21,24,30,36,42,48,54,60):
            text+=f"Kuesioner Pra Skrining Perkembangan (KPSP) Anak Umur {age} Bulan\n"
            for item in range(1,11):
                prefix=f"{item}. " if item<10 else "10\n.\n"
                text+=prefix+"TEST FORMAT ONLY, NOT CLINICAL.\nBicara dan\nbahasa\n"
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"source.md";p.write_text(text,encoding="utf-8")
            data=transcribe(p)
        self.assertEqual(data["questionnaires"][0]["items"][-1]["aspect"],"bicara_bahasa")
        self.assertEqual(data["source"]["input_sha256"],sha256(text.encode()).hexdigest())

    def test_missing_source_forms_fail_transcription(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"source.md";p.write_text("No forms",encoding="utf-8")
            with self.assertRaises(ValueError):transcribe(p)


if __name__=="__main__":unittest.main()
