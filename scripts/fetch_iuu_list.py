#!/usr/bin/env python3
"""Fetch RFMO IUU (illegal, unreported, unregulated) vessel blacklists into one normalized file.

This is the reference data that lets SeaVigil ADJUDICATE, not just detect: a detection whose identity
matches a vessel an RFMO has listed for IUU fishing is no longer an "unverifiable" lead, it is a known
offender. The lists are public (each Regional Fisheries Management Organisation publishes its own; the
FAO Global Record is the directory). We keep current AND previous names, because IUU vessels rename
constantly to shake their history, and the aliases are how you still catch them.

Extensible by design: add a parser to SOURCES and it joins the merged output. Output:
data/iuu/iuu_vessels.json. Run: uv run python scripts/fetch_iuu_list.py
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "iuu" / "iuu_vessels.json"


def _get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "SeaVigil/1.0 (IUU reference fetch)"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "").replace("\xa0", " ")).strip()


def parse_ccamlr(html: str, list_name: str) -> list[dict]:
    """CCAMLR publishes a Drupal views table: one row per vessel, cells keyed by views-field-* class."""
    body = re.search(r"<tbody[^>]*>(.*?)</tbody>", html, re.S)
    if not body:
        return []
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", body.group(1), re.S):
        cells = {}
        for cls, content in re.findall(r"<t[dh][^>]*\bviews-field-([a-z0-9-]+)[^>]*>(.*?)</t[dh]>", row, re.S):
            cells.setdefault(re.sub(r"^field-", "", cls), content)
        title = cells.get("title", "")
        nm = re.search(r"<a[^>]*>(.*?)</a>", title, re.S)
        name = _strip(nm.group(1)) if nm else _strip(re.split(r"<div", title)[0])
        if not name:
            continue
        aliases = [_strip(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", title, re.S)]
        out.append({
            "source": "CCAMLR", "list": list_name,
            "name": name, "aliases": [a for a in aliases if a and a.lower() != name.lower()],
            "flag": _strip(cells.get("flag", "")),
            "imo": _strip(cells.get("imo-number", "")),
            "callsign": _strip(cells.get("callsign", "")),
            "date_listed": _strip(cells.get("date-listed", "")),
        })
    return out


SOURCES = {
    "CCAMLR Non-Contracting Party": {
        "url": "https://www.ccamlr.org/en/compliance/non-contracting-party-iuu-vessel-list",
        "parser": lambda h: parse_ccamlr(h, "Non-Contracting Party"),
    },
    "CCAMLR Contracting Party": {
        "url": "https://www.ccamlr.org/en/compliance/contracting-party-iuu-vessel-list",
        "parser": lambda h: parse_ccamlr(h, "Contracting Party"),
    },
}


def main() -> None:
    records, errors = [], []
    for name, src in SOURCES.items():
        try:
            recs = src["parser"](_get(src["url"]))
            print(f"  {name}: {len(recs)} vessels")
            records += recs
        except Exception as ex:                       # surface, do not silently skip a source
            errors.append(f"{name}: {ex}")
            print(f"  {name}: FAILED ({ex})")
    if not records:
        raise SystemExit(f"No IUU records fetched; sources may have changed. Errors: {errors}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"vessels": records, "sources": list(SOURCES), "errors": errors}, indent=1))
    n_imo = sum(1 for r in records if r["imo"])
    n_alias = sum(len(r["aliases"]) for r in records)
    print(f"{len(records)} IUU-listed vessels ({n_imo} with IMO, {n_alias} aliases) -> {OUT}")


if __name__ == "__main__":
    main()
