# Incident `great_barrier_reef_marine_park__503011670_0000`

- **MPA:** Great Barrier Reef Marine Park
- **Severity:** LOW (multi-use protected area)  ·  boundary sample-approx-2024
- **Vessel:** 🇦🇺 QPV PERRY IRWIN  ·  **gear:** unknown
- **When (UTC):** 2026-06-28T22:54:49Z → 2026-06-28T22:54:49Z (0.0 h)
- **Apparent fishing:** 1 of 1 in-MPA positions; mean p=0.67, max p=0.67
- **Where:** -16.952, 145.773 (centroid)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; here the speed rule alone suffices.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `distance_from_shore` | 10043.985 | +0.208 |
| `distance_from_port` | 2505.309 | -0.096 |
| `speed` | 0.000 | +0.046 |
| `hour_cos` | 0.959 | +0.030 |
| `speed_roll_std` | 0.000 | -0.024 |

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
- **Integrity (SHA-256 of canonical facts):** `f29f3f1f48653492993edcb4ee02b9726effc9a99b34415c1730d2e6123264e5`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
