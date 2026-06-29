#!/usr/bin/env python3
"""Fold our own Sentinel-1 SAR vessel detections into SeaVigil.

Input is the detections CSV produced by notebooks/sentinel1_vessel_detection.ipynb (the
open Allen Institute detector). For each detection we tag its EEZ and reserve, attach the
SAR vessel attributes (length, heading, speed, fishing-vessel class), optionally flag the
ones with no AIS broadcast as DARK, add an evidence hash, and write a ?sar view
(web/data/sar). The detections reuse the existing dark_vessel_sar marker and dossier.

    uv run python scripts/sar_detections_to_incidents.py --detections seavigil_detections.csv
    uv run python scripts/sar_detections_to_incidents.py --detections d.csv --ais positions.csv

This is our own detection (we chose the scene and ran the model), unlike the consumed GFW
SAR. A SAR blip carries no identity, so each record is an inspection lead, not proof.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seavigil import evidence, site  # noqa: E402
from seavigil.dossier import write_dossiers  # noqa: E402
from seavigil.jurisdiction import enrich_jurisdiction  # noqa: E402
from seavigil.mpa import MPAIndex, grade_severity  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MPA_GEOJSON = ROOT / "data" / "mpa" / "wdpa_marine_showcase.geojson"
OUT_INC = ROOT / "results" / "sar"
WEB_OUT = ROOT / "web" / "data" / "sar"
NM_M = 1852.0

_METHOD = "Sentinel-1 SAR, Allen Institute open detector (Apache-2.0), run on demand by SeaVigil."
_CAVEATS = [
    "A SAR detection is a radar blip: it has a position and a size, not an identity.",
    "Length, heading and the fishing-vessel class are model estimates, not ground truth.",
    "Dark means no AIS broadcast matched at the acquisition time; without an AIS feed the "
    "broadcasting status is unverified, not assumed.",
    "An inspection lead, not proof of illegal activity.",
]


def _scene_time(scene_id: str) -> str:
    m = re.search(r"(\d{8})T(\d{6})", scene_id or "")
    if not m:
        return ""
    d, t = m.groups()
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}T{t[:2]}:{t[2:4]}:{t[4:6]}Z"


def _heading_deg(row: dict) -> int | None:
    b = [float(row.get(f"heading_bucket_{i}") or 0) for i in range(16)]
    if not any(b):
        return None
    return round(max(range(16), key=lambda i: b[i]) * 22.5)


def _f(row: dict, key: str) -> float | None:
    try:
        v = float(row.get(key) or 0)
        return v or None
    except (TypeError, ValueError):
        return None


def _haversine_nm(lon1, lat1, lon2, lat2) -> float:
    r1, r2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dlmb / 2) ** 2
    return (6371000.0 * 2 * math.asin(math.sqrt(a))) / NM_M


def _dossier(seq, scene, t, lon, lat, length, fishing, score, speed, head, in_mpa, mname, notake, iucn):
    is_fishing = fishing >= 0.5
    drivers = [
        f"Sentinel-1 SAR detection, confidence {score:.2f}",
        (f"length {length:.0f} m" + (" (industrial scale)" if length >= 24 else " (small)")
         if length else "length not estimated"),
        f"classified {'fishing' if is_fishing else 'non-fishing'} vessel (p={fishing:.2f})",
    ]
    if head is not None:
        drivers.append(f"heading about {head} deg at {speed:.0f} kn")
    short = (scene[17:25] if len(scene) > 25 else "scene") or "scene"
    return {
        "type": "dark_vessel_sar",
        "incident_id": f"s1sar__{short}_{seq:04d}",
        "mpa_name": mname or "Sentinel-1 SAR detection",
        "mpa_no_take": notake, "mpa_iucn_cat": iucn,
        "severity": "medium", "severity_reason": "",   # finalized below
        "vessel_id": "(SAR detection -- no AIS identity)",
        "ship_name": "", "flag": "",
        "ship_type": "Fishing vessel" if is_fishing else "Vessel",
        "gear": "Sentinel-1 SAR (our detection)",
        "time_start_utc": t, "time_end_utc": t, "duration_hours": 0.0,
        "n_positions": 1, "n_fishing_positions": 1,
        "mean_fishing_proba": fishing, "max_fishing_proba": fishing,
        "centroid_lat": lat, "centroid_lon": lon,
        "length_m": length,
        "matched_to_ais": None,            # set by AIS matching (or stays unverified)
        "authorization_status": "unverifiable",
        "detection_source": "seavigil_sentinel1",
        "vessel_length_m": length, "vessel_speed_kn": round(speed, 1),
        "heading_deg": head, "sar_confidence": round(score, 3),
        "is_fishing_vessel_proba": round(fishing, 3), "scene_id": scene,
        "_in_mpa": in_mpa, "_notake": notake, "_iucn": iucn,
        "explanation": {"method": _METHOD, "drivers": drivers},
        "caveats": _CAVEATS,
        "track": [],
    }


# SAR-estimated speed below this reads as moored / at anchor, not as fishing. SAR speed is a
# noisy azimuth-offset estimate, so this only separates clearly-stationary from clearly-underway.
UNDERWAY_KN = 1.0


def _finalize_severity(d: dict) -> None:
    """Grade a SAR detection. The strongest IUU signal is *dark*: a vessel emitting no AIS. That
    needs an AIS feed to confirm, so when no feed matched at acquisition the broadcasting status is
    unverified and we must not claim "high" (we cannot tell a dark intruder from the broadcasting
    local fleet). In that case we grade by activity and location instead, and a near-stationary
    vessel (likely at anchor) is a weak lead, not apparent fishing.
    """
    dark = d["matched_to_ais"] is False        # confirmed: no AIS broadcast matched (needs a feed)
    matched = d["matched_to_ais"] is True       # confirmed: broadcasting at acquisition
    in_mpa, notake, iucn = d.pop("_in_mpa"), d.pop("_notake"), d.pop("_iucn")
    is_fishing = (d.get("is_fishing_vessel_proba") or 0) >= 0.5
    underway = (d.get("vessel_speed_kn") or 0) >= UNDERWAY_KN
    if dark:
        if in_mpa and is_fishing:
            sev, reason = "high", "dark fishing-type vessel inside a protected area"
        elif in_mpa:
            sev, reason = "high", "dark vessel inside a protected area"
        else:
            sev, reason = "high", "dark vessel (no AIS broadcast) detected by SAR"
    elif matched:
        sev, reason = "low", "SAR detection matched to an AIS broadcast (identified, broadcasting)"
    elif in_mpa and is_fishing and underway:
        sev, reason = "medium", "fishing-type vessel underway in a protected area (broadcasting unverified)"
    elif in_mpa and not underway:
        sev, reason = "low", "stationary vessel inside a protected area (likely at anchor; broadcasting unverified)"
    elif in_mpa:
        sev, reason = grade_severity(iucn, notake)  # non-fishing underway in a reserve: by category
    elif is_fishing and underway:
        sev, reason = "medium", "fishing-type vessel underway (broadcasting unverified)"
    else:
        sev, reason = "low", "SAR-detected vessel (broadcasting unverified)"
    d["severity"], d["severity_reason"] = sev, reason
    if dark:
        d["vessel_id"] = "(dark -- no AIS identity)"
        d["gear"] = "Sentinel-1 SAR (dark)"
        d["explanation"]["drivers"].append("no AIS broadcast matched at acquisition (dark)")
    elif matched:
        d["explanation"]["drivers"].append("matched to an AIS broadcast at acquisition")
    elif not underway:
        d["explanation"]["drivers"].append("near-stationary at acquisition (likely at anchor)")


def _match_ais(dossiers, ais_csv, radius_nm=2.0, coverage_nm=50.0, window_min=30):
    """Cross-match each SAR detection against the AIS buffer, three ways:
      matched (True)    : an AIS broadcast within radius_nm and +/- window_min -> identified, broadcasting.
      dark (False)      : no match, BUT AIS reception existed within coverage_nm at that time, so a
                          broadcasting vessel would have been received -> genuinely not broadcasting.
      no coverage (None): no AIS at all nearby in the window -> a reception gap, status unverified.
    The middle case is the only honest "dark" flag: we call a vessel dark only when we can show we
    would have received it if it were broadcasting. Offshore, where aisstream is sparse, many
    detections fall to None rather than False, which is the truthful answer.
    """
    pts = []
    with open(ais_csv) as f:
        for a in csv.DictReader(f):
            try:
                pts.append((float(a["timestamp"]), float(a["lat"]), float(a["lon"])))
            except (KeyError, ValueError):
                continue
    matched = dark = nocov = 0
    for d in dossiers:
        try:
            te = datetime.fromisoformat(d["time_start_utc"].replace("Z", "+00:00")).timestamp()
        except ValueError:
            d["matched_to_ais"] = None
            nocov += 1
            continue
        near = [(la, lo) for ts, la, lo in pts if abs(ts - te) <= window_min * 60]
        if any(_haversine_nm(d["centroid_lon"], d["centroid_lat"], lo, la) <= radius_nm
               for la, lo in near):
            d["matched_to_ais"] = True
            matched += 1
        elif any(_haversine_nm(d["centroid_lon"], d["centroid_lat"], lo, la) <= coverage_nm
                 for la, lo in near):
            d["matched_to_ais"] = False   # reception nearby but no match -> dark
            dark += 1
        else:
            d["matched_to_ais"] = None     # no reception nearby -> coverage gap, unverified
            nocov += 1
    return matched, dark, nocov


def build(detections_csv: str, ais_csv: str | None = None) -> list[dict]:
    mpa = MPAIndex.from_geojson(str(MPA_GEOJSON))
    dossiers = []
    with open(detections_csv) as f:
        for seq, r in enumerate(csv.DictReader(f)):
            try:
                lon, lat = float(r["lon"]), float(r["lat"])
            except (KeyError, ValueError):
                continue
            scene = r.get("scene_id", "")
            mi = int(mpa.assign([lon], [lat])[0]) if len(mpa) else -1
            in_mpa = mi >= 0
            m = mpa.mpas[mi] if in_mpa else None
            dossiers.append(_dossier(
                seq, scene, _scene_time(scene), lon, lat,
                _f(r, "vessel_length_m"), float(r.get("is_fishing_vessel") or 0),
                float(r.get("score") or 0), _f(r, "vessel_speed_k") or 0.0, _heading_deg(r),
                in_mpa, (m.name if m else None), (m.no_take if m else None), (m.iucn_cat if m else None)))
    if ais_csv:
        matched, dark, nocov = _match_ais(dossiers, ais_csv)
        print(f"AIS matching: {matched} matched a broadcast, {dark} dark (reception nearby, no "
              f"match), {nocov} no coverage (unverified)")
    for d in dossiers:
        _finalize_severity(d)
    return dossiers


def main() -> None:
    ap = argparse.ArgumentParser(description="Fold Sentinel-1 SAR detections into SeaVigil")
    ap.add_argument("--detections", required=True, help="detections CSV from the Colab notebook")
    ap.add_argument("--ais", default=None, help="optional AIS positions CSV (vessel_id,timestamp,lat,lon) to flag dark")
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
    n_mpa = sum(1 for d in dossiers if d.get("mpa_name") != "Sentinel-1 SAR detection")
    n_fish = sum(1 for d in dossiers if (d.get("is_fishing_vessel_proba") or 0) >= 0.5)
    print(f"{len(dossiers)} SAR detections -> {WEB_OUT} (?sar view) | {n_mpa} inside a reserve, "
          f"{n_fish} classified fishing vessels")


if __name__ == "__main__":
    main()
