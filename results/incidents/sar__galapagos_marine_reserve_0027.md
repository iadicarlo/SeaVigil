# Dark-vessel detection `sar__galapagos_marine_reserve_0027`

- **MPA:** Galápagos Marine Reserve
- **Severity:** HIGH (no-take / national-park protection)  ·  boundary sample-approx-2024
- **EEZ:** Ecuadorian Exclusive Economic Zone (Galapagos) (Ecuador)
- **Vessel:** (dark -- no AIS identity)  ·  **source:** SAR (dark)
- **When (UTC):** 2024-01-02T11:42:31Z
- **Length:** n/a  ·  **broadcasting AIS:** no (dark)  ·  **GFW fishing-score:** n/a (Portal-only)
- **Where:** -0.150, -90.630

## Why this was flagged

_SAR detection attributes (no AIS track or identity; not SHAP-explainable)._

- inside MPA: Galápagos Marine Reserve
- not broadcasting AIS (dark vessel)
- satellite detections in window: 1

## Could be innocent

A radar contact with no AIS may be a vessel not required to broadcast, sea clutter, or fixed infrastructure; treat as a lead to confirm.

## Caveats

- Dark vessel: detected by satellite SAR but not broadcasting AIS.
- Not SHAP-explainable -- a SAR detection has no movement track to attribute.
- length_m and fishing_score are GFW model estimates from imagery, not ground truth.
- MPA boundary may be approximate; verify against official WDPA limits.
- An inspection lead, not courtroom evidence.

## Provenance & integrity

- Global Fishing Watch Sentinel-1 SAR vessel detections (Paolo et al., Nature 2024). CC BY-NC 4.0 (non-commercial).
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `5be30371ad710883f0e6daf61c23e8bce4eaee9039f2a369fab995d9a2097495`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
