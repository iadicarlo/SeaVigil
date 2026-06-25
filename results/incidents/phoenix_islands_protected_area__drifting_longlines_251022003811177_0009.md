# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0009`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-07T21:40:47Z → 2014-12-07T23:24:48Z (1.734 h)
- **Apparent fishing:** 79 of 82 in-MPA positions; mean p=0.67, max p=0.82
- **Where:** -3.322, -170.412 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 79)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `hour_cos` | 0.926 | +0.073 |
| `hour_sin` | -0.341 | +0.041 |
| `distance_from_port` | 154754.615 | +0.038 |
| `distance_from_shore` | 55539.928 | +0.024 |
| `speed_roll_std` | 0.304 | +0.016 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
