# Incident `live_ais__f5fef908975f26`

- **MPA:** AIS disabling (going dark)
- **Severity:** HIGH (foreign vessel, no authorization on record)
- **EEZ:** Australian Exclusive Economic Zone (Australia) -- FOREIGN-flagged vessel
- **Authorization:** No authorization on record
- **Vessel:** 🇮🇸 SOUTH SEAS 01-99%  ·  **signal:** AIS gap
- **When (UTC):** 2026-06-24T19:31:08.000Z → 2026-06-26T02:37:09.000Z
- **Gap:** 31.1 h dark, 50.0 nm offshore
- **Where:** -38.420, 150.693

## Why this was flagged

_GFW Events gaps dataset (satellite AIS).._

- went dark 50 nm offshore for 31 h
- satellite-confirmed AIS gap (GFW Events)

## Caveats

- AIS gaps can be reception loss, not always intentional disabling.
- The position is where AIS dropped; the path while dark is unknown.
- An inspection lead from GFW Events, not proof of illegal activity.

## Provenance & integrity

- NOAA Marine Cadastre AIS (marinecadastre.gov/ais (vessel positions)). US public domain.
- WDPA / WD-OECM (World Database on Protected Areas) (UNEP-WCMC and IUCN (2026), June 2026). Protected Planet Terms of Use (non-commercial, display-only).
- Marine Regions Exclusive Economic Zones v12 (Flanders Marine Institute (2024), DOI 10.14284/632). CC BY 4.0.
- **Integrity (SHA-256 of canonical facts):** `e7fbc2f434863c2128596cc8248e3043a96cbad55888983163ccdc48c3cfaa30`
- **Evidence schema:** seavigil-evidence-1.0

_Apparent activity and an inspection lead, not proof of illegality. AIS and SAR evidence have known coverage gaps and spoofing risks; verify against authoritative sources before any enforcement action._
