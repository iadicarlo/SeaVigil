#!/usr/bin/env python3
"""Fuse the separate detection views into vessel-centric cases (the operational unit).

Each detector publishes its own view (apparent-fishing AIS, SAR, optical, behaviors). This gathers them
all and runs seavigil.fusion to collapse detections of the same vessel-event into one case with a single
confidence, so an operator sees one decision, not parallel dots. A case corroborated by more than one
independent sensor (a dark SAR blip plus an AIS gap at the same place and time) is the strongest lead
the system can produce. Writes results/cases/cases.json and a web/data/cases view.

    uv run python scripts/build_cases.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from seavigil.fusion import fuse  # noqa: E402

VIEWS = ["incidents", "live", "sar", "behaviors", "s2", "vbd"]
OUT_JSON = ROOT / "results" / "cases" / "cases.json"
WEB = ROOT / "web" / "data" / "cases"
PROPS = ("case_id", "severity", "confidence", "corroborated", "n_sensors", "sources",
         "iuu_listed", "ship_name", "flag", "eez_iso_sov", "summary", "time_start_utc")


def load_dossiers() -> list[dict]:
    dossiers = []
    for v in VIEWS:
        p = ROOT / "results" / v / "incidents.json"
        if not p.exists():
            continue
        recs = json.loads(p.read_text())
        for d in recs:
            d["_view"] = v
        dossiers += recs
        print(f"  {v}: {len(recs)} detections")
    return dossiers


def main() -> None:
    dossiers = load_dossiers()
    if not dossiers:
        raise SystemExit("No detection views found under results/*/incidents.json")
    cases = fuse(dossiers)
    corroborated = [c for c in cases if c["corroborated"]]

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(cases, indent=1))

    WEB.mkdir(parents=True, exist_ok=True)
    feats = [{"type": "Feature",
              "geometry": {"type": "Point", "coordinates": [c["centroid_lon"], c["centroid_lat"]]},
              "properties": {k: c[k] for k in PROPS}}
             for c in cases if c.get("centroid_lat") is not None and c.get("centroid_lon") is not None]
    (WEB / "cases.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    summary = {
        "n_detections": len(dossiers),
        "n_cases": len(cases),
        "n_corroborated_multi_sensor": len(corroborated),
        "by_sensor_count": {str(k): v for k, v in sorted(Counter(c["n_sensors"] for c in cases).items())},
        "generated_from": [v for v in VIEWS if (ROOT / "results" / v / "incidents.json").exists()],
    }
    (WEB / "summary.json").write_text(json.dumps(summary, indent=1))
    print(f"\n{len(dossiers)} detections -> {len(cases)} cases "
          f"({len(corroborated)} corroborated by 2+ independent sensors)")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
