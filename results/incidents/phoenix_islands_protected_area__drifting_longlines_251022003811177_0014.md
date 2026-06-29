# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0014`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-15T06:25:57Z → 2014-12-15T08:53:04Z (2.452 h)
- **Apparent fishing:** 98 of 98 in-MPA positions; mean p=0.93, max p=0.97
- **Where:** -3.475, -170.915 (centroid)
- **Track:** 98 positions, (-3.489, -170.961) → (-3.461, -170.850)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 98)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 3.426 | +0.173 |
| `speed_roll_mean` | 3.502 | +0.172 |
| `speed_roll_std` | 0.740 | +0.035 |
| `distance_from_shore` | 35579.989 | +0.026 |
| `hour_sin` | 0.896 | +0.008 |

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
- **Integrity (SHA-256 of canonical facts):** `182dc0ded2ce51d275abb736e06948f2103f754f2b414eae8b69d41cad579d8a`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
