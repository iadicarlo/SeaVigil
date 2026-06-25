"""Download, load, and clean Global Fishing Watch labeled AIS positions.

Data source: Global Fishing Watch "training-data" repository
(https://github.com/GlobalFishingWatch/training-data), the manually labeled AIS
position dataset described in Kroodsma et al., Science 2018.

The repository now stores its labeled positions as git-lfs ".npz" structured
arrays under "data/labeled/". The raw "data/<gear>.csv" layout referenced in
older tutorials no longer resolves (the per-gear CSVs were replaced by the
LFS-backed npz files). We therefore pull the npz files directly from the GitHub
LFS media endpoint, keep only the documented position columns, and present them
in the canonical schema:

    mmsi, timestamp, distance_from_shore, distance_from_port,
    speed, course, lat, lon, is_fishing, gear

Label semantics (GFW): is_fishing is 1 (fishing), 0 (not fishing), -1
(unlabeled), and can be fractional when annotations were averaged. We drop
is_fishing < 0 and binarize at 0.5 (>= 0.5 -> fishing).

Raw downloads are cached under data/raw/ (gitignored, never committed).
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

# Repo root: .../SeaVigil
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

# GitHub LFS media endpoint serves the real array bytes (the plain raw.* endpoint
# only returns the small LFS pointer file).
_LFS_BASE = (
    "https://media.githubusercontent.com/media/"
    "GlobalFishingWatch/training-data/master/data/labeled/"
)
_SUFFIX = ".measures.labels.npz"

# The position columns we keep. These exist in every labeled npz.
POSITION_COLUMNS = [
    "mmsi",
    "timestamp",
    "distance_from_shore",
    "distance_from_port",
    "speed",
    "course",
    "lat",
    "lon",
    "is_fishing",
]

# Per gear, the GFW source files (annotation campaigns) that carry that gear's
# labels. Combining campaigns gives more distinct vessels, which matters for a
# vessel-grouped train/test split.
GEAR_SOURCES: dict[str, list[str]] = {
    "trawlers": [
        "kristina_trawl_Trawlers",
        "pybossa_project_3_Trawlers",
        "false_positives_Trawlers",
    ],
    "drifting_longlines": [
        "kristina_longliner_Drifting_longlines",
        "pybossa_project_3_Drifting_longlines",
        "alex_crowd_sourced_Drifting_longlines",
    ],
    "purse_seines": [
        "kristina_ps_Purse_seines",
        "pybossa_project_3_Purse_seines",
        "alex_crowd_sourced_Purse_seines",
    ],
}

DEFAULT_GEARS = list(GEAR_SOURCES.keys())


def _cache_path(source: str) -> Path:
    return RAW_DIR / f"{source}{_SUFFIX}"


def download_source(source: str, *, force: bool = False) -> Path:
    """Download one GFW labeled-positions npz to data/raw/, with caching.

    Returns the local path. Existing non-empty files are reused unless force.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dest = _cache_path(source)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return dest
    url = f"{_LFS_BASE}{source}{_SUFFIX}"
    print(f"[data] downloading {source} ...")
    with urllib.request.urlopen(url, timeout=300) as resp:  # noqa: S310 (trusted host)
        payload = resp.read()
    dest.write_bytes(payload)
    print(f"[data]   saved {dest.name} ({len(payload) / 1e6:.1f} MB)")
    return dest


def _load_source_frame(source: str, gear: str) -> pd.DataFrame:
    """Load one cached npz as a DataFrame of position columns plus gear."""
    path = _cache_path(source)
    raw = np.load(io.BytesIO(path.read_bytes()), allow_pickle=True)["x"]
    cols = {c: np.asarray(raw[c], dtype="float64") for c in POSITION_COLUMNS}
    df = pd.DataFrame(cols)
    df["gear"] = gear
    df["source"] = source
    return df


