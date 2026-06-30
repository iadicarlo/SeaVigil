#!/usr/bin/env python3
"""Near-real-time monitor: pull recent GFW events, keep the high-signal ones (foreign /
unauthorized in an EEZ, or a no-take reserve incursion), grade + evidence them, write the
?live view, and update the alerts feed (alerts.json + alerts.xml RSS).

Needs GFW_TOKEN (in .env or the environment). Run:
    uv run python scripts/live_monitor.py
"""

from __future__ import annotations

import html
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seavigil import authorization, evidence, iuu_list, live_monitor, notify, site  # noqa: E402
from seavigil.dossier import write_dossiers  # noqa: E402
from seavigil.jurisdiction import enrich_jurisdiction  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIVE_INC = ROOT / "results" / "live"
WEB_LIVE = ROOT / "web" / "data" / "live"
ALERTS_JSON = ROOT / "web" / "data" / "alerts.json"
ALERTS_RSS = ROOT / "web" / "alerts.xml"
LIVE_AUTH_CACHE = ROOT / "data" / "authorizations_live.json"
SITE_URL = "https://seavigil.org"
MAX_FEED = 80     # most-recent high-signal events shown in the live view
MAX_ALERTS = 200  # alert history kept in the feed


def _token() -> str:
    tok = os.environ.get("GFW_TOKEN", "")
    if not tok and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("GFW_TOKEN="):
                tok = line.split("=", 1)[1].strip().strip("'\"")
                break
    if not tok:
        raise SystemExit("GFW_TOKEN not set (events + authorization both need it).")
    return tok


def _severity(d: dict) -> tuple[str, str]:
    st = d.get("authorization_status")
    if d.get("_no_take"):
        return "high", "inside a no-take reserve"
    if st == "no_record":
        return "high", "foreign vessel, no authorization on record"
    if st == "authorization_lapsed":
        return "high", "foreign vessel, authorization lapsed"
    if st == "authorized":
        return "medium", "foreign vessel, authorization on record"
    return "medium", "foreign vessel, authorization unverified"


def _load_alerts() -> list[dict]:
    if ALERTS_JSON.exists():
        try:
            return json.loads(ALERTS_JSON.read_text()).get("alerts", [])
        except (ValueError, KeyError):
            return []
    return []


def _update_alerts(feed: list[dict], now_iso: str) -> int:
    """Append newly seen high-severity flags to the alert history; return the new count."""
    existing = _load_alerts()
    seen = {a["id"] for a in existing}
    fresh = []
    for d in feed:
        if d.get("severity") != "high" or d["incident_id"] in seen:
            continue
        fresh.append({
            "id": d["incident_id"], "first_seen": now_iso,
            "type": d["type"], "when": d.get("time_start_utc"),
            "eez": d.get("eez_name") or "", "flag": d.get("flag") or "",
            "authorization": d.get("authorization_status") or "",
            "severity_reason": d.get("severity_reason") or "",
            "lat": d.get("centroid_lat"), "lon": d.get("centroid_lon"),
            "ship_name": d.get("ship_name") or "",
        })
    alerts = (fresh + existing)[:MAX_ALERTS]
    ALERTS_JSON.write_text(json.dumps({"generated_at": now_iso, "alerts": alerts}, indent=0))
    _write_rss(alerts)
    return len(fresh)


def _write_rss(alerts: list[dict]) -> None:
    def esc(s: str) -> str:
        return html.escape(str(s or ""))
    items = []
    for a in alerts[:60]:
        title = f"{a['type']}: {a.get('flag') or 'unknown flag'} in {a.get('eez') or 'an EEZ'}"
        desc = (f"{a.get('ship_name') or 'vessel'} ({a.get('flag')}), {a.get('severity_reason')}. "
                f"Authorization: {a.get('authorization')}. Event time {a.get('when')}.")
        items.append(
            f"<item><title>{esc(title)}</title>"
            f"<description>{esc(desc)}</description>"
            f"<guid isPermaLink=\"false\">{esc(a['id'])}</guid>"
            f"<link>{SITE_URL}/?live</link></item>")
    rss = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="alerts.xsl"?>\n'
        '<rss version="2.0"><channel>'
        '<title>SeaVigil alerts</title>'
        f'<link>{SITE_URL}/?live</link>'
        '<description>New high-severity illegal-fishing leads: foreign or unauthorized '
        'vessels going dark or transshipping, from Global Fishing Watch events.</description>'
        + "".join(items) + "</channel></rss>")
    ALERTS_RSS.write_text(rss)


def main() -> None:
    token = _token()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    dossiers = live_monitor.build_dossiers(token, days=14, max_per_type=1500)
    enrich_jurisdiction(dossiers)  # eez_name / sovereign / foreign (from the GFW event flag)
    # High signal only: a foreign vessel inside another state's EEZ, or a no-take incursion.
    gfw = [d for d in dossiers if d.get("eez_foreign") is True or d.get("_no_take")]
    gfw.sort(key=lambda d: d.get("time_end_utc") or "", reverse=True)

    # AIS spoofing over the rolling positions buffer (always kept; the anomaly is the signal).
    buffer = os.environ.get("AIS_BUFFER")
    spoof: list[dict] = []
    if buffer:
        spoof = live_monitor.spoofing_dossiers(buffer)
        enrich_jurisdiction(spoof)
    feed = (spoof + gfw)[:MAX_FEED]
    print(f"fetched {len(dossiers)} recent events -> {len(gfw)} high-signal (foreign / no-take) "
          f"+ {len(spoof)} spoofing")

    mmsis = [d["vessel_id"] for d in feed if str(d.get("vessel_id") or "").isdigit()]
    cache = authorization.build_cache(mmsis, token, out_path=LIVE_AUTH_CACHE)
    authorization.enrich_authorization(feed, cache)
    for d in feed:
        if d.get("type") != "ais_spoofing":  # spoofing keeps the detector's own severity
            d["severity"], d["severity_reason"] = _severity(d)
    n_iuu = iuu_list.enrich_iuu(feed)  # known-offender flag (RFMO IUU lists); forces severity high
    if n_iuu:
        print(f"IUU cross-reference: {n_iuu} incident(s) match an RFMO IUU-listed vessel")
    notify.notify_incidents(feed)  # push NEW high-severity leads to a webhook if SEAVIGIL_WEBHOOK_URL set

    evidence.enrich_evidence(feed)
    LIVE_INC.mkdir(parents=True, exist_ok=True)
    for p in LIVE_INC.glob("*.md"):  # clear stale per-incident dossiers from the previous run
        if p.name != "INDEX.md":
            p.unlink()
    write_dossiers(feed, LIVE_INC)
    site.build_site(str(LIVE_INC / "incidents.json"), out_dir=str(WEB_LIVE))
    n_new = _update_alerts(feed, now_iso)
    print(f"live view: {len(feed)} flags written to {WEB_LIVE} | {n_new} new alert(s) -> {ALERTS_JSON.name}, {ALERTS_RSS.name}")


if __name__ == "__main__":
    main()
