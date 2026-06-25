# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0000`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-11-27T23:44:50Z → 2014-12-02T02:30:47Z (98.766 h)
- **Apparent fishing:** 965 of 1150 in-MPA positions; mean p=0.87, max p=1.00
- **Where:** -2.540, -172.560 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 965)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.738 | +0.122 |
| `speed` | 4.792 | +0.118 |
| `distance_from_shore` | 73086.679 | +0.074 |
| `speed_roll_std` | 0.492 | +0.033 |
| `distance_from_port` | 148635.644 | +0.007 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
