"""Patch 03: deterministic offline tests, without shipping invented clinical data.

The full-grid fixtures below are explicitly synthetic *format fixtures*.
They never enter engine/data/who or any user-facing medical calculation.
"""

from __future__ import annotations

from hashlib import sha1
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.who_tables import (
    TABLE_SPECS,
    WHODataError,
    WHO_SOURCE_BLOBS,
    LMS,
    _parse_table,
    git_blob_sha,
    load_who_tables,
    who_tables_loaded,
)
from app.main import create_app
from scripts import fetch_who_tables


def _tsv(indicator: str, rows: list[tuple[int, int, str, str, str]]) -> bytes:
    """Small made-up rows for parser validation, not reference data."""
    spec = TABLE_SPECS[indicator]
    keys = ["sex", spec.axis, "l", "m", "s"]
    if spec.extra_header:
        keys.append(spec.extra_header)
    lines = ["\t".join(keys)]
    for sex, index, l, m, s in rows:
        x = str(index if spec.axis == "age" else index / 10)
        values = [str(sex), x, l, m, s]
        if spec.extra_header == "loh":
            values.append("L" if index < 731 else "H")
        if spec.extra_header == "lorh":
            values.append(spec.expected_marker)
        lines.append("\t".join(values))
    return ("\n".join(lines) + "\n").encode()


def _full_fake_tables(directory: Path) -> dict[str, str]:
    """Generate complete *synthetic* grids purely to exercise the loader."""
    checksums = {}
    for indicator, spec in TABLE_SPECS.items():
        rows = []
        for sex in (1, 2):
            for index in range(spec.min_index, spec.max_index + 1):
                # These are test parser sentinels, NOT WHO medical measurements.
                rows.append((sex, index, "1", "10", "0.1"))
        data = _tsv(indicator, rows)
        (directory / spec.filename).write_bytes(data)
        checksums[spec.filename] = git_blob_sha(data)
    return checksums


def test_git_blob_sha_matches_git_algorithm() -> None:
    raw = b"test\n"
    expected = sha1(b"blob 5\x00test\n").hexdigest()
    assert git_blob_sha(raw) == expected


def test_official_who_sample_row_parses() -> None:
    # Read from official WorldHealthOrganization/anthro weianthro.txt, first row.
    original = b"sex\tage\tl\tm\ts\n1\t0\t0.3487\t3.3464\t0.14602\n"
    assert _parse_table(original, "wfa", strict_coverage=False)["wfa", 1, 0] == LMS(
        0.3487, 3.3464, 0.14602
    )


def test_all_five_native_who_headers_are_supported() -> None:
    for indicator, spec in TABLE_SPECS.items():
        raw = _tsv(indicator, [(1, spec.min_index, "1", "10", "0.1")])
        loaded = _parse_table(raw, indicator, strict_coverage=False)
        assert loaded[indicator, 1, spec.min_index] == LMS(1.0, 10.0, 0.1)


def test_malformed_headers_rejected() -> None:
    with pytest.raises(WHODataError, match="Header"):
        _parse_table(b"sex,age,L,M,S\n1,0,1,10,0.1\n", "wfa", strict_coverage=False)


@pytest.mark.parametrize("bad", [(0, 0, "1", "10", "0.1"), (3, 0, "1", "10", "0.1"), (1, 0, "1", "0", "0.1"), (1, 0, "1", "10", "0"), (1, 0, "nan", "10", "0.1"), (1, 1827, "1", "10", "0.1")])
def test_bad_rows_rejected(bad) -> None:
    with pytest.raises(WHODataError):
        _parse_table(_tsv("wfa", [bad]), "wfa", strict_coverage=False)


def test_reject_duplicate_axis_value() -> None:
    raw = _tsv("wfa", [(1, 0, "1", "10", "0.1"), (1, 0, "1", "10", "0.1")])
    with pytest.raises(WHODataError, match="duplikat"):
        _parse_table(raw, "wfa", strict_coverage=False)


def test_reject_wrong_marker_at_24_months() -> None:
    raw = b"sex\tage\tl\tm\ts\tloh\n1\t731\t1\t10\t0.1\tL\n"
    with pytest.raises(WHODataError, match="posisi"):
        _parse_table(raw, "lhfa", strict_coverage=False)


