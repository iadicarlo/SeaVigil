# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0001`

- **MPA:** Phoenix Islands Protected Area
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-02T10:19:38Z → 2014-12-02T17:14:07Z (6.908 h)
- **Apparent fishing:** 174 of 174 in-MPA positions; mean p=0.87, max p=0.99
- **Where:** -3.094, -173.950 (centroid)

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 174)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.048 | +0.135 |
| `speed` | 5.184 | +0.127 |
| `distance_from_shore` | 60201.038 | +0.060 |
| `speed_roll_std` | 0.528 | +0.037 |
| `distance_from_port` | 249871.425 | +0.008 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.
