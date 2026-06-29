"""Fuse detections into vessel-centric CASES.

The detectors run in parallel and publish separate views: a SAR blip here, an optical hull there, an
AIS gap, an apparent-fishing track. To an operator those are three dots, not one decision. Fusion
collapses detections that are the same real-world vessel-event (same identity, or close in space and
time) into one case with a single confidence. The point is corroboration: a dark SAR detection in a
no-take reserve that lines up with a recent AIS gap is far stronger than either alone, and the fused
confidence reflects that. Independent sensors agreeing is the signal a single view cannot show.

Linking is conservative: a shared 9-digit MMSI or IMO links unconditionally; otherwise detections link
only if within ``radius_nm`` and ``window_h`` of each other. Connected detections form a case (union-
find / transitive closure). A case carries the union of evidence, the strongest member severity, and a
confidence raised when more than one independent sensor contributes.
"""

from __future__ import annotations

import hashlib
import math
from datetime import datetime

SEV_SCORE = {"high": 0.8, "medium": 0.5, "low": 0.3}


def _parse_t(s: str | None) -> float | None:
    try:
        return datetime.fromisoformat((s or "").replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return None


def _hav_nm(lo1, la1, lo2, la2) -> float:
    r1, r2 = math.radians(la1), math.radians(la2)
    dphi, dl = math.radians(la2 - la1), math.radians(lo2 - lo1)
    a = math.sin(dphi / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dl / 2) ** 2
    return 2 * 6371000 * math.asin(min(1, math.sqrt(a))) / 1852.0


def source_family(d: dict) -> str:
    """The sensor family a dossier came from (so 'independent sensors agreeing' is well-defined)."""
    t = (d.get("type") or "").lower()
    ds = (d.get("detection_source") or "").lower()
    if "optical" in t or "sentinel2" in ds:
        return "optical"
    if "sar" in t or "sentinel1" in ds:
        return "sar"
    if "viirs" in t or "vbd" in t:
        return "viirs"
    if "going_dark" in t or "encounter" in t or "gap" in t or "transship" in t:
        return "behavior"
    return "ais"


def _identity(d: dict):
    mmsi = str(d.get("vessel_id") or "")
    if mmsi.isdigit() and len(mmsi) == 9:
        return ("mmsi", mmsi)
    imo = str(d.get("registry_imo") or d.get("imo") or "")
    if imo.isdigit() and len(imo) >= 6:
        return ("imo", imo)
    return None


def _linked(a: dict, b: dict, radius_nm: float, window_h: float) -> bool:
    ia, ib = _identity(a), _identity(b)
    if ia and ia == ib:
        return True
    la, lo = a.get("centroid_lat"), a.get("centroid_lon")
    lb, lob = b.get("centroid_lat"), b.get("centroid_lon")
    if None in (la, lo, lb, lob):
        return False
    if _hav_nm(lo, la, lob, lb) > radius_nm:
        return False
    ta, tb = _parse_t(a.get("time_start_utc")), _parse_t(b.get("time_start_utc"))
    if ta is not None and tb is not None and abs(ta - tb) > window_h * 3600:
        return False
    return True


def fuse(dossiers: list[dict], radius_nm: float = 2.0, window_h: float = 6.0) -> list[dict]:
    """Cluster dossiers into vessel-centric cases (transitive closure of the link relation)."""
    n = len(dossiers)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _linked(dossiers[i], dossiers[j], radius_nm, window_h):
                parent[find(i)] = find(j)

    groups: dict[int, list[dict]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(dossiers[i])
    return [_build_case(m) for m in groups.values()]


def _build_case(members: list[dict]) -> dict:
    sources = sorted({source_family(d) for d in members})
    corroborated = len(sources) >= 2
    iuu = any(d.get("iuu_listed") for d in members)
    sev_label = max((d.get("severity") or "low" for d in members),
                    key=lambda s: SEV_SCORE.get((s or "").lower(), 0))
    conf = SEV_SCORE.get(sev_label.lower(), 0.3)
    if corroborated:
        conf = min(0.99, conf + 0.15 * (len(sources) - 1))   # independent agreement raises confidence
    if iuu:
        conf = max(conf, 0.95)                                # a known offender dominates
    rep = max(members, key=lambda d: (_identity(d) is not None,
                                      SEV_SCORE.get((d.get("severity") or "").lower(), 0)))
    lats = [d["centroid_lat"] for d in members if d.get("centroid_lat") is not None]
    lons = [d["centroid_lon"] for d in members if d.get("centroid_lon") is not None]
    ids = sorted(str(d.get("incident_id") or "") for d in members)
    case_id = "case_" + hashlib.sha1("|".join(ids).encode()).hexdigest()[:12]  # noqa: S324 (id, not security)
    ident = _identity(rep)
    return {
        "case_id": case_id,
        "n_members": len(members),
        "sources": sources,
        "n_sensors": len(sources),
        "corroborated": corroborated,
        "iuu_listed": iuu,
        "severity": sev_label,
        "confidence": round(conf, 2),
        "centroid_lat": round(sum(lats) / len(lats), 5) if lats else rep.get("centroid_lat"),
        "centroid_lon": round(sum(lons) / len(lons), 5) if lons else rep.get("centroid_lon"),
        "time_start_utc": rep.get("time_start_utc"),
        "identity_type": ident[0] if ident else "",
        "identity_value": ident[1] if ident else "",
        "ship_name": rep.get("ship_name") or "",
        "flag": rep.get("flag") or "",
        "eez_iso_sov": rep.get("eez_iso_sov") or "",
        "members": [{"incident_id": d.get("incident_id"), "source": source_family(d),
                     "type": d.get("type"), "severity": d.get("severity")} for d in members],
        "summary": _summary(sources, corroborated, iuu, sev_label),
    }


def _summary(sources: list[str], corroborated: bool, iuu: bool, sev: str) -> str:
    s = f"{sev} severity; seen by {', '.join(sources)}"
    if corroborated:
        s += f" ({len(sources)} independent sensors agree)"
    if iuu:
        s += "; matches an RFMO IUU-listed vessel"
    return s
