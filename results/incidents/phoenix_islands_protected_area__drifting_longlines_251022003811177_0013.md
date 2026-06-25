# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0013`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-14T19:02:23Z → 2014-12-14T22:16:53Z (3.242 h)
- **Apparent fishing:** 174 of 176 in-MPA positions; mean p=0.84, max p=0.96
- **Where:** -3.466, -170.168 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 174)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 6.110 | +0.088 |
| `speed` | 6.098 | +0.077 |
| `distance_from_shore` | 66842.888 | +0.068 |
| `hour_sin` | -0.719 | +0.044 |
| `hour_cos` | 0.657 | +0.043 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
