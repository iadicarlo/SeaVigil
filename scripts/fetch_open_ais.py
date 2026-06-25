#!/usr/bin/env python3
"""Pull a sample of OPEN, real AIS positions into the seavigil `--positions` schema.

Source: HuggingFace `eyesofworld/AIS_Dataset` (US Gulf of Mexico, from NOAA Marine
Cadastre; Apache-2.0), via the public datasets-server `/rows` API — no account, no
download of the full 7 GB. Lets you run the model OUT-OF-SAMPLE on a real recent feed;
distance_from_shore / distance_from_port are computed on load (seavigil.enrich).

Usage:
    python scripts/fetch_open_ais.py --n 3000 --out data/positions/gulf_ais_real.csv
    uv run python -m seavigil.alert --positions data/positions/gulf_ais_real.csv --mpa <gulf_mpa.geojson>
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import urllib.request

DATASET = "eyesofworld/AIS_Dataset"
ROWS = (f"https://datasets-server.huggingface.co/rows"
        f"?dataset={DATASET}&config=default&split=train")
FIRST = (f"https://datasets-server.huggingface.co/first-rows"
         f"?dataset={DATASET}&config=default&split=train")
FIELDS = ["vessel_id", "timestamp", "lat", "lon", "speed", "course", "gear"]
# NOTE: this dataset isn't indexed for random access (/rows -> 501), so the open API
# caps us at ~100 rows via /first-rows. For a fuller feed, download NOAA Marine
# Cadastre daily AIS (coast.noaa.gov/htdata/CMSP/AISDataHandler/) and map the same
# columns -- everything downstream (enrich + score) is identical.


def _epoch(s: str) -> int | None:
    try:
        return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
                   .replace(tzinfo=dt.timezone.utc).timestamp())
    except (ValueError, TypeError):
        return None


def _get(url: str) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "seavigil/0.1"})
    with urllib.request.urlopen(req, timeout=90) as resp:  # noqa: S310 (trusted host)
        return json.load(resp).get("rows", [])


def fetch(n: int, out: str) -> int:
    raw = []
    try:  # random-access pagination if the dataset supports it
        offset = 0
        while len(raw) < n:
            batch = _get(f"{ROWS}&offset={offset}&length=100")
            if not batch:
                break
            raw.extend(batch)
            offset += 100
    except urllib.error.HTTPError:
        raw = _get(FIRST)  # fall back to the first ~100 rows

    rows = []
    for item in raw[:n]:
        x = item["row"]
        ts = _epoch(x.get("BaseDateTime"))
        if ts is None or x.get("LAT") is None or x.get("SOG") is None:
            continue
        rows.append({
            "vessel_id": f"{x['MMSI']}_{x.get('TrackID', 0)}",
            "timestamp": ts, "lat": x["LAT"], "lon": x["LON"],
            "speed": x["SOG"], "course": x.get("COG", 0.0), "gear": "unknown",
        })
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} real AIS rows -> {out}")
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch open AIS into the --positions schema")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--out", default="data/positions/gulf_ais_real.csv")
    args = ap.parse_args()
    fetch(args.n, args.out)


if __name__ == "__main__":
    main()
