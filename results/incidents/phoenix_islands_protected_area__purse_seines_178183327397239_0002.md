# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0002`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-11T11:07:33Z → 2013-11-11T14:40:01Z (3.541 h)
- **Apparent fishing:** 17 of 66 in-MPA positions; mean p=0.57, max p=0.76
- **Where:** -3.317, -172.868 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 1.053 | +0.057 |
| `speed_roll_std` | 1.168 | +0.055 |
| `hour_cos` | -0.833 | -0.045 |
| `speed_roll_mean` | 1.929 | +0.041 |
| `hour_sin` | -0.463 | -0.020 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
