# Incident `great_barrier_reef_marine_park__503177400_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Severity:** LOW (multi-use protected area)  ·  boundary sample-approx-2024
- **Vessel:** 🇦🇺 PMG PRIDE  ·  **gear:** unknown  ·  Tug  ·  to MACKAY
- **When (UTC):** 2026-06-26T02:11:38Z → 2026-06-26T02:11:38Z (0.0 h)
- **Apparent fishing:** 1 of 1 in-MPA positions; mean p=0.68, max p=0.68
- **Where:** -19.259, 146.840 (centroid)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 8195.748 | +0.213 |
| `distance_from_port` | 1900.106 | -0.103 |
| `speed` | 0.000 | +0.048 |
| `hour_cos` | 0.841 | +0.031 |
| `speed_roll_std` | 0.000 | -0.025 |

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
- **Integrity (SHA-256 of canonical facts):** `a3150d0c09c91cc51cf63b220ca0e37f9fb71361fdf17aaad4c1ecc2864954bb`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
