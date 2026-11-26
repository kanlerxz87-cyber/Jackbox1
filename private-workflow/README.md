# Private workflow: use the parcel location without putting it in Git

Public code, private data. These scripts turn the real parcel location into a **consistent set of census tracts** and a **blank hazard checklist**, entirely on your own machine. The location, the tract list and every per-tract result stay in the git-ignored `private/` folder. Only an aggregate with no tract IDs may be shared, and only after you review it.

Session `S-f6ebb740`, task F6-05. Standard library only (Python 3.9+). Documentation page: `outlook/workflow.html`.

## What never happens

- The location is never written to a tracked file, printed, or put in a pull request.
- The scripts refuse to run unless `git check-ignore private/` says the folder is ignored, and refuse to write outside it.
- A public aggregate needs at least 10 tracts and carries no tract IDs, distances or coordinates.
- Your Census API key is read from the `CENSUS_API_KEY` environment variable and is never printed or saved.

## One-time setup

1. Copy `private-workflow/private.example/location.example.json` to `private/location.json` and put in the latitude and longitude as plain numbers.
2. Download the public **Gazetteer census tracts file** (national zip, pipe-delimited text with internal-point coordinates, based on 2020 tracts) from the Census page <https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html>. Opening that page and the format were verified on 2026-11-26.
3. For step 3, request a free Census API key at <https://api.census.gov/data/key_signup.html>. A key is required (verified 2026-11-26).

## Steps

| Step | Command | What leaves the machine |
|---|---|---|
| 1 | `python3 private-workflow/step1_trade_area_tracts.py --gazetteer PATH --county 06037 --radii 1,3,5` | nothing |
| 2 (optional) | `python3 private-workflow/step2_confirm_tract.py` (dry run) or add `--online` | dry run: nothing. `--online`: the coordinates reach a Census server, which may log them |
| 3 | `CENSUS_API_KEY=YOUR_KEY python3 private-workflow/step3_acs_tracts.py --vintage 2024` | a whole-county request plus your key; no location |
| 4 | `python3 private-workflow/step4_hazard_checklist.py` | nothing (writes a blank checklist) |
| test | `python3 private-workflow/selftest.py` | nothing (synthetic data, no network) |

Outputs appear in `private/out/`. Share only `public_aggregate_*.json` after reading it.

## Method notes and limits

- **Tract choice is an approximation.** Step 1 selects a tract when its internal point is inside the ring. A tract can overlap a ring without its internal point being inside. For the containing tract use step 2 or the Census Geocoder page by hand.
- **Consistent geography.** Compare two ACS vintages only when the tract IDs match. Step 3 reports tracts missing from the second vintage and does not guess a crosswalk. Use the Census tract relationship files when boundaries changed.
- **Medians are not additive.** The aggregate reports the spread of tract medians (minimum, quartiles, maximum), clearly labelled, not an area median. Counts are summed and margins of error combined by root of sum of squares.
- **Reliability.** The share of tracts whose median-income coefficient of variation is above 0.30 is reported. That 0.30 is this project's warning rule, not a Census threshold.
- **Sentinel values.** The very large negative numbers the Census uses to mark missing medians are treated as missing and never interpreted.
- **Variable checks.** Before data are trusted, each variable's concept and label are fetched from the Census metadata and compared with what the script expects. Two labels were checked by hand on 2026-11-26 (B01003_001E 'Total Population'; B25003_003E 'Renter occupied'); B19013 is 'Median Household Income'.
- **Hazards are manual by design.** The FEMA flood service returned HTTP 500 and the CAL FIRE service on `services.gis.ca.gov` still lists 2007 and DRAFT layers, so no automated hazard answer is offered. See flags OL-F07 and OL-F08.

## What this does not do

It does not geocode a street address, does not fetch planning, traffic, school or competitor evidence (those need the same private location and are listed as open items on the Questions page), and does not decide anything about selling or renewing.
