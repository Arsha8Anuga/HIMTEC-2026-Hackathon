"""Strict KPSP shapes; score request matches the existing Go client body."""

import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from app.schemas.common import ContractModel

_RULES = json.loads((Path(__file__).resolve().parents[2] / "data" / "kpsp" / "rules.json").read_text(encoding="utf-8"))
ANSWER_COUNT = _RULES["answer_count"]
SCHEDULE = tuple(_RULES["schedule_months"])


class KpspAnswer(ContractModel):
    item_no: int = Field(strict=True, ge=1, le=ANSWER_COUNT)
    answer: bool = Field(strict=True)


class KpspScoreRequest(ContractModel):
    questionnaire_age_months: int = Field(strict=True)
    answers: list[KpspAnswer] = Field(min_length=ANSWER_COUNT, max_length=ANSWER_COUNT)

    @model_validator(mode="after")
    def validate_schedule_and_items(self):
        if self.questionnaire_age_months not in SCHEDULE:
            raise ValueError("questionnaire_age_months tidak ada dalam jadwal kontrak")
        if {item.item_no for item in self.answers} != set(range(1, ANSWER_COUNT + 1)):
            raise ValueError("answers wajib memuat item_no 1 sampai 10 masing-masing sekali")
        return self


class KpspItem(ContractModel):
    item_no: int = Field(strict=True, ge=1, le=ANSWER_COUNT)
    aspect: Literal["gerak_kasar", "gerak_halus", "bicara_bahasa", "sosialisasi_kemandirian"]
    question: str = Field(min_length=1)


class KpspQuestionnaire(ContractModel):
    questionnaire_age_months: int = Field(strict=True)
    items: list[KpspItem] = Field(min_length=ANSWER_COUNT, max_length=ANSWER_COUNT)

    @model_validator(mode="after")
    def validate_questionnaire(self):
        if self.questionnaire_age_months not in SCHEDULE:
            raise ValueError("umur kuesioner tidak ada dalam jadwal kontrak")
        if {item.item_no for item in self.items} != set(range(1, ANSWER_COUNT + 1)):
            raise ValueError("item_no harus lengkap dan unik")
        if any(not item.question.strip() for item in self.items):
            raise ValueError("question tidak boleh kosong")
        return self
