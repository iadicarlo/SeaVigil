"""Per-position, physically interpretable movement features.

All features are computed *within each vessel track* (grouped by vessel_id,
ordered by time), so no information leaks across vessels and every feature has a
direct kinematic reading that makes a SHAP explanation meaningful.

Feature set
-----------
speed              : reported instantaneous speed over ground (knots).
speed_roll_mean    : mean speed over a small trailing window (smooths noise).
speed_roll_std     : speed variability over that window (steady vs. erratic).
turning_rate       : absolute course change per minute (deg/min); high when the
                     vessel is working a fishing pattern, low when steaming.
abs_course_change  : absolute course change to the previous point (deg), the
                     raw turn before normalizing by time.
time_gap_min       : minutes since the previous fix (AIS cadence / coverage).
distance_from_shore: meters to nearest shore (context: fishing grounds).
distance_from_port : meters to nearest port (context: transit vs. on-grounds).
hour_sin, hour_cos : cyclic encoding of local-UTC hour-of-day (diel pattern).

The window length and gap clipping are conservative defaults chosen so the
features stay interpretable rather than tuned for raw score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Trailing rolling window, in number of positions, for speed smoothing.
ROLL_WINDOW = 5

# Clip implausible time gaps (e.g. multi-day AIS outages) so per-minute rates
# stay finite and interpretable. 6 hours is a generous upper bound for a fix.
MAX_GAP_MINUTES = 6 * 60.0
MIN_GAP_MINUTES = 1.0 / 60.0  # 1 second floor to avoid divide-by-zero

FEATURE_COLUMNS = [
    "speed",
    "speed_roll_mean",
    "speed_roll_std",
    "turning_rate",
    "abs_course_change",
    "time_gap_min",
    "distance_from_shore",
    "distance_from_port",
    "hour_sin",
    "hour_cos",
]


def _angular_diff(course: np.ndarray) -> np.ndarray:
    """Absolute minimal angular difference (deg) to the previous course.

    Wraps correctly around 0/360 so a 350 -> 10 step is a 20 deg turn, not 340.
    The first point of a track has no predecessor and is set to 0.
    """
    prev = np.empty_like(course)
    prev[0] = course[0]
    prev[1:] = course[:-1]
    diff = (course - prev + 180.0) % 360.0 - 180.0
    return np.abs(diff)


def _track_features(track: pd.DataFrame) -> pd.DataFrame:
    """Compute movement features for one vessel track, ordered by time."""
    t = track.sort_values("timestamp").copy()

    speed = t["speed"].to_numpy(dtype="float64")
    course = t["course"].to_numpy(dtype="float64")
    ts = t["timestamp"].to_numpy(dtype="float64")

    # Time gap to previous fix (minutes), clipped to a sane range.
    gap = np.empty_like(ts)
    gap[0] = np.nan
    gap[1:] = (ts[1:] - ts[:-1]) / 60.0
    gap = np.clip(gap, MIN_GAP_MINUTES, MAX_GAP_MINUTES)
    # First point: assume a typical cadence rather than NaN, so the row is usable.
    if len(gap) > 1:
        gap[0] = np.nanmedian(gap[1:])
    else:
        gap[0] = MIN_GAP_MINUTES

    # Course change and turning rate (deg per minute).
    abs_dcourse = _angular_diff(course)
    turning_rate = abs_dcourse / gap

    # Trailing rolling speed stats (min_periods=1 so early points are defined).
    s = pd.Series(speed)
    roll_mean = s.rolling(ROLL_WINDOW, min_periods=1).mean().to_numpy()
    roll_std = s.rolling(ROLL_WINDOW, min_periods=1).std().fillna(0.0).to_numpy()

    # Hour-of-day cyclic encoding (UTC; the dataset is global so this is a
    # coarse diel proxy rather than true local solar time).
    hour = (t["datetime"].dt.hour + t["datetime"].dt.minute / 60.0).to_numpy()
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)

    out = pd.DataFrame(
        {
            "speed": speed,
            "speed_roll_mean": roll_mean,
            "speed_roll_std": roll_std,
            "turning_rate": turning_rate,
            "abs_course_change": abs_dcourse,
            "time_gap_min": gap,
            "distance_from_shore": t["distance_from_shore"].to_numpy(),
            "distance_from_port": t["distance_from_port"].to_numpy(),
            "hour_sin": hour_sin,
            "hour_cos": hour_cos,
            "label": t["label"].to_numpy(),
            "vessel_id": t["vessel_id"].to_numpy(),
            "gear": t["gear"].to_numpy(),
            # Passthrough position/time columns (not model features) so the MPA
            # overlay and incident builder can locate and timestamp each row.
            "lat": t["lat"].to_numpy(),
            "lon": t["lon"].to_numpy(),
            "timestamp": ts,
        },
        index=t.index,
    )
    # Optional vessel-identity passthrough (present for live / BYO AIS, absent for the
    # anonymized GFW training labels) so dossiers can show name / flag / destination.
    for col in ("ship_name", "flag", "destination", "ship_type"):
        if col in t.columns:
            out[col] = t[col].to_numpy()
    return out


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the per-position feature table from cleaned positions.

    Returns a frame with FEATURE_COLUMNS plus label, vessel_id, gear. Rows keep
    one-to-one correspondence with input positions (within-track ordering only).
    """
    parts = [
        _track_features(track)
        for _, track in df.groupby("vessel_id", sort=False)
    ]
    feats = pd.concat(parts).sort_index()

    # Guard: distances in the GFW set are in meters and non-negative; any
    # residual non-finite value from upstream is dropped here.
    feats = feats.replace([np.inf, -np.inf], np.nan).dropna(subset=FEATURE_COLUMNS)
    return feats.reset_index(drop=True)


def split_xy(feats: pd.DataFrame):
    """Return (X, y, groups) ready for a vessel-grouped split."""
    X = feats[FEATURE_COLUMNS].to_numpy(dtype="float64")
    y = feats["label"].to_numpy(dtype="int64")
    groups = feats["vessel_id"].to_numpy()
    return X, y, groups


if __name__ == "__main__":
    from seavigil.data import load_clean

    clean = load_clean()
    f = build_features(clean)
    print(f"feature rows: {len(f):,}  columns: {FEATURE_COLUMNS}")
    print(f.describe().T[["mean", "std", "min", "max"]])
