# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0004`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-04T17:12:23Z → 2014-12-05T02:13:13Z (9.014 h)
- **Apparent fishing:** 111 of 354 in-MPA positions; mean p=0.74, max p=0.92
- **Where:** -3.629, -171.023 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 111)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 4.840 | +0.128 |
| `speed_roll_mean` | 4.871 | +0.120 |
| `speed_roll_std` | 0.527 | +0.022 |
| `distance_from_port` | 118198.793 | -0.022 |
| `hour_cos` | 0.932 | -0.018 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
