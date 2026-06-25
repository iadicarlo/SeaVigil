#!/usr/bin/env python3
"""Stream near-real-time AIS from aisstream.io into the seavigil `--positions` schema.

aisstream.io is a free global live AIS WebSocket (needs a free API key in AISSTREAM_KEY).
This subscribes to a bounding box, collects PositionReports for a while, and writes a CSV
the model can score (distance_from_shore/port are computed on load by seavigil.enrich).

Because a static site cannot hold a live socket, "near-real-time" means a scheduled job
runs this every N minutes for the monitored MPAs, then re-scores and republishes.

Setup:  export AISSTREAM_KEY=...   (kept in .env, gitignored)
Run:
  uv run --with websockets python scripts/fetch_live_ais.py \
      --bbox -24.5,142.5,-10.5,154.0 --seconds 60 --out data/positions/live_ais_real.csv
  uv run python -m seavigil.alert --positions data/positions/live_ais_real.csv \
      --mpa data/mpa/wdpa_marine_sample.geojson
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

# Make `seavigil` importable when run as a standalone script (package is not installed).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ENDPOINT = "wss://stream.aisstream.io/v0/stream"
FIELDS = ["vessel_id", "timestamp", "lat", "lon", "speed", "course", "gear",
          "ship_name", "flag", "destination", "ship_type"]


def _epoch(s) -> int | None:
    if not s:
        return None
    try:  # aisstream time_utc looks like "2026-06-25 16:31:52.607 +0000 UTC"
        return int(dt.datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S")
                   .replace(tzinfo=dt.timezone.utc).timestamp())
    except (ValueError, TypeError):
        return None


_TYPE = {30: "Fishing", 31: "Tug", 32: "Tug", 36: "Sailing", 37: "Pleasure craft",
         50: "Pilot", 51: "SAR", 52: "Tug", 53: "Port tender", 55: "Law enforcement"}


def _ship_type_label(code) -> str:
    try:
        c = int(code)
    except (TypeError, ValueError):
        return ""
    if c in _TYPE:
        return _TYPE[c]
    if 40 <= c <= 49:
        return "High-speed craft"
    if 60 <= c <= 69:
        return "Passenger"
    if 70 <= c <= 79:
        return "Cargo"
    if 80 <= c <= 89:
        return "Tanker"
    return "Other"


async def _stream(key: str, bbox, seconds: int, maxn: int) -> list[dict]:
    import websockets

    from seavigil import flags

    sub = {
        "APIKey": key,
        "BoundingBoxes": [[[bbox[0], bbox[1]], [bbox[2], bbox[3]]]],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
    }
    statics: dict = {}   # MMSI -> {ship_name, destination, ship_type}
    rows: list[dict] = []
    async with websockets.connect(ENDPOINT, ping_interval=None, max_size=None) as ws:
        await ws.send(json.dumps(sub))
        try:
            async with asyncio.timeout(seconds):
                async for raw in ws:
                    m = json.loads(raw)
                    mt = m.get("MessageType")
                    meta = m.get("MetaData", {})
                    mmsi = meta.get("MMSI")
                    if mt == "ShipStaticData":
                        sd = m["Message"]["ShipStaticData"]
                        statics[mmsi] = {
                            "ship_name": (sd.get("Name") or meta.get("ShipName") or "").strip(),
                            "destination": (sd.get("Destination") or "").strip(),
                            "ship_type": _ship_type_label(sd.get("Type")),
                        }
                        continue
                    if mt != "PositionReport":
                        continue
                    pr = m["Message"]["PositionReport"]
                    lat, lon = pr.get("Latitude"), pr.get("Longitude")
                    ts = _epoch(meta.get("time_utc"))
                    if lat is None or lon is None or ts is None:
                        continue
                    st = statics.get(mmsi, {})
                    iso2, _ = flags.from_mmsi(mmsi)
                    rows.append({
                        "vessel_id": str(mmsi or ""),
                        "timestamp": ts, "lat": lat, "lon": lon,
                        "speed": pr.get("Sog", 0.0), "course": pr.get("Cog", 0.0),
                        "gear": "unknown",
                        "ship_name": st.get("ship_name") or (meta.get("ShipName") or "").strip(),
                        "flag": iso2,
                        "destination": st.get("destination", ""),
                        "ship_type": st.get("ship_type", ""),
                    })
                    if len(rows) >= maxn:
                        break
        except (asyncio.TimeoutError, TimeoutError):
            pass

    # Back-fill identity for positions seen before their static message arrived.
    for r in rows:
        st = statics.get(int(r["vessel_id"]) if r["vessel_id"].isdigit() else r["vessel_id"])
        if st:
            r["ship_name"] = r["ship_name"] or st["ship_name"]
            r["destination"] = r["destination"] or st["destination"]
            r["ship_type"] = r["ship_type"] or st["ship_type"]
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Stream live AIS (aisstream.io) into --positions CSV")
    ap.add_argument("--bbox", required=True, help="lat_min,lon_min,lat_max,lon_max")
    ap.add_argument("--seconds", type=int, default=60)
    ap.add_argument("--max", type=int, default=20000)
    ap.add_argument("--out", default="data/positions/live_ais_real.csv")
    args = ap.parse_args()

    key = os.environ.get("AISSTREAM_KEY")
    if not key:
        raise SystemExit("AISSTREAM_KEY not set (free key at aisstream.io; keep it in .env)")
    bbox = [float(x) for x in args.bbox.split(",")]

    rows = asyncio.run(_stream(key, bbox, args.seconds, args.max))
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    vessels = len({r["vessel_id"] for r in rows})
    print(f"wrote {len(rows)} live AIS positions ({vessels} vessels) -> {args.out}")


if __name__ == "__main__":
    main()