def test_reject_imprecise_lengths() -> None:
    raw = b"sex\tlength\tl\tm\ts\tlorh\n1\t45.03\t1\t10\t0.1\tL\n"
    with pytest.raises(WHODataError, match="Nilai rusak"):
        _parse_table(raw, "wfl", strict_coverage=False)


def test_reject_non_finite_or_unparseable_axis() -> None:
    for invalid in ("NaN", "inf", "oops"):
        raw = f"sex\tage\tl\tm\ts\n1\t{invalid}\t1\t10\t0.1\n".encode()
        with pytest.raises(WHODataError):
            _parse_table(raw, "wfa", strict_coverage=False)


def test_strict_parser_rejects_partial_data() -> None:
    raw = _tsv("wfa", [(1, 0, "1", "10", "0.1")])
    with pytest.raises(WHODataError, match="tidak lengkap"):
        _parse_table(raw, "wfa")


def test_missing_files_refused_and_health_false(tmp_path: Path) -> None:
    with pytest.raises(WHODataError, match="belum tersedia"):
        load_who_tables(tmp_path)
    assert who_tables_loaded(tmp_path) is False


def test_corrupt_file_refused_even_with_good_other_files(tmp_path: Path) -> None:
    checksums = _full_fake_tables(tmp_path)
    first_file = tmp_path / "weianthro.txt"
    first_file.write_bytes(first_file.read_bytes() + b"TAMPERED")
    with pytest.raises(WHODataError, match="Checksum"):
        load_who_tables(tmp_path, source_blobs=checksums)


def test_valid_complete_synthetic_grids_can_be_loaded(tmp_path: Path) -> None:
    checksums = _full_fake_tables(tmp_path)
    tables = load_who_tables(tmp_path, source_blobs=checksums)
    # Synthetic sentinel values verify indexing, not clinical accuracy.
    assert tables.lookup("wfa", "male", 0) == LMS(1, 10, 0.1)
    assert tables.lookup("wfa", "female", 1826) == LMS(1, 10, 0.1)
    assert tables.lookup("wfl", "female", 45.1) == LMS(1, 10, 0.1)
    assert tables.lookup("wfh", "male", 120.0) == LMS(1, 10, 0.1)
    assert tables.lookup("lhfa", "male", 731) == LMS(1, 10, 0.1)
    assert tables.lookup("hcfa", "female", 1826) == LMS(1, 10, 0.1)
    assert len(tables.rows) == sum(2 * (spec.max_index - spec.min_index + 1) for spec in TABLE_SPECS.values())
    for args in (("wfa", "female", 1856), ("wfl", "male", 45.05)):
        with pytest.raises(WHODataError):
            tables.lookup(*args)
    for args in (("bad", "male", 1), ("wfa", "bad", 1)):
        with pytest.raises(ValueError):
            tables.lookup(*args)


def test_valid_shape_but_not_official_hash_is_rejected(tmp_path: Path) -> None:
    _full_fake_tables(tmp_path)
    with pytest.raises(WHODataError, match="Checksum"):
        load_who_tables(tmp_path)  # Default only trusts pinned WHO data.
    assert who_tables_loaded(tmp_path) is False


def test_health_stays_false_without_complete_official_data(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.api.health.who_tables_loaded", lambda: who_tables_loaded(tmp_path))
    with TestClient(create_app()) as client:
        response = client.get("/engine/v1/health")
    assert response.status_code == 200
    assert response.json()["data"] == {"status": "ok", "who_tables_loaded": False}


def test_fetch_script_rejects_wrong_source_sha() -> None:
    class BytesResponse(BytesIO):
        pass

    def fake_download(url, *, timeout):
        assert url.startswith(fetch_who_tables.RAW_BASE)
        return BytesResponse(b"untrusted upstream bytes")

    with pytest.raises(WHODataError, match="Checksum"):
        fetch_who_tables.fetch_and_verify(fake_download)


def test_source_checksums_list_only_official_who_tables() -> None:
    assert set(WHO_SOURCE_BLOBS) == {spec.filename for spec in TABLE_SPECS.values()}
    assert all(len(blob) == 40 for blob in WHO_SOURCE_BLOBS.values())
