"""Vessel authorization layer: turn a bare 'foreign' flag into a graded status.

A foreign vessel inside another state's EEZ is only an IUU lead, not proof: it may be
licensed. National EEZ licences are not public, but vessel registry identity and the
RFMO / regional authorization records ARE, via Global Fishing Watch's vessel-identity
dataset (itself built from those registries). For every incident that carries a vessel
identity (MMSI) we look up the GFW registry to get the authoritative flag and the
authorizations on record, then grade the incident against the incident date:

  authorized            - an authorization covering the incident date is on record
  authorization_lapsed  - an authorization exists but expired before the incident
  no_record             - foreign vessel, no authorization of any kind on record
  domestic              - registry flag matches the EEZ sovereign (its own EEZ)
  flag_unknown          - identity found but no flag, so foreign cannot be decided
  unverifiable          - no vessel identity at all (anonymized AIS labels, dark SAR)

This is consumed, not asserted. An empty authorization list means 'no public record',
NOT proof of illegality, and national EEZ licences are out of scope; the dossier says so.
GFW vessel identity: CC BY-NC. Authorization sources include FFA, WCPFC, IOTC, ICCAT,
IATTC, CCSBT, CCAMLR, NPFC and other RFMOs/agencies.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from seavigil.jurisdiction import is_foreign

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "authorizations.json"
_API = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"
_UA = "SeaVigil/1.0 (research; contact via github.com/iadicarlo/seavigil)"

STATUS_LABEL = {
    "authorized": "Authorization on record (current)",
    "authorization_lapsed": "Authorization lapsed before this date",
    "no_record": "No public authorization record (check coastal state)",
    "domestic": "Domestic flag (own EEZ)",
    "flag_unknown": "Flag unknown; authorization not checkable",
    "unverifiable": "No vessel identity; authorization not checkable",
}
# Statuses that strengthen an IUU lead (foreign vessel we could not clear).
ELEVATED = {"no_record", "authorization_lapsed"}


def _query(mmsi: str, token: str) -> dict | None:
    qs = urllib.parse.urlencode(
        {"query": mmsi, "datasets[0]": "public-global-vessel-identity:latest",
         "includes[0]": "AUTHORIZATIONS"}, safe=":")
    req = urllib.request.Request(f"{_API}?{qs}",
                                 headers={"Authorization": f"Bearer {token}", "User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed https host)
        data = json.load(r)
    entries = data.get("entries") or []
    return entries[0] if entries else None


def parse_entry(entry: dict | None) -> dict:
    """Flatten a GFW vessels-search entry to the fields the dossier needs."""
    if not entry:
        return {"found": False}
    reg = (entry.get("registryInfo") or [{}])[0]
    auths = []
    for a in entry.get("registryPublicAuthorizations") or []:
        for src in a.get("sourceCode") or []:
            auths.append({"source": src,
                          "date_from": (a.get("dateFrom") or "")[:10],
                          "date_to": (a.get("dateTo") or "")[:10]})
    geartypes = reg.get("geartypes") or []
    return {
        "found": True,
        "flag": reg.get("flag") or "",
        "shipname": reg.get("shipname") or "",
        "imo": reg.get("imo") or "",
        "geartype": (geartypes[0] if geartypes else "") or "",
        "authorizations": auths,
    }


def fetch_vessel(mmsi: str, token: str) -> dict:
    return parse_entry(_query(mmsi, token))


def build_cache(mmsis, token: str, out_path: str | Path = CACHE_PATH, pace: float = 0.4) -> dict:
    """Query GFW for every MMSI and write a committable cache (so later builds and CI
    need no token and rebuild offline). Network errors raise rather than being hidden."""
    out: dict[str, dict] = {}
    uniq = sorted({str(m) for m in mmsis if str(m).isdigit()})
    for i, mmsi in enumerate(uniq):
        out[mmsi] = fetch_vessel(mmsi, token)
        if i + 1 < len(uniq):
            time.sleep(pace)  # be gentle with the API
    Path(out_path).write_text(json.dumps(out, indent=0, sort_keys=True))
    return out


def load_cache(path: str | Path = CACHE_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"authorization cache not found: {p}. Build it with "
            "`uv run python scripts/fetch_authorizations.py`."
        )
    return json.loads(p.read_text())


def classify(vessel: dict | None, incident_iso: str | None, eez_iso_sov: str | None,
             flag: str | None) -> dict:
    """Grade one incident. ``vessel`` is a parsed cache record (or None / not found);
    ``flag`` is the best available vessel flag (registry flag if present, else the
    MMSI-derived one) used to decide foreign vs domestic."""
    if not vessel or not vessel.get("found"):
        return {"status": "unverifiable", "current": [], "lapsed": []}
    foreign = is_foreign(flag, eez_iso_sov)  # True / False / None
    day = (incident_iso or "")[:10]
    all_auths = vessel.get("authorizations") or []
    # An "IUU" entry in the registry is a LISTING, not a fishing authorization. Never let it count as
    # authorized (that would grade a known IUU vessel "authorized"); surface it as a flag instead.
    iuu = any((a.get("source") or "").upper() == "IUU" for a in all_auths)
    auths = [a for a in all_auths if (a.get("source") or "").upper() != "IUU"]
    current = sorted({a["source"] for a in auths
                      if a.get("date_from", "") <= day <= (a.get("date_to") or "9999-12-31")})
    lapsed = sorted({a["source"] for a in auths
                     if a.get("date_to") and a["date_to"] < day and a["source"] not in current})
    if foreign is False:
        status = "domestic"
    elif current:
        status = "authorized"
    elif lapsed:
        status = "authorization_lapsed"
    elif foreign is True:
        status = "no_record"
    else:
        status = "flag_unknown"
    return {"status": status, "current": current, "lapsed": lapsed, "iuu": iuu}


def enrich_authorization(dossiers: list[dict], cache: dict) -> list[dict]:
    """Add authorization_status (+ registry identity) to each dossier in place.

    Refines ``eez_foreign`` with the authoritative registry flag when GFW has one.
    Incidents without a 9-digit MMSI (anonymized AIS labels, dark SAR) are 'unverifiable'.
    """
    for d in dossiers:
        mmsi = str(d.get("vessel_id") or "")
        vessel = cache.get(mmsi) if (mmsi.isdigit() and len(mmsi) == 9) else None
        reg_flag = vessel.get("flag") if (vessel and vessel.get("found")) else None
        # Prefer the authoritative registry flag, else keep the MMSI-derived one.
        eff_flag = reg_flag or d.get("flag")
        res = classify(vessel, d.get("time_start_utc"), d.get("eez_iso_sov"), eff_flag)
        d["authorization_status"] = res["status"]
        d["authorization_authorities"] = res["current"] or res["lapsed"]
        d["registry_iuu_tag"] = bool(res.get("iuu"))   # GFW registry has it on an RFMO IUU list
        if vessel and vessel.get("found"):
            d["registry_flag"] = reg_flag or ""
            d["registry_imo"] = vessel.get("imo") or ""
            if vessel.get("shipname") and not d.get("ship_name"):
                d["ship_name"] = vessel["shipname"]
            if eff_flag:
                d["flag"] = eff_flag
                d["eez_foreign"] = is_foreign(eff_flag, d.get("eez_iso_sov"))
    return dossiers


def summary_label(d: dict) -> str:
    """One-line authorization sentence for a dossier."""
    st = d.get("authorization_status") or "unverifiable"
    auths = d.get("authorization_authorities") or []
    base = STATUS_LABEL.get(st, st)
    if st in ("authorized", "authorization_lapsed") and auths:
        return f"{base}: {', '.join(auths)}"
    return base
