"""Build at-sea encounter (transshipment) dossiers from GFW's published events.

Transshipment, a fishing vessel offloading its catch to a refrigerated carrier at
sea, can launder illegally caught fish into the legal market by hiding where it was
caught. It mostly happens on the high seas to avoid port inspection, so SeaVigil
consumes Global Fishing Watch's published two-vessel encounter dataset (Miller et al.,
Frontiers in Marine Science 2018, DOI 10.3389/fmars.2018.00240; freely in their GitHub
repo, CC BY-NC) and adds the explanation + evidence layer, the same consume-not-recompute
pattern as the SAR dark fleet and the going-dark events. Only events inside a showcase
EEZ are kept; the Phoenix Islands EEZ (Western Central Pacific tuna grounds) is a real
hotspot. An encounter is apparent transshipment, an inspection lead, not proof.
"""

from __future__ import annotations

import csv
from pathlib import Path

from seavigil.flags import from_mmsi

CAVEATS = [
    "Apparent at-sea transshipment encounter, not proven and not necessarily illegal.",
    "Two AIS vessels held close and slow; some encounters are legitimate (bunkering, aid).",
    "Source: GFW two-vessel encounters (Miller et al. 2018); an inspection lead.",
    "GFW data is CC BY-NC; only derived in-EEZ dossiers are shown here, with attribution.",
]
_METHOD = "GFW two-vessel encounters (Miller et al. 2018, DOI 10.3389/fmars.2018.00240)"


def build_from_gfw_encounters(
    csv_path: str | Path,
    eez_index,
    *,
    max_events: int = 28,
    cap_per_eez: int = 15,
    min_duration_hr: float = 3.0,
    max_duration_hr: float = 48.0,
) -> list[dict]:
    """Return at-sea encounter dossiers (type ``encounter``) inside any coastal-state EEZ
    worldwide, selected round-robin across EEZs and by longest duration for diversity."""
    cand = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r["mean_latitude"])
                lon = float(r["mean_longitude"])
                dur = float(r["duration_hr"])
            except (ValueError, KeyError):
                continue
            if not (min_duration_hr <= dur <= max_duration_hr):
                continue  # plausible transshipment window (skip multi-week co-locations)
            r["_lat"], r["_lon"], r["_dur"] = lat, lon, dur
            cand.append((r, lon, lat))

    idx = eez_index.assign_many([c[1] for c in cand], [c[2] for c in cand])
    rows = []
    for (r, _lon, _lat), fi in zip(cand, idx):
        if fi < 0:
            continue
        r["_eez"] = eez_index.features[int(fi)]["properties"].get("name")
        rows.append(r)

    by_eez: dict = {}
    for r in sorted(rows, key=lambda r: -r["_dur"]):  # longest encounters first
        by_eez.setdefault(r["_eez"], []).append(r)

    picked: list[dict] = []
    buckets = list(by_eez.values())
    per_eez: dict = {}
    while len(picked) < max_events:
        progressed = False
        for b in buckets:
            if b and per_eez.get(b[0]["_eez"], 0) < cap_per_eez:
                r = b.pop(0)
                per_eez[r["_eez"]] = per_eez.get(r["_eez"], 0) + 1
                picked.append(r)
                progressed = True
            if len(picked) >= max_events:
                break
        if not progressed:  # every remaining bucket is empty or capped
            break

    dossiers = []
    for seq, r in enumerate(picked):
        fmmsi = r.get("fishing_vessel_mmsi") or ""
        cmmsi = r.get("transshipment_vessel_mmsi") or ""
        ff, _ = from_mmsi(fmmsi)
        cf, _ = from_mmsi(cmmsi)
        dist_m = float(r.get("median_distance_km") or 0) * 1000
        spd = float(r.get("median_speed_knots") or 0)
        dur = r["_dur"]
        drivers = [
            f"fishing vessel ({ff or 'flag ?'}) met a carrier ({cf or 'flag ?'}) for {dur:.0f} h",
            f"held {dist_m:.0f} m apart at {spd:.1f} kn (consistent with transshipment)",
            "two-vessel at-sea encounter (GFW / Miller et al. 2018)",
        ]
        dossiers.append({
            "type": "encounter",
            "incident_id": f"enc__{fmmsi}_{seq:04d}",
            "mpa_name": "At-sea encounter",
            "severity": "high" if dur >= 8 else "medium",
            "severity_reason": "apparent at-sea transshipment (catch-laundering pathway)",
            "vessel_id": str(fmmsi),
            "ship_name": "",
            "flag": ff,
            "ship_type": "Fishing",
            "gear": "Encounter",
            "carrier_mmsi": str(cmmsi),
            "time_start_utc": (r.get("start_time") or "")[:19].replace(" ", "T") + "Z",
            "time_end_utc": (r.get("end_time") or "")[:19].replace(" ", "T") + "Z",
            "duration_hours": round(dur, 1),
            "n_positions": 0, "n_fishing_positions": 0,
            "mean_fishing_proba": None, "max_fishing_proba": None,
            "centroid_lat": r["_lat"], "centroid_lon": r["_lon"],
            "explanation": {"method": _METHOD, "drivers": drivers},
            "caveats": CAVEATS,
        })
    return dossiers
