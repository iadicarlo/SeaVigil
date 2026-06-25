# Incident `phoenix_islands_protected_area__drifting_longlines_271347251834362_0000`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_271347251834362`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-06T01:39:29Z → 2014-06-10T17:13:17Z (111.563 h)
- **Apparent fishing:** 639 of 672 in-MPA positions; mean p=0.91, max p=1.00
- **Where:** -4.102, -171.862 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 639)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 3.304 | +0.146 |
| `speed_roll_mean` | 3.480 | +0.143 |
| `distance_from_shore` | 51934.752 | +0.077 |
| `distance_from_port` | 145735.464 | +0.020 |
| `hour_cos` | -0.108 | +0.018 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
