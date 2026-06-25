# SeaVigil web map

A static [MapLibre GL](https://maplibre.org/) map of fishing-in-MPA incidents and dark-vessel
SAR detections. It loads only static files (`data/*.geojson`) — **no server, no API token, no
GFW call from the browser** — so it deploys to GitHub Pages as-is.

## Build the data

```bash
uv run python -m seavigil.alert --scope all --sample-sar   # produces results/incidents/
uv run python -m seavigil.site                             # -> web/data/*.geojson
```

`seavigil.site` converts `results/incidents/incidents.json` + the MPA polygons into
`web/data/incidents.geojson` and `web/data/mpas.geojson`.

## Preview locally

```bash
python -m http.server -d web 8000   # then open http://localhost:8000
```

## Deploy

`.github/workflows/pages.yml` publishes `web/` to GitHub Pages on push to `main`. The data is
**precomputed and committed** (the precompute-and-ship-static pattern); a production refresh
would be a scheduled GitHub Actions job that pulls fresh GFW data (token in Actions secrets)
and re-runs `seavigil.alert` + `seavigil.site`.

## Caveats baked into the demo

- **MPA boundaries** here are the approximate sample boxes. Real **WDPA** boundaries are
  non-commercial and **must not** be shipped as downloadable GeoJSON — convert them to
  non-extractable vector tiles (PMTiles) before deploying with real limits.
- The basemap uses OpenStreetMap raster tiles (no key); for production use a proper tile
  provider per OSM's usage policy.
- Markers are *apparent* fishing / *dark* detections inside MPAs — inspection leads, not proof.
