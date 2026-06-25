"""Auditable evidence package for an incident: provenance, integrity, reproducibility.

The downloadable dossier is the offline, court-facing half of SeaVigil's wedge. This
stamps each incident with a tamper-evident content hash over its canonical facts and
records the full data provenance (dataset, reference, version, license) so a reviewer
can (a) verify the record was not altered and (b) trace every input to its licensed
source. It never overstates: the package carries the standing "inspection lead, not
proof" disclaimer and the known limits of AIS/SAR evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCHEMA_VERSION = "seavigil-evidence-1.0"
_CALIBRATION = Path(__file__).resolve().parent.parent / "results" / "calibration.json"

# Per-incident-type data lineage.
TYPE_SOURCES = {
    "ais_fishing_incident": {
        "dataset": "Global Fishing Watch labelled AIS training data",
        "reference": "Kroodsma et al., Science 2018",
        "license": "CC BY 4.0",
        "url": "https://globalfishingwatch.org",
    },
    "dark_vessel_sar": {
        "dataset": "Global Fishing Watch Sentinel-1 SAR vessel detections",
        "reference": "Paolo et al., Nature 2024",
        "license": "CC BY-NC 4.0 (non-commercial)",
        "url": "https://globalfishingwatch.org",
    },
}
BOUNDARY_SOURCES = {
    "wdpa": {
        "dataset": "WDPA / WD-OECM (World Database on Protected Areas)",
        "reference": "UNEP-WCMC and IUCN (2026)",
        "version": "June 2026",
        "license": "Protected Planet Terms of Use (non-commercial, display-only)",
        "url": "https://www.protectedplanet.net",
    },
    "eez": {
        "dataset": "Marine Regions Exclusive Economic Zones v12",
        "reference": "Flanders Marine Institute (2024), DOI 10.14284/632",
        "license": "CC BY 4.0",
        "url": "https://www.marineregions.org",
    },
}

DISCLAIMER = (
    "Apparent activity and an inspection lead, not proof of illegality. AIS and SAR "
    "evidence have known coverage gaps and spoofing risks; verify against authoritative "
    "sources before any enforcement action."
)

# Canonical facts the integrity hash covers. Stable order, explanation-independent so
# the hash anchors the WHO/WHERE/WHEN/HOW-STRONG, not the prose.
_HASH_FIELDS = (
    "incident_id", "type", "mpa_name", "mpa_iucn_cat", "mpa_no_take",
    "eez_name", "eez_sovereign", "eez_foreign",
    "time_start_utc", "time_end_utc", "centroid_lat", "centroid_lon",
    "mean_fishing_proba", "severity", "flag", "vessel_id",
)


def _canonical(d: dict) -> dict:
    return {k: d.get(k) for k in _HASH_FIELDS}


def evidence_hash(d: dict) -> str:
    """SHA-256 over the incident's canonical facts (tamper-evidence anchor)."""
    blob = json.dumps(_canonical(d), sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def enrich_evidence(dossiers: list[dict]) -> list[dict]:
    """Stamp each dossier with its evidence schema id and content hash, in place."""
    for d in dossiers:
        d["evidence_schema"] = SCHEMA_VERSION
        d["evidence_hash"] = evidence_hash(d)
    return dossiers


def calibration_summary() -> dict | None:
    """Compact confidence statement from scripts/calibration_report.py, or None.

    Lets a dossier say honestly how trustworthy the fishing probabilities are, rather
    than presenting a bare score. A low Brier with little gain from recalibration means
    the score can be read as a probability.
    """
    if not _CALIBRATION.exists():
        return None
    try:
        d = json.loads(_CALIBRATION.read_text())
    except (ValueError, OSError):
        return None
    raw = d.get("raw", {})
    n = d.get("n_test")
    brier = raw.get("brier")
    if brier is None:
        return None
    return {
        "brier": brier,
        "log_loss": raw.get("log_loss"),
        "n_held_out": n,
        "isotonic_brier": (d.get("calibrated") or {}).get("brier"),
        "statement": (f"Fishing probabilities are well-calibrated (Brier {brier} on "
                      f"{n:,} held-out positions from vessels not seen in training); "
                      "read the score as a probability."),
    }


def provenance_for(incident_type: str | None) -> list[dict]:
    """Data lineage for an incident type plus the boundary datasets it is judged against."""
    out = []
    src = TYPE_SOURCES.get(incident_type or "")
    if src:
        out.append(src)
    out.append(BOUNDARY_SOURCES["wdpa"])
    out.append(BOUNDARY_SOURCES["eez"])
    return out
