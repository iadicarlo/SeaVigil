#!/usr/bin/env python3
"""Look up every identified incident vessel in the GFW vessel-identity registry and
cache its flag + authorizations to data/authorizations.json (committed, so later builds
and CI need no token and rebuild offline).

Needs GFW_TOKEN (in .env or the environment). Run after regenerating incidents:
    uv run python scripts/fetch_authorizations.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make `seavigil` importable when run as a standalone script (package is not installed).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seavigil import authorization  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INCIDENTS = ROOT / "results" / "incidents" / "incidents.json"


def _token() -> str:
    tok = os.environ.get("GFW_TOKEN", "")
    if not tok:
        env = ROOT / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("GFW_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip("'\"")
                    break
    if not tok:
        raise SystemExit("GFW_TOKEN not set (put it in .env or the environment).")
    return tok


def main() -> None:
    inc = json.loads(INCIDENTS.read_text())
    mmsis = sorted({str(d.get("vessel_id")) for d in inc
                    if str(d.get("vessel_id") or "").isdigit() and len(str(d["vessel_id"])) == 9})
    print(f"identified vessels to look up: {len(mmsis)}")
    cache = authorization.build_cache(mmsis, _token())
    found = sum(1 for v in cache.values() if v.get("found"))
    with_auth = sum(1 for v in cache.values() if v.get("authorizations"))
    print(f"registry hits: {found}/{len(cache)} | with authorizations on record: {with_auth}")
    print(f"wrote {authorization.CACHE_PATH}")


if __name__ == "__main__":
    main()
