# Incident `live_ais__d6e261313c54b0`

- **MPA:** AIS disabling (going dark)
- **Severity:** HIGH (foreign vessel, no authorization on record)
- **EEZ:** Brazilian Exclusive Economic Zone (Brazil) -- FOREIGN-flagged vessel
- **Authorization:** No authorization on record
- **Vessel:** 🇸🇬 EAGLE PAULINIA  ·  **signal:** AIS gap
- **When (UTC):** 2026-06-25T13:59:46.000Z → 2026-06-26T10:00:55.000Z
- **Gap:** 20.0 h dark, 108.0 nm offshore
- **Where:** -24.785, -42.510

## Why this was flagged

_GFW Events gaps dataset (satellite AIS).._

- went dark 108 nm offshore for 20 h
- satellite-confirmed AIS gap (GFW Events)

## Caveats

- AIS gaps can be reception loss, not always intentional disabling.
- The position is where AIS dropped; the path while dark is unknown.
- An inspection lead from GFW Events, not proof of illegal activity.

## Provenance & integrity

- NOAA Marine Cadastre AIS (marinecadastre.gov/ais (vessel positions)). US public domain.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `b9f811b286114aba845fe143095e54c2df5a0c9ae4bb7a525021113eea9b6a76`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
