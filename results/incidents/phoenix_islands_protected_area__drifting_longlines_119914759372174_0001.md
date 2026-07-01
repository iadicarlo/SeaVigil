# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0001`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-08-15T06:38:37Z → 2014-08-18T18:51:14Z (84.21 h)
- **Apparent fishing:** 174 of 200 in-MPA positions; mean p=0.90, max p=1.00
- **Where:** -2.208, -171.509 (centroid)
- **Track:** 200 positions, (-2.201, -171.286) → (-2.184, -171.272)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions (sampled 50 of 174)._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 4.320 | +0.151 |
| `speed` | 4.358 | +0.138 |
| `distance_from_shore` | 69095.788 | +0.078 |
| `speed_roll_std` | 0.963 | +0.047 |
| `abs_course_change` | 22.568 | +0.005 |

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
- **Integrity (SHA-256 of canonical facts):** `3eb720da31152bcf507df78104f228475d190bbeee6443bddbc8f23418a7d0a0`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
