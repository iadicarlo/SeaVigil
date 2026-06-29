# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0006`

- **MPA:** Phoenix Islands Protected Area (WDPA 309888)
- **Severity:** MEDIUM (protected area (category not reported))  ·  boundary WDPA/WD-OECM Jun2026
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Authorization:** No vessel identity; authorization not checkable
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-05T22:31:41Z → 2014-12-06T03:55:45Z (5.401 h)
- **Apparent fishing:** 96 of 96 in-MPA positions; mean p=0.95, max p=0.99
- **Where:** -3.483, -171.058 (centroid)
- **Track:** 96 positions, (-3.468, -171.030) → (-3.468, -171.022)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 96)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 2.368 | +0.187 |
| `speed_roll_mean` | 2.348 | +0.175 |
| `distance_from_shore` | 37570.602 | +0.051 |
| `speed_roll_std` | 0.398 | +0.016 |
| `hour_cos` | 0.929 | +0.014 |

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
- **Integrity (SHA-256 of canonical facts):** `c6f29b30283034a5e6b0668eba3105c877b82dbc93043c7ceec6bb25aaa2174e`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
