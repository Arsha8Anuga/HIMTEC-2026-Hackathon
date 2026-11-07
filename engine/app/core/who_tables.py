"""Verified, offline loader for WHO 2006 LMS growth reference tables.

Upstream: https://github.com/WorldHealthOrganization/anthro/tree/master/data-raw/growthstandards
Pinned commit: b776d8a12b1c97369c748b561159fd2ec4f4db58
The downloaded upstream files are copyright WHO, distributed there under GPL-3.

Only reads WHO data. Does NOT calculate z-scores or classify children.
All five real, complete files must be present and match Git blob hashes.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha1
from io import StringIO
from math import isfinite
from pathlib import Path
from typing import Mapping

WHO_SOURCE_COMMIT = "b776d8a12b1c97369c748b561159fd2ec4f4db58"
WHO_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "who"

# SHA-1 is Git's *blob object identifier*, not a password hash.
# Files pinned to the official WorldHealthOrganization/anthro repository.
WHO_SOURCE_BLOBS: dict[str, str] = {
    "weianthro.txt": "e2af85d4a973ca1fe4f731c401a770287c57e1db",
    "lenanthro.txt": "e592bb0dbf4f1c25c4607a7160a33d84b0fb5308",
    "wflanthro.txt": "3b5620579a42e380b73705359b97754d8fbefab6",
    "wfhanthro.txt": "2efe8d2b0ce5ff19bec33d97d1c98e3808c03de8",
    "hcanthro.txt": "53e2f8bf9a367976052af1fb0d84be177c80dd8a",
}

# WHO anthro uses WHO sex codes: 1=male, 2=female.
# WHO's daily age grid covers 0..1826 (60 months ~= 1826.25 days).
# Contract v0.6 limits measurements to day 1826 to match this grid.
@dataclass(frozen=True)
class TableSpec:
    filename: str
    axis: str
    min_index: int
    max_index: int
    extra_header: str | None = None
    expected_marker: str | None = None


TABLE_SPECS: dict[str, TableSpec] = {
    "wfa": TableSpec("weianthro.txt", "age", 0, 1826),
    "lhfa": TableSpec("lenanthro.txt", "age", 0, 1826, "loh"),
    "wfl": TableSpec("wflanthro.txt", "length", 450, 1100, "lorh", "L"),
    "wfh": TableSpec("wfhanthro.txt", "height", 650, 1200, "lorh", "H"),
    "hcfa": TableSpec("hcanthro.txt", "age", 0, 1826),
}


class WHODataError(ValueError):
    """WHO data missing, corrupt, incomplete, or not from the pinned source."""


@dataclass(frozen=True)
class LMS:
    l: float
    m: float
    s: float


@dataclass(frozen=True)
class WHOTables:
    # Index: (indicator, WHO sex code, day or tenths of a centimetre).
    rows: Mapping[tuple[str, int, int], LMS]

    def lookup(self, indicator: str, sex: str, x: int | float | Decimal) -> LMS:
        """Exact table lookup. No interpolation, extrapolation, or rounding."""
        if indicator not in TABLE_SPECS:
            raise ValueError("Indikator WHO tidak dikenal")
        if sex not in ("male", "female"):
            raise ValueError("Jenis kelamin tidak dikenal")
        axis = TABLE_SPECS[indicator].axis
        index = _axis_index(x, axis)
        try:
            return self.rows[(indicator, 1 if sex == "male" else 2, index)]
        except KeyError as exc:
            raise WHODataError("Koordinat di luar tabel referensi WHO") from exc


def git_blob_sha(data: bytes) -> str:
    """Compute SHA-1 for a Git blob (length-prefixed, unlike raw SHA-1)."""
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def _axis_index(value: int | float | Decimal | str, axis: str) -> int:
    if isinstance(value, bool):
        raise WHODataError("Koordinat WHO tidak valid")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise WHODataError("Koordinat WHO tidak valid") from exc
    if not d.is_finite():
        raise WHODataError("Koordinat WHO tidak valid")
    scaled = d if axis == "age" else d * 10
    if scaled != scaled.to_integral_value():
        raise WHODataError("Koordinat WHO harus tepat: umur per hari atau ukuran per 0,1 cm")
    return int(scaled)


def _parse_table(raw: bytes, indicator: str, *, strict_coverage: bool = True) -> dict[tuple[str, int, int], LMS]:
    """Parse the official WHO anthro TSV schema; strict mode rejects incomplete grids."""
    spec = TABLE_SPECS[indicator]
    header = ["sex", spec.axis, "l", "m", "s"]
    if spec.extra_header:
        header.append(spec.extra_header)
    try:
        reader = csv.DictReader(StringIO(raw.decode("utf-8-sig")), delimiter="\t")
        if reader.fieldnames != header:
            raise WHODataError(f"Header WHO tidak cocok untuk {spec.filename}")
        rows: dict[tuple[str, int, int], LMS] = {}
        for line_number, row in enumerate(reader, start=2):
            try:
                sex = int(row["sex"])
                x = _axis_index(row[spec.axis], spec.axis)
                l, m, s = float(row["l"]), float(row["m"]), float(row["s"])
            except (ValueError, TypeError, KeyError, WHODataError) as exc:
                raise WHODataError(f"Nilai rusak pada {spec.filename} baris {line_number}") from exc
            if sex not in (1, 2) or x < spec.min_index or x > spec.max_index:
                raise WHODataError(f"Domain WHO tidak valid pada {spec.filename} baris {line_number}")
            if not all(isfinite(v) for v in (l, m, s)) or m <= 0 or s <= 0:
                raise WHODataError(f"Parameter LMS tidak valid pada {spec.filename} baris {line_number}")
            if spec.expected_marker is not None and row[spec.extra_header] != spec.expected_marker:
                raise WHODataError(f"Penanda posisi salah pada {spec.filename} baris {line_number}")
            if indicator == "lhfa" and row["loh"] != ("L" if x < 731 else "H"):
                raise WHODataError(f"Penanda umur/posisi tidak cocok pada {spec.filename} baris {line_number}")
            key = (indicator, sex, x)
            if key in rows:
                raise WHODataError(f"Baris duplikat pada {spec.filename} baris {line_number}")
            rows[key] = LMS(l, m, s)
        if strict_coverage:
            expected = 2 * (spec.max_index - spec.min_index + 1)
            if len(rows) != expected:
                raise WHODataError(f"Tabel {spec.filename} tidak lengkap ({len(rows)} dari {expected})")
            # Number + exact allowed range + unique keys implies the complete grid.
        return rows
    except UnicodeError as exc:
        raise WHODataError(f"Encoding tidak valid pada {spec.filename}") from exc


def load_who_tables(
    directory: Path = WHO_DATA_DIR,
    *,
    source_blobs: Mapping[str, str] = WHO_SOURCE_BLOBS,
) -> WHOTables:
    """Load all five pinned WHO files, rejecting missing/modified/incomplete data.

    `source_blobs` is injectable for tests; production defaults to verified WHO hashes.
    Does not access the network or add a database.
    """
    result: dict[tuple[str, int, int], LMS] = {}
    for indicator, spec in TABLE_SPECS.items():
        try:
            raw = (Path(directory) / spec.filename).read_bytes()
        except OSError as exc:
            raise WHODataError(f"Tabel WHO belum tersedia: {spec.filename}") from exc
        if git_blob_sha(raw) != source_blobs.get(spec.filename):
            raise WHODataError(f"Checksum WHO tidak sesuai: {spec.filename}")
        result.update(_parse_table(raw, indicator))
    return WHOTables(rows=result)


def who_tables_loaded(directory: Path = WHO_DATA_DIR) -> bool:
    """True only when the *full authentic* WHO data set can be loaded."""
    try:
        load_who_tables(directory)
    except WHODataError:
        return False
    return True
