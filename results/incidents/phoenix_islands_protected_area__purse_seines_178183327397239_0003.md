# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0003`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-11T21:23:25Z → 2013-11-12T03:50:22Z (6.449 h)
- **Apparent fishing:** 28 of 66 in-MPA positions; mean p=0.71, max p=0.93
- **Where:** -3.373, -172.776 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 3.123 | +0.072 |
| `speed` | 3.550 | +0.060 |
| `speed_roll_std` | 1.440 | +0.059 |
| `distance_from_shore` | 132060.473 | +0.039 |
| `distance_from_port` | 132515.531 | -0.024 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
