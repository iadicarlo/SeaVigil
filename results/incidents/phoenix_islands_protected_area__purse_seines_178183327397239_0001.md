# Incident `phoenix_islands_protected_area__purse_seines_178183327397239_0001`

- **MPA:** Phoenix Islands Protected Area
- **Severity:** HIGH (strict no-take reserve)  ·  boundary sample-approx-2024
- **EEZ:** Kiribati Exclusive Economic Zone (Phoenix Group) (Kiribati)
- **Vessel:** `purse_seines_178183327397239`  ·  **gear:** purse_seines
- **When (UTC):** 2013-11-11T04:38:02Z → 2013-11-11T04:39:42Z (0.028 h)
- **Apparent fishing:** 4 of 52 in-MPA positions; mean p=0.55, max p=0.62
- **Where:** -3.390, -172.742 (centroid)
- **Track:** 52 positions, (-3.312, -172.974) → (-3.389, -172.742)
- **Vs. speed baseline:** the trivial rule (speed < 10.7 kn) also flags 100% of these positions; the rule agrees on this slow visit, but globally the model beats the speed rule by a wide margin (PR-AUC 0.93 vs 0.40), rejecting slow non-fishing transits and catching fast working passes.

## Why this was flagged

_mean per-position SHAP (fishing class) over the incident's fishing positions._

| feature | mean value | mean SHAP |
|---|---:|---:|
| `speed` | 9.050 | -0.074 |
| `speed_roll_mean` | 9.340 | -0.072 |
| `distance_from_shore` | 130173.609 | +0.062 |
| `hour_sin` | 0.938 | +0.051 |
| `distance_from_port` | 130645.172 | +0.050 |

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
- **Integrity (SHA-256 of canonical facts):** `7ebe26ff6f3df7004877bd6bb3aa899770a756d1b9007d50906cbc897ff9a054`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
