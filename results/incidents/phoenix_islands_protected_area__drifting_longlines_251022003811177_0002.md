# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0002`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-02T23:51:10Z → 2014-12-03T04:47:09Z (4.933 h)
- **Apparent fishing:** 142 of 144 in-MPA positions; mean p=0.76, max p=0.89
- **Where:** -3.970, -174.197 (centroid)
- **Track:** 144 positions, (-3.934, -174.026) → (-4.046, -173.991)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 142)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `hour_cos` | 0.893 | +0.092 |
| `distance_from_port` | 303895.741 | +0.081 |
| `speed_roll_mean` | 7.413 | +0.032 |
| `speed_roll_std` | 0.229 | +0.020 |
| `hour_sin` | 0.385 | +0.011 |

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
- **Integrity (SHA-256 of canonical facts):** `a09d2644391453e973bfcc32333b6d3a0e30e418b4d6a466d616fbaf3ccbb8f5`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