def load_raw(
    gears: list[str] | None = None, *, force_download: bool = False
) -> pd.DataFrame:
    """Download (if needed) and load the raw labeled positions for given gears.

    No cleaning is applied here beyond column selection. mmsi values in this
    dataset are anonymized integer-valued floats; they are kept as-is and used
    only as grouping keys.
    """
    gears = gears or DEFAULT_GEARS
    frames: list[pd.DataFrame] = []
    for gear in gears:
        if gear not in GEAR_SOURCES:
            raise ValueError(f"unknown gear {gear!r}; known: {DEFAULT_GEARS}")
        for source in GEAR_SOURCES[gear]:
            download_source(source, force=force_download)
            frames.append(_load_source_frame(source, gear))
    df = pd.concat(frames, ignore_index=True)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean labeled positions into a binary, model-ready table.

    Steps:
      - drop unlabeled rows (is_fishing < 0),
      - binarize the (possibly fractional) label at 0.5,
      - drop rows with non-finite position/movement fields,
      - drop physically impossible coordinates,
      - build a unique, stable vessel id and a UTC datetime column.
    """
    df = df.copy()

    # Drop unlabeled (GFW uses -1 for unlabeled).
    df = df[df["is_fishing"] >= 0].copy()

    # Binarize fractional / averaged labels.
    df["label"] = (df["is_fishing"] >= 0.5).astype("int8")

    # Core numeric fields must be finite.
    core = ["mmsi", "timestamp", "speed", "course", "lat", "lon",
            "distance_from_shore", "distance_from_port"]
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=core)

    # Sane physical ranges.
    df = df[(df["lat"].between(-90, 90)) & (df["lon"].between(-180, 360))]
    df = df[df["speed"] >= 0]

    # A vessel id that stays unique even if the same anonymized mmsi appears in
    # two campaigns: combine gear + mmsi. (mmsi alone can collide across files.)
    df["vessel_id"] = (
        df["gear"].astype(str) + "_" + df["mmsi"].astype("int64").astype(str)
    )

    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)

    df = df.reset_index(drop=True)
    return df


def load_clean(
    gears: list[str] | None = None, *, force_download: bool = False
) -> pd.DataFrame:
    """Convenience: load_raw then clean."""
    return clean(load_raw(gears, force_download=force_download))


# Core columns an external (bring-your-own / live) positions file must provide. The
# distance_from_shore / distance_from_port features are computed (see seavigil.enrich)
# when absent, since raw AIS feeds don't carry them.
REQUIRED_POSITION_FIELDS = ["vessel_id", "timestamp", "lat", "lon", "speed", "course"]


def load_positions_file(path: str | Path, *, enrich_distances: bool = True) -> pd.DataFrame:
    """Load an external AIS positions file (CSV or Parquet) for SCORING.

    The model is trained on the GFW labels; this loads *new, unlabeled* positions to
    run inference on (your own AIS/VMS feed, or a live export). Required columns are
    REQUIRED_POSITION_FIELDS; ``gear`` is optional. ``timestamp`` is epoch seconds.
    If distance_from_shore / distance_from_port are absent they are computed from
    bundled coastline + ports (``enrich_distances``).
    """
    path = Path(path)
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)

    missing = [c for c in REQUIRED_POSITION_FIELDS if c not in df.columns]
    if missing:
        raise ValueError(
            f"positions file missing columns {missing}; required: {REQUIRED_POSITION_FIELDS}"
        )

    df = df.copy()
    for c in ["timestamp", "lat", "lon", "speed", "course"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    have_dist = {"distance_from_shore", "distance_from_port"} <= set(df.columns)
    if have_dist:
        for c in ["distance_from_shore", "distance_from_port"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=REQUIRED_POSITION_FIELDS)
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 360) & (df["speed"] >= 0)]

    if "gear" not in df.columns:
        df["gear"] = "unknown"
    df["vessel_id"] = df["vessel_id"].astype(str)
    df["label"] = 0  # unlabeled; present only so build_features can pass it through
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
    df = df.reset_index(drop=True)

    if not have_dist:
        if not enrich_distances:
            raise ValueError("positions lack distance_from_shore/port and enrich_distances=False")
        from seavigil import enrich  # local import: shapely-heavy, only needed for raw feeds
        df = enrich.add_distances(df)
    return df


if __name__ == "__main__":
    frame = load_clean()
    n_pos = int(frame["label"].sum())
    print(f"rows={len(frame):,}  vessels={frame['vessel_id'].nunique()}  "
          f"fishing={n_pos:,} ({100 * n_pos / len(frame):.1f}%)")
    print(frame.groupby("gear")["label"].agg(["count", "mean"]))
