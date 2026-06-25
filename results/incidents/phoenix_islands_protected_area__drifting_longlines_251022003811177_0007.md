# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0007`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-06T10:07:06Z → 2014-12-07T01:40:44Z (15.561 h)
- **Apparent fishing:** 309 of 312 in-MPA positions; mean p=0.85, max p=0.99
- **Where:** -3.353, -170.627 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 309)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.935 | +0.095 |
| `speed` | 5.902 | +0.079 |
| `hour_cos` | 0.046 | +0.058 |
| `distance_from_port` | 132517.859 | +0.038 |
| `distance_from_shore` | 41444.697 | +0.034 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
