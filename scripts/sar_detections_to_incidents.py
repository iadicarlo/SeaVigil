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
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seavigil import evidence, site  # noqa: E402
from seavigil.dossier import write_dossiers  # noqa: E402
from seavigil.jurisdiction import enrich_jurisdiction  # noqa: E402
from seavigil.landmask import drop_land  # noqa: E402
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

# SeaVigil runs two of its own detectors; both feed this converter and the 3-way AIS match. Each
# carries its own labels and writes its own view, so SAR and optical leads never get conflated.
SOURCES = {
    "sar": {
        "method": _METHOD, "caveats": _CAVEATS,
        "evidence": "Sentinel-1 SAR detection", "type": "dark_vessel_sar", "id_prefix": "s1sar",
        "gear": "Sentinel-1 SAR (our detection)", "detection_source": "seavigil_sentinel1",
        "no_id": "(SAR detection -- no AIS identity)", "label": "Sentinel-1 SAR detection",
        "out_inc": OUT_INC, "web_out": WEB_OUT, "results_rel": "results/sar/incidents.json",
    },
    "optical": {
        "method": "Sentinel-2 optical, Ai2 (Allen) trained detector (rslearn, Apache-2.0), run "
                  "on demand by SeaVigil.",
        "caveats": [
            "An optical detection sees a vessel's hull in clear daylight; cloud and sun glint are "
            "the limits, which is why we pair it with all-weather SAR.",
            "Length and the vessel type are estimates from the Ai2 model, not ground truth.",
            "Dark means no AIS broadcast matched at the acquisition time; without an AIS feed the "
            "broadcasting status is unverified, not assumed.",
            "An inspection lead, not proof of illegal activity.",
        ],
        "evidence": "Sentinel-2 optical detection", "type": "dark_vessel_optical", "id_prefix": "s2opt",
        "gear": "Sentinel-2 optical (Ai2 trained model)", "detection_source": "seavigil_sentinel2",
        "no_id": "(optical detection -- no AIS identity)", "label": "Sentinel-2 optical detection",
        "out_inc": ROOT / "results" / "s2", "web_out": ROOT / "web" / "data" / "s2",
        "results_rel": "results/s2/incidents.json",
    },
}


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


