# Incident `live_ais__2ea3a25182424d`

- **MPA:** AIS disabling (going dark)
- **Severity:** HIGH (foreign vessel, no authorization on record)
- **EEZ:** Saudi Arabian Exclusive Economic Zone (Saudi Arabia) -- FOREIGN-flagged vessel
- **Authorization:** No authorization on record
- **Vessel:** 🇱🇷 TILOS I  ·  **signal:** AIS gap
- **When (UTC):** 2026-06-25T16:21:22.000Z → 2026-06-26T04:22:39.000Z
- **Gap:** 12.0 h dark, 68.0 nm offshore
- **Where:** 18.692, 39.660

## Why this was flagged

_GFW Events gaps dataset (satellite AIS).._

- went dark 68 nm offshore for 12 h
- satellite-confirmed AIS gap (GFW Events)

## Caveats

- AIS gaps can be reception loss, not always intentional disabling.
- The position is where AIS dropped; the path while dark is unknown.
- An inspection lead from GFW Events, not proof of illegal activity.

## Provenance & integrity

- NOAA Marine Cadastre AIS (marinecadastre.gov/ais (vessel positions)). US public domain.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `f66abf0e4bbcd60441dab6ad32b1b16ad104e2df7fc04855fdb24a713272cdb9`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
