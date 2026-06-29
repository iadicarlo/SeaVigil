# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0000`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-11-27T23:44:50Z → 2014-12-02T02:30:47Z (98.766 h)
- **Apparent fishing:** 965 of 1150 in-MPA positions; mean p=0.87, max p=1.00
- **Where:** -2.540, -172.560 (centroid)
- **Track:** 1150 positions, (-2.108, -171.095) → (-3.024, -174.594)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

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

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `5405a2ae427b77658b7d86a5bbefa8d7889698541b6ce9e3781301c9ab8b0272`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
