"""One-time setup: fetch pinned reference data from WHO's official Anthro repo.

Usage (from engine/): python scripts/fetch_who_tables.py
Requires internet at *setup only*. Runtime is completely offline.
The script validates upstream Git blob hashes before writing anything.

Do not commit/redistribute the downloaded GPL-3 tables without checking
and complying with WHO Anthro's LICENSE.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.request import urlopen

# Keep script runnable from any working directory.
ENGINE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE_ROOT))

from app.core.who_tables import (  # noqa: E402
    WHO_DATA_DIR,
    WHO_SOURCE_BLOBS,
    WHO_SOURCE_COMMIT,
    WHODataError,
    _parse_table,
    git_blob_sha,
    TABLE_SPECS,
)

RAW_BASE = (
    "https://raw.githubusercontent.com/WorldHealthOrganization/anthro/"
    + WHO_SOURCE_COMMIT + "/data-raw/growthstandards/"
)


def fetch_and_verify(fetch=urlopen) -> dict[str, bytes]:
    """All-or-nothing in-memory validation before persisting."""
    downloaded: dict[str, bytes] = {}
    for indicator, spec in TABLE_SPECS.items():
        with fetch(RAW_BASE + spec.filename, timeout=30) as response:
            data = response.read()
        if git_blob_sha(data) != WHO_SOURCE_BLOBS[spec.filename]:
            raise WHODataError(f"Checksum tidak cocok dari WHO: {spec.filename}")
        _parse_table(data, indicator)
        downloaded[spec.filename] = data
    return downloaded


def main() -> None:
    data = fetch_and_verify()
    WHO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, content in data.items():
        (WHO_DATA_DIR / filename).write_bytes(content)
    print("Lima tabel WHO resmi berhasil diverifikasi dan disimpan untuk penggunaan offline.")
    print("Periksa lisensi GPL-3 WHO Anthro sebelum distribusi data.")


if __name__ == "__main__":
    main()
