export const referenceKeys = [
  "sd_neg3",
  "sd_neg2",
  "median",
  "sd_pos2",
  "sd_pos3",
] as const;
export interface GrowthPoint {
  measurement_id: string;
  measured_at: string;
  x: number;
  value: number;
  z: number | null;
  flagged: boolean;
}
export interface GrowthData {
  indicator: "wfa" | "lhfa" | "wfl_wfh" | "hcfa";
  x_unit: "days" | "cm";
  points: GrowthPoint[];
  reference: Record<(typeof referenceKeys)[number] | "x", number[]>;
}

/** Validate chart structure only; no medical thresholds or generated references. */
export function isGrowthData(data: unknown): data is GrowthData {
  if (!data || typeof data !== "object") return false;
  const d = data as GrowthData;
  if (!["wfa", "lhfa", "wfl_wfh", "hcfa"].includes(d.indicator)) return false;
  if (!["days", "cm"].includes(d.x_unit) || !Array.isArray(d.points))
    return false;
  const r = d.reference;
  if (!r || !Array.isArray(r.x)) return false;
  if (
    ![r.x, ...referenceKeys.map((key) => r[key])].every(
      (values) =>
        Array.isArray(values) &&
        values.length === r.x.length &&
        values.every(Number.isFinite),
    )
  )
    return false;
  return d.points.every(
    (p) =>
      p &&
      Number.isFinite(p.x) &&
      Number.isFinite(p.value) &&
      typeof p.flagged === "boolean",
  );
}
