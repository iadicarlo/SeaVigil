#!/usr/bin/env bash
# Convert a WDPA / Protected Planet export into NON-EXTRACTABLE vector tiles
# (PMTiles) for the SeaVigil web map.
#
# WHY: the UNEP-WCMC / WDPA license forbids redistributing the boundaries through
# an interactive web map that lets users DOWNLOAD the source polygons. Raw
# .geojson is downloadable; vector tiles are not (they ship rendered tile pyramids,
# not the source geometry). You must ALSO (a) obtain written sign-off from
# UNEP-WCMC for a public tool, (b) keep the IUCN/UNEP-WCMC citation + a
# protectedplanet.net link visible, and (c) keep the tool non-commercial.
# See docs/DEPLOY.md.
#
# Requires: mapshaper (npm i -g mapshaper), tippecanoe, pmtiles
#   (brew install tippecanoe; brew install pmtiles, or go install).
#
# Usage: scripts/wdpa_to_pmtiles.sh path/to/wdpa_marine.geojson web/data/mpas.pmtiles

set -euo pipefail

IN="${1:?usage: wdpa_to_pmtiles.sh <input.geojson> <output.pmtiles>}"
OUT="${2:?usage: wdpa_to_pmtiles.sh <input.geojson> <output.pmtiles>}"

for tool in mapshaper tippecanoe pmtiles; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "ERROR: '$tool' not found. Install it first (see header)." >&2
    exit 1
  }
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[1/3] simplify polygons (keep shapes, drop vertices)…"
mapshaper "$IN" -simplify 8% keep-shapes -o "$TMP/simplified.geojson"

echo "[2/3] tile (zoom 0–8)…"
tippecanoe -o "$TMP/mpas.mbtiles" -l mpas -z8 -Z0 \
  --drop-densest-as-needed --force "$TMP/simplified.geojson"

echo "[3/3] pack to PMTiles → $OUT…"
pmtiles convert "$TMP/mpas.mbtiles" "$OUT"

echo "Done: $OUT"
echo "Point the MapLibre 'mpas' source at pmtiles://./data/$(basename "$OUT") (needs the pmtiles JS protocol plugin)."
