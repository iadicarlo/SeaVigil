"""Near-real-time monitor: pull recent events from the Global Fishing Watch Events API,
keep the high-signal ones (foreign / unauthorized in an EEZ, or a no-take reserve
incursion), and run them through the same explain + jurisdiction + authorization +
evidence layer as the showcase. Output feeds the ?live view and the alerts feed.

GFW Events API gives near-real-time (about a 3-4 day latency) GLOBAL events with vessel
identity and the EEZ / MPA / RFMO regions each falls in. We consume gaps (AIS disabling
= going dark) and encounters (transshipment), the two behaviors we already model, now
live and worldwide rather than from a static research snapshot. Needs GFW_TOKEN.

This is consumed, not asserted: every record stays an inspection lead, not proof, and the
authorization grade carries the same "national licences are not public" caveat.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from seavigil.flags import emoji_for

API = "https://gateway.api.globalfishingwatch.org/v3/events"
_UA = "SeaVigil/1.0 (research; github.com/iadicarlo/seavigil)"
NM_KM = 1.852

# GFW event datasets we consume (gaps = going dark, encounters = transshipment).
DATASETS = {
    "ais_disabling": "public-global-gaps-events:latest",
    "encounter": "public-global-encounters-events:latest",
}
# Plausible AIS-disabling window (skip multi-month/year gaps that are decommissioning,
# and sub-half-day gaps that are routine reception loss), matching the showcase criteria.
GAP_MIN_H, GAP_MAX_H = 12.0, 24.0 * 21
ENC_MIN_H, ENC_MAX_H = 3.0, 48.0


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=40) as r:  # noqa: S310 (fixed https host)
        return json.load(r)


def fetch_recent(token: str, dataset: str, *, days: int = 14, max_events: int = 1000) -> list[dict]:
    """Most-recent events for a dataset over the last ``days`` (sorted newest-first)."""
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days)
    out: list[dict] = []
    offset, limit = 0, 500
    while len(out) < max_events:
        qs = urllib.parse.urlencode(
            {"datasets[0]": dataset, "start-date": str(start), "end-date": str(end),
             "limit": limit, "offset": offset, "sort": "-end"}, safe=":")
        data = _get(f"{API}?{qs}", token)
        entries = data.get("entries") or []
        out.extend(entries)
        offset += limit
        if not entries or offset >= (data.get("total") or 0):
            break
    return out[:max_events]


def _hours(start: str | None, end: str | None) -> float:
    try:
        a = datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = datetime.fromisoformat(end.replace("Z", "+00:00"))
        return (b - a).total_seconds() / 3600.0
    except (AttributeError, ValueError):
        return 0.0


_GAP_CAVEATS = [
    "AIS gaps can be reception loss, not always intentional disabling.",
    "The position is where AIS dropped; the path while dark is unknown.",
    "An inspection lead from GFW Events, not proof of illegal activity.",
]
_ENC_CAVEATS = [
    "Co-location can be legitimate (joint operations, safety, shelter).",
    "Apparent transshipment is inferred from proximity and low speed, not observed.",
    "An inspection lead from GFW Events, not proof of illegal activity.",
]


def _base(e: dict, kind: str, gear: str) -> dict:
    pos = e.get("position") or {}
    v = e.get("vessel") or {}
    return {
        "incident_id": f"live_{kind[:4]}_{e.get('id', '')[:14]}",
        "type": kind,
        "centroid_lon": pos.get("lon"),
        "centroid_lat": pos.get("lat"),
        "time_start_utc": e.get("start"),
        "time_end_utc": e.get("end"),
        "vessel_id": (v.get("ssvid") or "").strip(),
        "ship_name": (v.get("name") or "").strip(),
        "ship_type": (str(v.get("type") or "vessel")).title(),
        "flag": (v.get("flag") or "").strip(),
        "flag_emoji": emoji_for(v.get("flag")),
        "gear": gear,
        "track": [],  # events carry a single point, no track line to draw
        "n_positions": 0, "n_fishing_positions": 0,
        "mean_fishing_proba": None, "max_fishing_proba": None,
        "_rfmo": (e.get("regions") or {}).get("rfmo") or [],
        "_no_take": bool((e.get("regions") or {}).get("mpaNoTake")),
    }


def gap_to_dossier(e: dict) -> dict | None:
    gap_h = _hours(e.get("start"), e.get("end"))
    if not (GAP_MIN_H <= gap_h <= GAP_MAX_H):
        return None
    d = _base(e, "ais_disabling", "AIS gap")
    if d["centroid_lon"] is None:
        return None
    off_nm = float((e.get("distances") or {}).get("startDistanceFromShoreKm") or 0) / NM_KM
    d["mpa_name"] = "AIS disabling (going dark)"
    d["gap_hours"] = round(gap_h, 1)
    d["duration_hours"] = round(gap_h, 1)
    d["off_distance_nm"] = round(off_nm, 0)
    d["displacement_nm"] = None  # the event surfaces one position, not the reappearance
    d["explanation"] = {"method": "GFW Events gaps dataset (satellite AIS).", "drivers": [
        f"went dark {off_nm:.0f} nm offshore for {gap_h:.0f} h",
        "satellite-confirmed AIS gap (GFW Events)",
    ]}
    d["caveats"] = _GAP_CAVEATS
    return d


def encounter_to_dossier(e: dict) -> dict | None:
    dur_h = _hours(e.get("start"), e.get("end"))
    if not (ENC_MIN_H <= dur_h <= ENC_MAX_H):
        return None
    d = _base(e, "encounter", "Encounter")
    if d["centroid_lon"] is None:
        return None
    other = (e.get("encounter") or {}).get("vessel") or {}
    carrier = (other.get("ssvid") or "").strip()
    d["mpa_name"] = "At-sea encounter (transshipment)"
    d["duration_hours"] = round(dur_h, 1)
    d["carrier_mmsi"] = carrier
    d["explanation"] = {"method": "GFW Events encounters dataset (Miller et al. 2018).", "drivers": [
        f"two vessels within range for {dur_h:.0f} h",
        f"counterpart: {other.get('name') or carrier or 'another vessel'}",
        "two-vessel at-sea encounter (GFW Events)",
    ]}
    d["caveats"] = _ENC_CAVEATS
    return d


def spoofing_dossiers(buffer_path: str | Path) -> list[dict]:
    """Run the AIS-spoofing detector over the rolling positions buffer.

    Spoofing (impossible-speed jumps, or two vessels broadcasting one MMSI) needs a time
    series per vessel, which a single short stream cannot give; the buffer accumulates
    hours of aisstream fixes across runs so vessels build up enough track to flag.
    incident_id is keyed by MMSI so a persistent spoofer is one stable alert, not a new
    one each run. Returns [] if the buffer is absent or empty (the bootstrap case).
    """
    import pandas as pd  # noqa: PLC0415

    from seavigil import spoofing  # noqa: PLC0415

    p = Path(buffer_path)
    if not p.exists():
        return []
    df = pd.read_csv(p)
    if df.empty:
        return []
    out = spoofing.build_spoofing_dossiers(df)
    for d in out:
        d["incident_id"] = f"live_spoof_{d['vessel_id']}"
        d["flag_emoji"] = emoji_for(d.get("flag"))
        d["_no_take"] = False
        d["_rfmo"] = []
    return out


def build_dossiers(token: str, *, days: int = 14, max_per_type: int = 1000) -> list[dict]:
    """Fetch + map recent gaps and encounters into dossier dicts (unfiltered, untagged).

    GFW lists each encounter twice (once per vessel, same event id), so events are
    deduplicated by id; for an encounter the fishing vessel is kept as the subject.
    """
    out: list[dict] = []
    seen: dict[str, int] = {}  # incident_id -> index in out
    for kind, dataset in DATASETS.items():
        mapper = gap_to_dossier if kind == "ais_disabling" else encounter_to_dossier
        for e in fetch_recent(token, dataset, days=days, max_events=max_per_type):
            d = mapper(e)
            if not d:
                continue
            iid = d["incident_id"]  # encounter pairs share this (the encounter id prefix)
            is_fishing = ((e.get("vessel") or {}).get("type") or "").lower() == "fishing"
            if iid in seen:
                if kind == "encounter" and is_fishing:  # prefer the fishing-vessel side
                    out[seen[iid]] = d
                continue
            seen[iid] = len(out)
            out.append(d)
    return out
