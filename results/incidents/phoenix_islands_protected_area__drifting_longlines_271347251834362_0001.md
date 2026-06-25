# Incident `phoenix_islands_protected_area__drifting_longlines_271347251834362_0001`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_271347251834362`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-21T02:01:39Z → 2014-06-26T01:02:46Z (119.019 h)
- **Apparent fishing:** 727 of 1004 in-MPA positions; mean p=0.89, max p=1.00
- **Where:** -3.031, -171.341 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 727)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.302 | +0.103 |
| `speed` | 5.240 | +0.092 |
| `distance_from_shore` | 96878.158 | +0.083 |
| `distance_from_port` | 180864.163 | +0.045 |
| `hour_cos` | -0.132 | +0.028 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
