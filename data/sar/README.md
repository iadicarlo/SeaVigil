# SAR vessel detections (dark fleet)

`sample_sar_detections.geojson` is a **synthetic** sample so the dark-fleet path runs with no
account or download. Each detection has `length_m`, `fishing_score`, and `matched_to_ais`
(an AIS-matched detection is a *broadcasting* vessel; an **unmatched** one is **dark**).

**Do not treat the sample as real detections.**

The published showcase no longer uses this synthetic sample: `scripts/swap_real_sar.py`
selects a temporally and spatially diverse subset of **real** GFW Sentinel-1 dark-vessel
detections (from the gitignored `gfw_sar_detections.geojson`) that fall inside the MPAs, and
ships only the derived in-MPA dossiers (not the raw detection database), with attribution.

For real use, export **point-level Sentinel-1 SAR vessel detections** - with `length_m` and
the fishing/presence/matching scores - from the
[GFW Data Download Portal](https://globalfishingwatch.org/our-apis/) (the data behind
Paolo et al., *Nature* 2024). The 4Wings *API* only returns gridded counts, not these fields,
so the **Portal** is the right source for per-detection dossiers.

**License: CC BY-NC 4.0 (non-commercial).** Consuming GFW SAR detections binds any built-on
tool to non-commercial use (unlike the CC BY 4.0 *training* labels). A free GFW account/token
is required.

Why these get a different dossier than AIS incidents: a SAR detection is a single radar blip
with **no movement track and no AIS identity**, so the per-position SHAP model cannot run on
it. Its rationale is attribute-based (length + fishing-score + not-broadcasting + inside-MPA),
not a SHAP "why". See `docs/DESIGN.md` §6.5.
