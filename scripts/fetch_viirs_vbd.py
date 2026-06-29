#!/usr/bin/env python3
"""Fetch VIIRS Boat Detection (VBD) detections from NOAA / Earth Observation Group (Payne
Institute, Colorado School of Mines), filtered to the watchlist.

VBD finds vessels that use bright lights to attract catch (squid jiggers, some purse seines) at
night. That is exactly the distant-water fleet that terrestrial AIS misses offshore, so it is the
free imagery layer that complements our Sentinel-1 SAR for the open-ocean dark fleet.

Free "final" (fnl) data is open but behind a free EOG account: register at
https://eogdata.mines.edu/products/register/ , then set EOG_USER and EOG_PASS in the environment.
Auth is a Keycloak password grant; the client and endpoint are overridable via env if EOG changes
them (EOG_TOKEN_URL, EOG_CLIENT_ID, EOG_CLIENT_SECRET).

    EOG_USER=... EOG_PASS=... uv run python scripts/fetch_viirs_vbd.py \
        --date 20260510 --out data/positions/vbd_detections.csv

Output CSV (the viirs_vbd_to_incidents.py input): lon, lat, timestamp, radiance, qf, scene_id.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WATCHLIST = ROOT / "data" / "watchlist.json"
TOKEN_URL = os.environ.get(
    "EOG_TOKEN_URL", "https://eogauth.mines.edu/realms/eog/protocol/openid-connect/token")
CLIENT_ID = os.environ.get("EOG_CLIENT_ID", "eogdata_oidc")
CLIENT_SECRET = os.environ.get("EOG_CLIENT_SECRET", "2677ad81-521b-4869-8480-6d05b9e57d48")
VBD_BASE = "https://eogdata.mines.edu/wwwdata/viirs_products/vbd-pub/v23"
# Column names in the v2.3 VBD CSV (overridable if EOG revises the schema).
COL = {"lat": os.environ.get("VBD_COL_LAT", "Lat_DNB"),
       "lon": os.environ.get("VBD_COL_LON", "Lon_DNB"),
       "rad": os.environ.get("VBD_COL_RAD", "Rad_DNB"),
       "qf": os.environ.get("VBD_COL_QF", "QF_Detect")}
BOAT_QF = {"1"}   # strong boat detections only (2=weak, 5=gas flare, 7=glow, 10=platform, ...)


def _token(user: str, pw: str) -> str:
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
        "username": user, "password": pw, "grant_type": "password"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        tok = json.load(r).get("access_token")
    if not tok:
        raise SystemExit("EOG auth returned no access_token (check EOG_USER / EOG_PASS).")
    return tok


def _download(url: str, token: str) -> str:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read().decode("utf-8", "replace")


def _areas():
    return json.loads(WATCHLIST.read_text())["areas"]


def _in_watchlist(lon, lat, areas) -> bool:
    for a in areas:
        w, s, e, n = a["bbox"]
        if w <= lon <= e and s <= lat <= n:
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch VIIRS Boat Detection (VBD) boats over the watchlist")
    ap.add_argument("--date", required=True, help="UTC date YYYYMMDD (free 'final' data lags ~weeks)")
    ap.add_argument("--region", default="global-saa", help="VBD region (default global-saa)")
    ap.add_argument("--out", default="data/positions/vbd_detections.csv")
    a = ap.parse_args()

    user, pw = os.environ.get("EOG_USER"), os.environ.get("EOG_PASS")
    if not (user and pw):
        raise SystemExit("Set EOG_USER and EOG_PASS (free account: https://eogdata.mines.edu/products/register/).")

    token = _token(user, pw)
    url = f"{VBD_BASE}/{a.region}/fnl/VBD_npp_d{a.date}_{a.region}_noaa_ops_v23.csv"
    print(f"downloading {url}")
    text = _download(url, token)

    areas = _areas()
    ts = int(datetime.strptime(a.date, "%Y%m%d").replace(tzinfo=timezone.utc).timestamp())
    scene = f"VBD_npp_d{a.date}"
    out_rows, total, boats = [], 0, 0
    for row in csv.DictReader(io.StringIO(text)):
        total += 1
        if str(row.get(COL["qf"], "")).strip() not in BOAT_QF:
            continue
        boats += 1
        try:
            lon, lat = float(row[COL["lon"]]), float(row[COL["lat"]])
        except (KeyError, ValueError):
            continue
        if not _in_watchlist(lon, lat, areas):
            continue
        out_rows.append({"lon": lon, "lat": lat, "timestamp": ts,
                         "radiance": row.get(COL["rad"], ""), "qf": row.get(COL["qf"], ""),
                         "scene_id": scene})

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["lon", "lat", "timestamp", "radiance", "qf", "scene_id"])
        w.writeheader()
        w.writerows(out_rows)
    print(f"{total} VBD records, {boats} boats, {len(out_rows)} inside the watchlist -> {out}")
    print("Fold into the view:")
    print(f"  uv run python scripts/viirs_vbd_to_incidents.py --detections {out}")


if __name__ == "__main__":
    main()
