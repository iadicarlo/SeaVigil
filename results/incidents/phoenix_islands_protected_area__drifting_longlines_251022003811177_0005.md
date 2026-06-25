# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0005`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-05T09:54:39Z → 2014-12-05T16:21:08Z (6.441 h)
- **Apparent fishing:** 230 of 230 in-MPA positions; mean p=0.85, max p=0.97
- **Where:** -3.264, -170.201 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 230)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.384 | +0.127 |
| `speed` | 5.388 | +0.121 |
| `distance_from_shore` | 76615.002 | +0.082 |
| `speed_roll_std` | 0.480 | +0.033 |
| `distance_from_port` | 175494.784 | -0.006 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
