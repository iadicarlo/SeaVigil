# Incident `phoenix_islands_protected_area__drifting_longlines_251022003811177_0007`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_251022003811177`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-12-06T10:07:06Z → 2014-12-07T01:45:15Z (15.636 h)
- **Apparent fishing:** 310 of 312 in-MPA positions; mean p=0.84, max p=0.99
- **Where:** -3.353, -170.628 (centroid)
- **Track:** 312 positions, (-3.340, -170.690) → (-3.463, -170.920)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 310)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 5.926 | +0.094 |
| `speed` | 5.818 | +0.077 |
| `hour_cos` | 0.045 | +0.055 |
| `distance_from_port` | 132913.164 | +0.038 |
| `distance_from_shore` | 41600.642 | +0.037 |

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
- **Integrity (SHA-256 of canonical facts):** `f90b4a4265c2979f069491591b80a3df0b92dd9adec93451d0ae95fb16a208c7`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
