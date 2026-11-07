type Form = Record<string, unknown>;

/** Empty optional measurements must be JSON null, never an empty string. */
export function optionalNumber(value: unknown): number | null {
  if (value === "" || value === undefined || value === null) return null;
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error("Masukkan angka yang valid.");
  return number;
}

export function measurementBody(form: Form) {
  const length = optionalNumber(form.length_height_cm);
  return {
    measured_at: form.measured_at,
    weight_kg: optionalNumber(form.weight_kg),
    length_height_cm: length,
    head_circumference_cm: optionalNumber(form.head_circumference_cm),
    position: length === null ? null : form.position,
    source: form.source,
    note: form.note || null,
  };
}

export function childBody(form: Form) {
  return {
    name: String(form.name || "").trim(),
    sex: form.sex,
    birth_date: form.birth_date,
    is_preterm: form.is_preterm,
    birth_weight_kg: optionalNumber(form.birth_weight_kg),
    birth_length_cm: optionalNumber(form.birth_length_cm),
  };
}

export function foodBody(form: Form) {
  return {
    recall_date: form.recall_date,
    breastfed: form.breastfed,
    food_groups: form.food_groups,
    meal_count: optionalNumber(form.meal_count),
    milk_feed_count: optionalNumber(form.milk_feed_count),
  };
}
