"""RFMO IUU blacklist cross-reference: a detection whose identity matches a vessel an RFMO has
listed for IUU fishing is no longer an 'unverifiable' lead, it is a KNOWN offender.

This is the adjudication signal the authorization layer could not give: authorization answers "is this
vessel licensed here?"; the IUU list answers "has an RFMO already condemned this hull?". They are
orthogonal, and an IUU listing is the strongest single flag SeaVigil can attach. Run this AFTER
``authorization.enrich_authorization`` so the GFW-resolved IMO and ship name are available to match on.

Matching is conservative and transparent: IMO or call sign is a strong identifier (drives the listing);
a name / previous-name hit is softer (these vessels rename to evade, so the aliases are valuable, but a
shared name is not proof) and is surfaced as "verify", not asserted. Reference data: data/iuu/
iuu_vessels.json from scripts/fetch_iuu_list.py (public RFMO lists).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IUU_PATH = ROOT / "data" / "iuu" / "iuu_vessels.json"


def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


class IUUList:
    """Indexed RFMO IUU vessel list with lookup by IMO, call sign, and (current + previous) name."""

    def __init__(self, records: list[dict]):
        self.records = records
        self.by_imo: dict[str, dict] = {}
        self.by_callsign: dict[str, dict] = {}
        self.by_name: dict[str, dict] = {}
        for r in records:
            imo = str(r.get("imo") or "").strip()
            if imo:
                self.by_imo.setdefault(imo, r)
            cs = (r.get("callsign") or "").replace(" ", "").upper()
            if cs:
                self.by_callsign.setdefault(cs, r)
            for nm in [r.get("name", ""), *r.get("aliases", [])]:
                k = _norm_name(nm)
                if len(k) >= 4:                       # skip 1-3 char names: too collision-prone
                    self.by_name.setdefault(k, r)

    @classmethod
    def load(cls, path: str | Path = IUU_PATH) -> "IUUList":
        p = Path(path)
        if not p.exists():
            return cls([])
        return cls(json.loads(p.read_text()).get("vessels", []))

    def match(self, imo: str = "", mmsi: str = "", name: str = "", callsign: str = ""):
        """Return (record, how) where how is 'imo' | 'callsign' | 'name', or (None, '')."""
        imo = str(imo or "").strip()
        if imo and imo in self.by_imo:
            return self.by_imo[imo], "imo"
        cs = (callsign or "").replace(" ", "").upper()
        if cs and cs in self.by_callsign:
            return self.by_callsign[cs], "callsign"
        nk = _norm_name(name)
        if len(nk) >= 4 and nk in self.by_name:
            return self.by_name[nk], "name"
        return None, ""


def enrich_iuu(dossiers: list[dict], iuu: IUUList | None = None) -> int:
    """Flag dossiers whose identity matches an RFMO IUU-listed vessel. In place; returns match count.

    Strong match (IMO / call sign) -> iuu_listed=True and severity forced to high. Name match -> a
    softer 'verify' flag, not auto-high. Either way the matched listing is recorded for the dossier.
    """
    iuu = iuu or IUUList.load()
    if not iuu.records:
        return 0
    matched = 0
    for d in dossiers:
        rec, how = iuu.match(imo=d.get("registry_imo") or d.get("imo") or "",
                             mmsi=str(d.get("vessel_id") or ""),
                             name=d.get("ship_name") or "",
                             callsign=d.get("callsign") or "")
        if not rec:
            continue
        matched += 1
        strong = how in ("imo", "callsign")
        d["iuu_listed"] = bool(strong)
        d["iuu_match"] = {
            "source": rec["source"], "list": rec.get("list", ""), "listed_name": rec["name"],
            "matched_on": how, "date_listed": rec.get("date_listed", ""),
            "aliases": rec.get("aliases", [])[:8],
        }
        verb = (f"identified ({how}) as '{rec['name']}', on the {rec['source']} RFMO IUU vessel list"
                if strong else
                f"possible name match to '{rec['name']}' on the {rec['source']} IUU list (verify identity)")
        expl = d.setdefault("explanation", {})
        if isinstance(expl.get("drivers"), list):
            expl["drivers"].insert(0, verb)
        else:
            expl["drivers"] = [verb]
        caveats = d.setdefault("caveats", [])
        if isinstance(caveats, list) and how == "name":
            caveats.insert(0, "IUU match is by name only; IUU vessels reuse names, so confirm the identity.")
        if strong:
            d["severity"] = "high"
            d["severity_reason"] = f"On the {rec['source']} RFMO IUU vessel list"
    return matched


def summary_label(d: dict) -> str:
    """One-line IUU sentence for a dossier, or '' if not matched."""
    m = d.get("iuu_match")
    if not m:
        return ""
    if d.get("iuu_listed"):
        return f"On the {m['source']} RFMO IUU vessel list (as '{m['listed_name']}')"
    return f"Possible match to {m['source']} IUU-listed '{m['listed_name']}' (by name; verify)"
