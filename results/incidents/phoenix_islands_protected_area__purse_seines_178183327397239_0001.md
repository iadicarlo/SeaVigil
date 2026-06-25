# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0001`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-11T04:38:02Z → 2013-11-11T04:39:42Z (0.028 h)
- **Apparent fishing:** 3 of 52 in-MPA positions; mean p=0.55, max p=0.58
- **Where:** -3.391, -172.742 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 9.000 | -0.076 |
| `speed_roll_mean` | 9.467 | -0.073 |
| `distance_from_shore` | 130173.609 | +0.062 |
| `hour_sin` | 0.938 | +0.046 |
| `distance_from_port` | 130645.172 | +0.046 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
