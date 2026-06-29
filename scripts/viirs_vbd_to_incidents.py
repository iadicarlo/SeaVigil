#!/usr/bin/env python3
"""Fold VIIRS Boat Detection (VBD) light-fishing-vessel detections into SeaVigil (the ?vbd view).

VBD finds vessels that fish with bright lights (squid jiggers, some purse seines) at night, the
distant-water fleet that terrestrial AIS misses offshore. Each detection is tagged with its EEZ
and reserve, cross-matched against the live AIS buffer (matched / dark / no-coverage, the same
honesty rule as the SAR engine), given an evidence hash, and written to web/data/vbd.

    uv run python scripts/viirs_vbd_to_incidents.py --detections data/positions/vbd_detections.csv
    uv run python scripts/viirs_vbd_to_incidents.py --detections vbd.csv --ais data/positions/ais_buffer.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # sibling helpers

from seavigil import evidence, site  # noqa: E402
from seavigil.dossier import write_dossiers  # noqa: E402
from seavigil.jurisdiction import enrich_jurisdiction  # noqa: E402
from seavigil.mpa import MPAIndex  # noqa: E402
from sar_detections_to_incidents import _match_ais  # noqa: E402  (reuse the 3-way matcher)

ROOT = Path(__file__).resolve().parent.parent
MPA_GEOJSON = ROOT / "data" / "mpa" / "wdpa_marine_showcase.geojson"
OUT_INC = ROOT / "results" / "vbd"
WEB_OUT = ROOT / "web" / "data" / "vbd"

_METHOD = "VIIRS Boat Detection (NOAA / Earth Observation Group), nighttime lights, folded by SeaVigil."
_CAVEATS = [
    "VIIRS detects vessels that use bright lights to attract catch (squid jiggers, some purse "
    "seines); it does not see vessels that fish without lights.",
    "Night and clear-sky only; cloud cover and bright moonlight reduce detections.",
    "A light is a position, not an identity; cross-matching with AIS tells which are dark.",
    "An inspection lead, not proof of illegal activity.",
]


def _dossier(seq, scene, t, lon, lat, radiance, in_mpa, mname, notake, iucn):
    drivers = [
        "VIIRS boat detection (nighttime lights)",
        f"radiance {radiance} nW/cm2/sr" if radiance else "radiance not reported",
        "light-fishing vessel (squid jigger or light purse seine)",
    ]
    short = scene[-8:] if scene else "vbd"
    return {
        "type": "viirs_boat",
        "incident_id": f"vbd__{short}_{seq:04d}",
        "mpa_name": mname or "VIIRS boat detection",
        "mpa_no_take": notake, "mpa_iucn_cat": iucn,
        "severity": "medium", "severity_reason": "",   # finalized below
        "vessel_id": "(VIIRS light detection -- no AIS identity)",
        "ship_name": "", "flag": "",
        "ship_type": "Fishing vessel (light-using)",
        "gear": "VIIRS nighttime lights (our fold)",
        "time_start_utc": t, "time_end_utc": t, "duration_hours": 0.0,
        "n_positions": 1, "n_fishing_positions": 1,
        "mean_fishing_proba": 1.0, "max_fishing_proba": 1.0,
        "centroid_lat": lat, "centroid_lon": lon,
        "matched_to_ais": None,
        "authorization_status": "unverifiable",
        "detection_source": "viirs_vbd",
        "vbd_radiance": radiance, "scene_id": scene,
        "_in_mpa": in_mpa, "_notake": notake, "_iucn": iucn,
        "explanation": {"method": _METHOD, "drivers": drivers},
        "caveats": _CAVEATS,
        "track": [],
    }


def _finalize_severity(d: dict) -> None:
    """A VBD detection is a light-fishing vessel by nature, so the base lead is medium. Dark (no
    AIS where reception proves it would have been seen) is high; a confirmed AIS match is low."""
    dark = d["matched_to_ais"] is False
    matched = d["matched_to_ais"] is True
    in_mpa = d.pop("_in_mpa"); d.pop("_notake"); d.pop("_iucn")
    if dark:
        sev, reason = "high", ("dark light-fishing vessel inside a protected area" if in_mpa
                               else "light-fishing vessel with no AIS broadcast (dark)")
    elif matched:
        sev, reason = "low", "VIIRS boat matched to an AIS broadcast (identified, broadcasting)"
    elif in_mpa:
        sev, reason = "medium", "light-fishing vessel inside a protected area (broadcasting unverified)"
    else:
        sev, reason = "medium", "light-fishing vessel detected by night lights (broadcasting unverified)"
    d["severity"], d["severity_reason"] = sev, reason
    if dark:
        d["vessel_id"] = "(dark -- no AIS identity)"
        d["explanation"]["drivers"].append("no AIS broadcast matched at acquisition (dark)")
    elif matched:
        d["explanation"]["drivers"].append("matched to an AIS broadcast at acquisition")


def build(detections_csv: str, ais_csv: str | None = None) -> list[dict]:
    mpa = MPAIndex.from_geojson(str(MPA_GEOJSON)) if MPA_GEOJSON.exists() else None
    if mpa is None:
        print(f"note: {MPA_GEOJSON.name} absent; grading by EEZ + activity, no reserve tagging.")
    dossiers = []
    with open(detections_csv) as f:
        for seq, r in enumerate(csv.DictReader(f)):
            try:
                lon, lat = float(r["lon"]), float(r["lat"])
            except (KeyError, ValueError):
                continue
            scene = r.get("scene_id", "")
            t = _epoch_to_iso(r.get("timestamp"))
            mi = int(mpa.assign([lon], [lat])[0]) if (mpa and len(mpa)) else -1
            in_mpa = mi >= 0
            m = mpa.mpas[mi] if in_mpa else None
            dossiers.append(_dossier(seq, scene, t, lon, lat, r.get("radiance", ""),
                                     in_mpa, (m.name if m else None),
                                     (m.no_take if m else None), (m.iucn_cat if m else None)))
    if ais_csv:
        matched, dark, nocov = _match_ais(dossiers, ais_csv)
        print(f"AIS matching: {matched} matched, {dark} dark (reception nearby), {nocov} no coverage")
    for d in dossiers:
        _finalize_severity(d)
    return dossiers


def _epoch_to_iso(ts) -> str:
    from datetime import datetime, timezone
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return ""


def main() -> None:
    ap = argparse.ArgumentParser(description="Fold VIIRS VBD detections into SeaVigil")
    ap.add_argument("--detections", required=True, help="VBD detections CSV from fetch_viirs_vbd.py")
    ap.add_argument("--ais", default=None, help="optional AIS buffer CSV for the dark / matched determination")
    a = ap.parse_args()

    dossiers = build(a.detections, a.ais)
    enrich_jurisdiction(dossiers)
    evidence.enrich_evidence(dossiers)
    OUT_INC.mkdir(parents=True, exist_ok=True)
    for p in OUT_INC.glob("*.md"):
        if p.name != "INDEX.md":
            p.unlink()
    write_dossiers(dossiers, OUT_INC)
    site.build_site(str(OUT_INC / "incidents.json"), out_dir=str(WEB_OUT))
    n_dark = sum(1 for d in dossiers if d["severity"] == "high")
    print(f"{len(dossiers)} VIIRS boats -> {WEB_OUT} (?vbd view) | {n_dark} graded high (dark)")


if __name__ == "__main__":
    main()
