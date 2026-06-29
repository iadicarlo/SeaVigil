# Incident `phoenix_islands_protected_area__drifting_longlines_271347251834362_0001`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_271347251834362`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-21T02:01:39Z → 2014-06-26T01:02:46Z (119.019 h)
- **Apparent fishing:** 727 of 1004 in-MPA positions; mean p=0.89, max p=1.00
- **Where:** -3.031, -171.341 (centroid)
- **Track:** 1004 positions, (-4.507, -173.447) → (-2.523, -171.385)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

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

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `e7e9973739f31912110ff04a5dffc6daa9a2dae839cba7c0eca9ae5ce90a3a1d`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
