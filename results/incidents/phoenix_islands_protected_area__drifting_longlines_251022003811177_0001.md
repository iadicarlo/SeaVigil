# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0001`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-02T10:19:38Z → 2014-12-02T17:14:07Z (6.908 h)
- **Apparent fishing:** 174 of 174 in-MPA positions; mean p=0.87, max p=0.99
- **Where:** -3.094, -173.950 (centroid)
- **Track:** 174 positions, (-3.077, -174.163) → (-3.274, -173.702)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

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

## Provenance & integrity

- Global Fishing Watch labelled AIS training data (Kroodsma et al., Science 2018). CC BY 4.0.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Model confidence:** Fishing probabilities are well-calibrated (Brier 0.0915 on 408,194 held-out positions from vessels not seen in training); read the score as a probability.
- **Integrity (SHA-256 of canonical facts):** `deb0881ec5989e09c8b6866dcda02d2eaa9798120f45744ae1f1be2a3faf82f8`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
