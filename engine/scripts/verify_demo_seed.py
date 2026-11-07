"""Verify backend/migrations/005_seed_demo_measurements.sql with the real engine.

Usage (from engine/, WHO tables downloaded): python scripts/verify_demo_seed.py [--days N]
Simulates seeding on each of N days from today (002 birth_date = seed day - 11/13/15 months,
005 dates = birth_date + age months) and checks, for every measurement as it is entered
and for the full history as of the seed day and 14 days later:
  Anisa green -> yellow WEIGHT_NOT_GAINING -> red WEIGHT_NOT_GAINING_2X, lhfa >= -2;
  Bima green; Citra red STUNTED only. Info-level reasons are ignored.
"""
import argparse, calendar, re, sys
from datetime import date, timedelta
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

SEED = ENGINE.parent / "backend" / "migrations" / "005_seed_demo_measurements.sql"
CHILDREN = {"Anisa": ("female", 11), "Bima": ("male", 13), "Citra": ("female", 15)}  # as in 002


def add_months(d, k):  # PostgreSQL date + interval: clamp to month end
    y, m = divmod(d.year * 12 + d.month - 1 + k, 12)
    return date(y, m + 1, min(d.day, calendar.monthrange(y, m + 1)[1]))


def seed_rows():
    rows = re.findall(r"\('(\w+)', (\d+), ([\d.]+), ([\d.]+), ([\d.]+)\)", SEED.read_text(encoding="utf-8"))
    out = {}
    for name, age, w, l, hc in rows:
        out.setdefault(name, []).append((int(age), float(w), float(l), float(hc)))
    return out


def expected(name, cut, total):
    if name == "Bima":
        return "green", []
    if name == "Citra":
        return "red", ["STUNTED"]
    if cut == total:
        return "red", ["WEIGHT_NOT_GAINING_2X"]
    if cut == total - 1:
        return "yellow", ["WEIGHT_NOT_GAINING"]
    return "green", []


def check(client, rows, seed_day):
    failures = []
    for name, items in rows.items():
        sex, months = CHILDREN[name]
        birth = add_months(seed_day, -months)
        ms = [(add_months(birth, age), w, l, hc) for age, w, l, hc in sorted(items)]
        for cut in range(1, len(ms) + 1):
            prefix = ms[:cut]
            as_ofs = {prefix[-1][0]} | ({seed_day, seed_day + timedelta(days=14)} if cut == len(ms) else set())
            for as_of in sorted(as_ofs):
                body = {"as_of": as_of.isoformat(), "child": {"sex": sex, "birth_date": birth.isoformat()},
                        "measurements": [{"id": f"00000000-0000-4000-8000-{i:012d}", "measured_at": d.isoformat(),
                                          "weight_kg": w, "length_height_cm": l, "position": "recumbent",
                                          "head_circumference_cm": hc, "source": "posyandu"}
                                         for i, (d, w, l, hc) in enumerate(prefix)],
                        "kpsp_results": [], "food_recalls": []}
                r = client.post("/engine/v1/growth/evaluate", json=body)
                if r.status_code != 200:
                    failures.append((seed_day, name, cut, as_of, r.status_code, r.text[:200]))
                    continue
                data = r.json()["data"]
                codes = sorted(x["code"] for x in data["reasons"] if x["level"] != "info")
                lhfa = data["per_measurement"][-1]["z"]["lhfa"]
                if (data["level"], codes) != expected(name, cut, len(ms)) or (name == "Anisa" and lhfa < -2):
                    failures.append((seed_day, name, cut, as_of, data["level"], codes, lhfa))
    return failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1, help="number of seed days from today to simulate")
    args = parser.parse_args()
    client, rows, failures = TestClient(app), seed_rows(), []
    assert set(rows) == set(CHILDREN), rows.keys()
    for offset in range(args.days):
        failures += check(client, rows, date.today() + timedelta(days=offset))
    for f in failures[:20]:
        print("GAGAL", f)
    print(f"{args.days} hari seed diperiksa, {len(failures)} kegagalan")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
