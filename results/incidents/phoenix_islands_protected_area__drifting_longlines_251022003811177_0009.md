# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0009`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-07T21:40:47Z → 2014-12-07T23:24:48Z (1.734 h)
- **Apparent fishing:** 79 of 82 in-MPA positions; mean p=0.67, max p=0.82
- **Where:** -3.322, -170.412 (centroid)
- **Track:** 82 positions, (-3.294, -170.292) → (-3.342, -170.506)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 79)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `hour_cos` | 0.926 | +0.073 |
| `hour_sin` | -0.341 | +0.041 |
| `distance_from_port` | 154754.615 | +0.038 |
| `distance_from_shore` | 55539.928 | +0.024 |
| `speed_roll_std` | 0.304 | +0.016 |

## Caveats

- Apparent fishing inferred from AIS movement, not proven illegal fishing.
- AIS-only: blind to vessels not broadcasting AIS (~75% of industrial fishing vessels).
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `f4cb8b84da52d96267d980efd257255d3927af2b3999b9d855a7d21aeb578809`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
