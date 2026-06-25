"""Enrich raw AIS positions with distance_from_shore / distance_from_port.

Raw AIS/VMS feeds carry lat/lon/speed/course but NOT the distance-to-shore and
distance-to-port features the model needs. This computes them from bundled Natural
Earth coastline + ports (public domain), so any feed becomes scorable by
``alert --positions``. Distances are great-circle metres to the nearest coastline
and the nearest port; CPU-only, shapely + numpy.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import shapely
from shapely import STRtree
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parent.parent
COASTLINE_GEOJSON = ROOT / "data" / "geo" / "ne_110m_coastline.geojson"
PORTS_GEOJSON = ROOT / "data" / "geo" / "ne_10m_ports.geojson"
EARTH_RADIUS_M = 6_371_000.0


def _haversine_m(lon1, lat1, lon2, lat2) -> np.ndarray:
    lon1, lat1, lon2, lat2 = (np.radians(np.asarray(a, dtype="float64"))
                              for a in (lon1, lat1, lon2, lat2))
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return EARTH_RADIUS_M * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _load_geoms(path: Path):
    data = json.loads(Path(path).read_text())
    return [shape(f["geometry"]) for f in data.get("features", []) if f.get("geometry")]


def add_distances(
    df,
    *,
    lon_col: str = "lon",
    lat_col: str = "lat",
    coastline_path: str | Path = COASTLINE_GEOJSON,
    ports_path: str | Path = PORTS_GEOJSON,
):
    """Add distance_from_shore and distance_from_port (metres) to a positions frame."""
    lon = df[lon_col].to_numpy(dtype="float64")
    lat = df[lat_col].to_numpy(dtype="float64")
    pts = shapely.points(lon, lat)

    # Nearest coastline: nearest line geometry, then the nearest point on it.
    coast = np.array(_load_geoms(coastline_path), dtype=object)
    coast_tree = STRtree(coast)
    nearest_line = coast[coast_tree.nearest(pts)]
    seg = shapely.shortest_line(pts, nearest_line)          # 2-coord lines: [point, on-shore]
    on_shore = shapely.get_coordinates(seg).reshape(-1, 2, 2)[:, 1, :]
    dist_shore = _haversine_m(lon, lat, on_shore[:, 0], on_shore[:, 1])

    # Nearest port (points): nearest port, great-circle distance to it.
    ports = np.array(_load_geoms(ports_path), dtype=object)
    port_xy = shapely.get_coordinates(ports)               # (n_ports, 2)
    port_tree = STRtree(ports)
    npi = port_tree.nearest(pts)
    dist_port = _haversine_m(lon, lat, port_xy[npi, 0], port_xy[npi, 1])

    out = df.copy()
    out["distance_from_shore"] = dist_shore
    out["distance_from_port"] = dist_port
    return out


if __name__ == "__main__":
    import pandas as pd
    demo = pd.DataFrame({"lon": [-140.0, -91.0, 0.0], "lat": [0.0, -0.5, 51.5]})
    e = add_distances(demo)
    print(e[["lon", "lat", "distance_from_shore", "distance_from_port"]].round(0))