def _dossier(seq, scene, t, lon, lat, length, fishing, score, speed, head, in_mpa, mname, notake,
             iucn, src=None):
    src = src or SOURCES["sar"]
    is_fishing = fishing >= 0.5
    drivers = [
        f"{src['evidence']}, confidence {score:.2f}",
        (f"length {length:.0f} m" + (" (industrial scale)" if length >= 24 else " (small)")
         if length else "length not estimated"),
        f"classified {'fishing' if is_fishing else 'non-fishing'} vessel (p={fishing:.2f})",
    ]
    if head is not None:
        drivers.append(f"heading about {head} deg at {speed:.0f} kn")
    short = (scene[17:25] if len(scene) > 25 else "scene") or "scene"
    return {
        "type": src["type"],
        "incident_id": f"{src['id_prefix']}__{short}_{seq:04d}",
        "mpa_name": mname or src["label"],
        "mpa_no_take": notake, "mpa_iucn_cat": iucn,
        "severity": "medium", "severity_reason": "",   # finalized below
        "vessel_id": src["no_id"],
        "ship_name": "", "flag": "",
        "ship_type": "Fishing vessel" if is_fishing else "Vessel",
        "gear": src["gear"],
        "time_start_utc": t, "time_end_utc": t, "duration_hours": 0.0,
        "n_positions": 1, "n_fishing_positions": 1,
        "mean_fishing_proba": fishing, "max_fishing_proba": fishing,
        "centroid_lat": lat, "centroid_lon": lon,
        "length_m": length,
        "matched_to_ais": None,            # set by AIS matching (or stays unverified)
        "authorization_status": "unverifiable",
        "detection_source": src["detection_source"],
        "vessel_length_m": length, "vessel_speed_kn": round(speed, 1),
        "heading_deg": head, "sar_confidence": round(score, 3),
        "is_fishing_vessel_proba": round(fishing, 3), "scene_id": scene,
        "_in_mpa": in_mpa, "_notake": notake, "_iucn": iucn,
        "explanation": {"method": src["method"], "drivers": drivers},
        "caveats": src["caveats"],
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


def build(detections_csv: str, ais_csv: str | None = None, src: dict | None = None) -> list[dict]:
    src = src or SOURCES["sar"]
    # WDPA is not redistributed as raw GeoJSON (license), so the reserve set may be absent (e.g. on
    # a fresh CI checkout). Without it, detections are still graded by EEZ + dark + activity, just
    # without the "inside a reserve" tag.
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
            mi = int(mpa.assign([lon], [lat])[0]) if (mpa and len(mpa)) else -1
            in_mpa = mi >= 0
            m = mpa.mpas[mi] if in_mpa else None
            dossiers.append(_dossier(
                seq, scene, _scene_time(scene), lon, lat,
                _f(r, "vessel_length_m"), float(r.get("is_fishing_vessel") or 0),
                float(r.get("score") or 0), _f(r, "vessel_speed_k") or 0.0, _heading_deg(r),
                in_mpa, (m.name if m else None), (m.no_take if m else None),
                (m.iucn_cat if m else None), src))
    dossiers, n_land = drop_land(dossiers)
    if n_land:
        print(f"land mask: dropped {n_land} detection(s) on land (false positives)")
    if ais_csv:
        matched, dark, nocov = _match_ais(dossiers, ais_csv)
        print(f"AIS matching: {matched} matched a broadcast, {dark} dark (reception nearby, no "
              f"match), {nocov} no coverage (unverified)")
    for d in dossiers:
        _finalize_severity(d)
    return dossiers


def _accumulate(dossiers, keep_days, results_rel="results/sar/incidents.json"):
    """Merge this run's dossiers with the committed accumulated set, dedup by (scene, position),
    and keep only the last keep_days. This turns the view from a snapshot of the latest run into a
    rolling multi-hotspot map. The prior set is read from the last commit, so it works in CI."""
    try:
        prev_txt = subprocess.run(["git", "show", f"HEAD:{results_rel}"],
                                  cwd=ROOT, capture_output=True, text=True, timeout=30).stdout
        prev = json.loads(prev_txt) if prev_txt.strip() else []
    except Exception:
        prev = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)

    def key(d):
        return (d.get("scene_id"), round(d.get("centroid_lat") or 0, 4), round(d.get("centroid_lon") or 0, 4))

    def fresh(d):
        try:
            return datetime.fromisoformat((d.get("time_start_utc") or "").replace("Z", "+00:00")) >= cutoff
        except (ValueError, AttributeError):
            return True

    seen, out = set(), []
    for d in list(dossiers) + list(prev):   # this run first, so it wins on dedup
        k = key(d)
        if k in seen or not fresh(d):
            continue
        seen.add(k)
        out.append(d)
    print(f"accumulate: {len(dossiers)} new + {len(prev)} prior -> {len(out)} kept (last {keep_days}d)")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Fold our own vessel detections (SAR or optical) into SeaVigil")
    ap.add_argument("--detections", required=True, help="detections CSV (lon,lat,score,...)")
    ap.add_argument("--ais", default=None, help="optional AIS positions CSV (vessel_id,timestamp,lat,lon) to flag dark")
    ap.add_argument("--source", default="sar", choices=sorted(SOURCES),
                    help="detector that produced the CSV: sar (Sentinel-1) or optical (Sentinel-2 Ai2 model)")
    ap.add_argument("--accumulate-days", type=int, default=0,
                    help="merge with the committed view and keep the last N days (a rolling map); 0 = overwrite")
    a = ap.parse_args()
    src = SOURCES[a.source]
    out_inc, web_out = src["out_inc"], src["web_out"]

    dossiers = build(a.detections, a.ais, src)
    enrich_jurisdiction(dossiers)
    evidence.enrich_evidence(dossiers)
    if a.accumulate_days > 0:
        dossiers = _accumulate(dossiers, a.accumulate_days, src["results_rel"])
    out_inc.mkdir(parents=True, exist_ok=True)
    for p in out_inc.glob("*.md"):
        if p.name != "INDEX.md":
            p.unlink()
    write_dossiers(dossiers, out_inc)
    site.build_site(str(out_inc / "incidents.json"), out_dir=str(web_out))
    n_mpa = sum(1 for d in dossiers if d.get("mpa_name") != src["label"])
    n_fish = sum(1 for d in dossiers if (d.get("is_fishing_vessel_proba") or 0) >= 0.5)
    print(f"{len(dossiers)} {a.source} detections -> {web_out} | {n_mpa} inside a reserve, "
          f"{n_fish} classified fishing vessels")


if __name__ == "__main__":
    main()
