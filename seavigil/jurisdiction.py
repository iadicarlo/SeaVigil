"""Tag incidents with the EEZ (national jurisdiction) they fall in.

Most IUU fishing is a vessel fishing inside a coastal state's Exclusive Economic
Zone, so every incident is tagged with its EEZ and sovereign, and flagged FOREIGN
when the vessel's flag (derived from its MMSI) differs from the EEZ sovereign. A
foreign vessel apparent-fishing inside another state's EEZ is the canonical IUU
lead; it is not proof (the vessel may be licensed), so the dossier says so.

EEZ boundaries: Marine Regions (Flanders VLIZ), CC BY 4.0. The Python index reads the
global ``data/eez_tag.geojson.gz`` (every coastal state); the map renders the matching
``web/tiles/eez.pmtiles``, so the map and the dossiers agree on the boundary.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import shape

from seavigil.flags import from_iso3

ROOT = Path(__file__).resolve().parent.parent
# Global EEZ tag set (every coastal state) so any incident worldwide is placed in a
# jurisdiction and foreign-vs-domestic can be decided. Built by scripts/build_eez_tag.py;
# gzipped to keep the full-resolution boundary light enough to commit.
EEZ_GEOJSON = ROOT / "data" / "eez_tag.geojson.gz"


class EEZIndex:
    """STRtree point-in-polygon index over the global EEZ polygons."""

    def __init__(self, path: str | Path = EEZ_GEOJSON):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"EEZ tag file not found: {path}. Build it with "
                "`uv run --with pyogrio --with geopandas python scripts/build_eez_tag.py`."
            )
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
        self.features: list[dict] = [f for f in data.get("features", []) if f.get("geometry")]
        geoms = np.array([shape(f["geometry"]) for f in self.features], dtype=object)
        if not len(geoms):
            raise ValueError(f"EEZ tag file has no usable polygons: {path}")
        shapely.prepare(geoms)  # fast repeated point-in-polygon on large EEZ polygons
        self._tree = STRtree(geoms)

    def assign(self, lon: float, lat: float) -> dict | None:
        """Return the properties of the EEZ containing (lon, lat), or None."""
        if self._tree is None:
            return None
        hits = self._tree.query(shapely.points(lon, lat), predicate="intersects")
        if len(hits) == 0:
            return None
        return self.features[int(hits[0])]["properties"]

    def assign_many(self, lons, lats) -> np.ndarray:
        """Vectorized: feature index per point (-1 if outside every EEZ).

        One GEOS query for all points, vital when tagging tens of thousands of events
        (a per-point loop is far too slow against large EEZ polygons like the US).
        """
        lons = np.atleast_1d(np.asarray(lons, dtype="float64")).ravel()
        lats = np.atleast_1d(np.asarray(lats, dtype="float64")).ravel()
        out = np.full(lons.shape, -1, dtype="int64")
        if self._tree is None or lons.size == 0:
            return out
        point_idx, feat_idx = self._tree.query(shapely.points(lons, lats), predicate="intersects")
        order = np.argsort(feat_idx, kind="stable")  # lowest feature index wins, deterministically
        for p, fi in zip(point_idx[order], feat_idx[order]):
            if out[p] == -1:
                out[p] = fi
        return out


def _to_iso2(code: str | None) -> str:
    """Normalize a country code (ISO2 from MMSI, or ISO3 from GFW SAR) to ISO2."""
    if not code:
        return ""
    c = code.strip().upper()
    if len(c) == 3:
        iso2, _ = from_iso3(c)
        return iso2
    return c


def is_foreign(flag: str | None, eez_iso_sov: str | None) -> bool | None:
    """True if the vessel flag differs from the EEZ sovereign; None if undetermined.

    Handles mixed code formats: AIS flags arrive as ISO2 (from MMSI), GFW SAR flags
    and the EEZ sovereign as ISO3. Both are normalized to ISO2 before comparison.
    """
    f, s = _to_iso2(flag), _to_iso2(eez_iso_sov)
    if not f or not s:
        return None
    return f != s


def enrich_jurisdiction(dossiers: list[dict], index: EEZIndex | None = None) -> list[dict]:
    """Add eez_name / eez_sovereign / eez_foreign to each dossier dict in place.

    Incidents outside every showcase EEZ are left untagged. ``eez_foreign`` is None
    when the vessel flag is unknown (e.g. anonymized AIS labels or a dark SAR blip).
    """
    index = index or EEZIndex()
    if index._tree is None:  # noqa: SLF001 (internal, same module)
        return dossiers
    for d in dossiers:
        lon, lat = d.get("centroid_lon"), d.get("centroid_lat")
        if lon is None or lat is None:
            continue
        props = index.assign(lon, lat)
        if not props:
            continue
        d["eez_name"] = props.get("name")
        d["eez_sovereign"] = props.get("sovereign")
        d["eez_iso_sov"] = props.get("iso_sov")
        d["eez_foreign"] = is_foreign(d.get("flag"), props.get("iso_sov"))
    return dossiers
