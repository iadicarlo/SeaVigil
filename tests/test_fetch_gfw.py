"""Tests for the GFW SAR report parser (pure; no network)."""

from __future__ import annotations

from seavigil import fetch_gfw

# Shape mirrors a real 4Wings SAR report: one matched + one dark entry.
_PAYLOAD = {
    "entries": [
        {
            "public-global-sar-presence:v4.0": [
                {"lat": -0.4, "lon": -91.27, "detections": 1, "mmsi": "735060020",
                 "flag": "ECU", "shipName": "GRAND DAPHNE", "vesselType": "PASSENGER",
                 "geartype": "PASSENGER", "entryTimestamp": "2024-01-06T00:27:22Z"},
                {"lat": -0.7, "lon": -91.10, "detections": 2, "mmsi": "",
                 "flag": "", "shipName": "", "vesselType": "", "geartype": "",
                 "entryTimestamp": "2024-02-02T05:00:00Z"},
            ]
        }
    ]
}


def test_parse_sar_report_matched_and_dark():
    recs = fetch_gfw.parse_sar_report(_PAYLOAD)
    assert len(recs) == 2
    matched = [r for r in recs if r["matched_to_ais"]]
    dark = [r for r in recs if not r["matched_to_ais"]]
    assert len(matched) == 1 and len(dark) == 1
    assert matched[0]["flag"] == "ECU" and matched[0]["ship_name"] == "GRAND DAPHNE"
    assert dark[0]["flag"] is None and dark[0]["mmsi"] is None
    assert recs[0]["length_m"] is None  # API does not return length_m


def test_parse_skips_rows_without_coords():
    payload = {"entries": [{"ds": [{"mmsi": "1"}, {"lat": 1.0, "lon": 2.0, "mmsi": "2"}]}]}
    assert len(fetch_gfw.parse_sar_report(payload)) == 1


def test_to_geojson_shape_and_attribution():
    gj = fetch_gfw.to_geojson(fetch_gfw.parse_sar_report(_PAYLOAD))
    assert gj["type"] == "FeatureCollection"
    assert "Global Fishing Watch" in gj["_attribution"]
    f = gj["features"][0]
    assert f["geometry"]["type"] == "Point"
    assert f["geometry"]["coordinates"] == [-91.27, -0.4]
    assert "matched_to_ais" in f["properties"]


def test_empty_payload():
    assert fetch_gfw.parse_sar_report({}) == []
