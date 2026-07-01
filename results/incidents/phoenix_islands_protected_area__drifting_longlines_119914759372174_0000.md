# Incident `phoenix_islands_protected_area__drifting_longlines_119914759372174_0000`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `drifting_longlines_119914759372174`  ·  **gear:** drifting_longlines
- **When (UTC):** 2014-06-04T03:53:41Z → 2014-06-04T13:13:20Z (9.328 h)
- **Apparent fishing:** 24 of 28 in-MPA positions; mean p=0.93, max p=0.98
- **Where:** -2.328, -170.271 (centroid)
- **Track:** 28 positions, (-2.300, -170.135) → (-2.361, -170.026)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed_roll_mean` | 3.817 | +0.169 |
| `speed` | 3.417 | +0.157 |
| `distance_from_shore` | 125720.178 | +0.072 |
| `speed_roll_std` | 1.241 | +0.036 |
| `distance_from_port` | 170164.917 | -0.005 |

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
- **Integrity (SHA-256 of canonical facts):** `87ad4e33b248a35e3279182a39b1f1f5d7e8661b8cde7d3201889a22b8994d16`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
