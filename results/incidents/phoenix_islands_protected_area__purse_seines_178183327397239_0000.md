# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0000`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-07T03:03:07Z → 2013-11-08T15:27:28Z (36.406 h)
- **Apparent fishing:** 92 of 172 in-MPA positions; mean p=0.67, max p=0.89
- **Where:** -3.477, -171.915 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 92)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 2.662 | +0.132 |
| `speed_roll_mean` | 2.918 | +0.107 |
| `distance_from_port` | 76022.828 | -0.044 |
| `hour_cos` | -0.034 | -0.031 |
| `hour_sin` | 0.206 | -0.025 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
