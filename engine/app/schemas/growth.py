"""Inputs to POST /engine/v1/growth/evaluate (CONTRACT.md v0.4).

This module defines shapes and basic validation only. It does not perform
medical computations or introduce new clinical thresholds.
"""

from datetime import date
from typing import Literal

from pydantic import AwareDatetime, Field, UUID4, model_validator

from app.schemas.common import ContractModel


Sex = Literal["male", "female"]
Position = Literal["recumbent", "standing"]
Source = Literal["posyandu", "puskesmas", "home"]
KpspOutcome = Literal["sesuai", "meragukan", "penyimpangan"]
FoodGroup = Literal[
    "grains_roots_tubers",
    "pulses_nuts_seeds",
    "dairy",
    "flesh_foods",
    "eggs",
    "vita_fruits_veg",
    "other_fruits_veg",
]


class ChildInput(ContractModel):
    sex: Sex
    birth_date: date


class MeasurementInput(ContractModel):
    id: UUID4
    measured_at: date
    weight_kg: float = Field(ge=0.5, le=40, strict=True)
    length_height_cm: float | None = Field(default=None, ge=40, le=130, strict=True)
    position: Position | None = None
    head_circumference_cm: float | None = Field(default=None, ge=30, le=60, strict=True)
    source: Source

    @model_validator(mode="after")
    def position_required_for_length(self) -> "MeasurementInput":
        if self.length_height_cm is not None and self.position is None:
            raise ValueError("position wajib jika length_height_cm diisi")
        return self


class KpspHistoryInput(ContractModel):
    questionnaire_age_months: Literal[3, 6, 9, 12, 15, 18, 21, 24, 30, 36, 42, 48, 54, 60]
    answered_at: date
    result: KpspOutcome


class FoodRecallInput(ContractModel):
    """FoodRecall without database ids; created_at is optional history metadata."""

    recall_date: date
    breastfed: bool = Field(strict=True)
    food_groups: list[FoodGroup]
    meal_count: int = Field(ge=0, le=10, strict=True)
    milk_feed_count: int | None = Field(default=None, ge=0, le=10, strict=True)
    created_at: AwareDatetime | None = None


class GrowthEvaluateRequest(ContractModel):
    as_of: date
    child: ChildInput
    measurements: list[MeasurementInput]
    kpsp_results: list[KpspHistoryInput]
    food_recalls: list[FoodRecallInput]

    @model_validator(mode="after")
    def validate_dates(self) -> "GrowthEvaluateRequest":
        if self.as_of < self.child.birth_date:
            raise ValueError("as_of tidak boleh sebelum birth_date")
        measurement_ids: set[UUID4] = set()
        measurement_dates: set[date] = set()
        for measurement in self.measurements:
            if measurement.measured_at < self.child.birth_date:
                raise ValueError("measured_at tidak boleh sebelum birth_date")
            if measurement.measured_at > self.as_of:
                raise ValueError("measured_at tidak boleh setelah as_of")
            if (measurement.measured_at - self.child.birth_date).days > 1826:
                raise ValueError("umur pada measured_at tidak boleh lebih dari 1826 hari")
            if measurement.id in measurement_ids:
                raise ValueError("id pengukuran tidak boleh duplikat")
            if measurement.measured_at in measurement_dates:
                raise ValueError("hanya satu pengukuran per tanggal")
            measurement_ids.add(measurement.id)
            measurement_dates.add(measurement.measured_at)
        for item in self.kpsp_results:
            if item.answered_at < self.child.birth_date:
                raise ValueError("answered_at tidak boleh sebelum birth_date")
            if item.answered_at > self.as_of:
                raise ValueError("answered_at tidak boleh setelah as_of")
        recall_dates: set[date] = set()
        for item in self.food_recalls:
            if item.recall_date < self.child.birth_date:
                raise ValueError("recall_date tidak boleh sebelum birth_date")
            if item.recall_date > self.as_of:
                raise ValueError("recall_date tidak boleh setelah as_of")
            # CONTRACT v0.4 defines months as days / 30.4375. Use the
            # unrounded age on the recall date, not the display age/as_of.
            age_months = (item.recall_date - self.child.birth_date).days / 30.4375
            if not 6 <= age_months < 24:
                raise ValueError("umur pada recall_date harus 6 sampai kurang dari 24 bulan")
            if item.recall_date in recall_dates:
                raise ValueError("hanya satu catatan makan per tanggal")
            recall_dates.add(item.recall_date)
        return self
