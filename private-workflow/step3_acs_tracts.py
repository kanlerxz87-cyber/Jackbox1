#!/usr/bin/env python3
"""Step 3: ACS 5-year tract metrics for the step 1 tract set, with a public-safe aggregate.

The request goes to the Census API for a WHOLE COUNTY (never for the parcel); the tract set
is applied locally. Your Census API key is read from the CENSUS_API_KEY environment variable
and is never printed or written. Every variable label is checked against the Census metadata
before any data is trusted.

  CENSUS_API_KEY=... python3 private-workflow/step3_acs_tracts.py --vintage 2024 [--ring 3] [--compare-vintage 2019]
  python3 private-workflow/step3_acs_tracts.py --vintage 2024 --csv PATH      # offline: a CSV you downloaded
"""
import argparse
import csv
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pw_common as pw  # noqa: E402

# (variable stem, short name, expected concept text, expected label text or None)
VARS = [
    ("B01003_001", "population", "Total Population", None),
    ("B19013_001", "median_hh_income", "Median Household Income", None),
    ("B25003_001", "occupied_units", "Tenure", "Total"),
    ("B25003_003", "renter_occupied", "Tenure", "Renter occupied"),
    ("B25064_001", "median_gross_rent", "Median Gross Rent", None),
    ("B25077_001", "median_home_value", "Median Value", None),
]
ADDITIVE = ["population", "occupied_units", "renter_occupied"]
MEDIANS = ["median_hh_income", "median_gross_rent", "median_home_value"]
CV_WARN = 0.30   # this project's warning rule for a tract median, NOT a Census-published threshold


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "private-workflow/1.0 (local use)"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (fixed https host)
        return json.loads(r.read().decode("utf-8"))


def variable_url(vintage, stem):
    return f"https://api.census.gov/data/{vintage}/acs/acs5/variables/{stem}E.json"


def verify_variables(vintage, fetch=http_get_json):
    """Refuse to continue if any variable's concept or label differs from what this script expects."""
    for stem, short, concept, label in VARS:
        meta = fetch(variable_url(vintage, stem))
        if concept.lower() not in str(meta.get("concept", "")).lower():
            pw.die(f"variable {stem}E concept mismatch for {vintage}: expected text '{concept}'")
        if label and label.lower() not in str(meta.get("label", "")).lower():
            pw.die(f"variable {stem}E label mismatch for {vintage}: expected text '{label}'")


def api_url(vintage, state, county, key=None, masked=True):
    get = "NAME," + ",".join(f"{s}E,{s}M" for s, *_ in VARS)
    k = "REDACTED" if masked or not key else key
    return (f"https://api.census.gov/data/{vintage}/acs/acs5?get={get}&for=tract:*&in=state:{state}&in=county:{county}&key={k}")


def records_from_api_rows(rows):
    """API rows (list of lists with a header) -> {geoid: {short: (estimate, moe)}}"""
    head = rows[0]
    out = {}
    for r in rows[1:]:
        d = dict(zip(head, r))
        geoid = f'{d["state"]}{d["county"]}{d["tract"]}'
        out[geoid] = {short: (pw.clean_num(d.get(f"{stem}E")), pw.clean_num(d.get(f"{stem}M"))) for stem, short, *_ in VARS}
    return out


def records_from_csv(path):
    rows = pw.read_delimited_text(Path(path).read_text(encoding="utf-8", errors="replace"))
    out = {}
    for d in rows:
        geoid = d.get("GEOID") or d.get("geoid")
        if not geoid:
            continue
        out[geoid.strip()] = {short: (pw.clean_num(d.get(f"{stem}E")), pw.clean_num(d.get(f"{stem}M"))) for stem, short, *_ in VARS}
    return out


def read_ring(paths, ring):
    f = pw.private_path(paths, "out", "trade_area_tracts.csv")
    if not f.exists():
        pw.die("run step 1 first (private/out/trade_area_tracts.csv is missing)")
    with open(f, encoding="utf-8") as fh:
        return [r["GEOID"] for r in csv.DictReader(fh) if float(r["ring_mi"]) <= ring]


def default_ring(paths):
    f = pw.private_path(paths, "out", "trade_area_meta.json")
    if not f.exists():
        pw.die("run step 1 first (private/out/trade_area_meta.json is missing)")
    meta = json.loads(f.read_text(encoding="utf-8"))
    for r, n in sorted(((float(k), v) for k, v in meta["tract_counts_cumulative"].items())):
        if n >= pw.MIN_TRACTS_PUBLIC:
            return r
    pw.die(f"no ring holds {pw.MIN_TRACTS_PUBLIC} tracts; widen --radii in step 1")


def aggregate(records, geoids):
    """Aggregate the chosen tracts. The result holds no tract ids and no coordinates."""
    found = [records[g] for g in geoids if g in records]
    out = {"tracts_requested": len(geoids), "tracts_found": len(found), "tracts_missing_in_vintage": len(geoids) - len(found)}
    sums = {}
    for name in ADDITIVE:
        pairs = [v[name] for v in found if v[name][0] is not None]
        est = sum(p[0] for p in pairs)
        moes = [p[1] for p in pairs if p[1] is not None]
        sums[name] = {"sum": est, "tracts_with_value": len(pairs),
                      "moe_rss": round(pw.sum_moe(moes), 1) if len(moes) == len(pairs) and pairs else None}
    out["additive_counts"] = sums
    both = [v for v in found if v["renter_occupied"][0] is not None and v["occupied_units"][0] not in (None, 0)]
    occ = sum(v["occupied_units"][0] for v in both)
    out["renter_share"] = round(sum(v["renter_occupied"][0] for v in both) / occ, 4) if occ else None
    med = {}
    for name in MEDIANS:
        vals = sorted(v[name][0] for v in found if v[name][0] is not None)
        med[name] = {"tracts_with_value": len(vals), "min": vals[0] if vals else None, "p25": pw.quantile(vals, 0.25),
                     "median_of_tract_medians": pw.quantile(vals, 0.5), "p75": pw.quantile(vals, 0.75), "max": vals[-1] if vals else None}
    out["tract_median_spread"] = med
    cvs = [pw.cv(*v["median_hh_income"]) for v in found if v["median_hh_income"][0] is not None]
    cvs = [c for c in cvs if c is not None]
    out["median_income_low_reliability_share"] = round(sum(1 for c in cvs if c > CV_WARN) / len(cvs), 3) if cvs else None
    out["notes"] = ["Counts are summed; margins of error use the root of the sum of squares.",
                    "Medians cannot be added across tracts: the spread of tract medians is shown, not an area median.",
                    f"Low reliability = coefficient of variation above {CV_WARN} (this project's rule, not a Census threshold).",
                    "Census annotation sentinel values are treated as missing."]
    return out


def consistency(geoids, rec_a, rec_b):
    both = sum(1 for g in geoids if g in rec_a and g in rec_b)
    only_a = sum(1 for g in geoids if g in rec_a and g not in rec_b)
    msg = ("tract geography matches across both vintages" if only_a == 0 else
           "tract geography differs between vintages: do not compute change over the whole set; use the Census tract relationship files")
    return {"in_both": both, "only_in_first": only_a, "message": msg}


def per_tract_csv(records, geoids):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["GEOID"] + [f"{s}_{k}" for _, s, *_ in VARS for k in ("estimate", "moe")])
    for g in geoids:
        if g in records:
            w.writerow([g] + [x for _, s, *_ in VARS for x in records[g][s]])
    return buf.getvalue()


def load_vintage(vintage, state, county, key, csv_path, fetch, verify):
    if csv_path:
        return records_from_csv(csv_path)
    if not key:
        pw.die("set CENSUS_API_KEY (free key: https://api.census.gov/data/key_signup.html) or pass --csv")
    if verify:
        verify_variables(vintage, fetch)
    return records_from_api_rows(fetch(api_url(vintage, state, county, key, masked=False)))


def run(vintage, ring=None, compare=None, csv_path=None, compare_csv=None, county=None, paths=None, fetch=http_get_json, verify=True, env=None):
    paths = paths or pw.Paths()
    pw.require_private_ignored(paths)
    key = (env if env is not None else os.environ).get("CENSUS_API_KEY")
    ring = ring or default_ring(paths)
    geoids = read_ring(paths, ring)
    pw.public_guard(len(geoids))
    st, co = (county[:2], county[2:5]) if county else (geoids[0][:2], geoids[0][2:5])
    rec = load_vintage(vintage, st, co, key, csv_path, fetch, verify)
    agg = aggregate(rec, geoids)
    result = {"vintage": f"ACS {vintage} 5-year", "ring_miles": ring, "aggregate": agg}
    if compare or compare_csv:
        rec2 = load_vintage(compare or "csv", st, co, key, compare_csv, fetch, verify)
        result["consistency_with_comparison_vintage"] = consistency(geoids, rec, rec2)
        result["comparison_aggregate"] = aggregate(rec2, geoids)
        result["comparison_vintage"] = f"ACS {compare or 'csv'} 5-year"
    pw.write_private(paths, f"out/acs_tracts_{vintage}.csv", per_tract_csv(rec, geoids))
    pw.write_private(paths, f"out/public_aggregate_{vintage}_ring{ring:g}.json", json.dumps(result, indent=1) + "\n")
    print(f"aggregate written for {agg['tracts_found']} of {agg['tracts_requested']} tracts (ring {ring:g} mi). Review it before sharing; it holds no tract ids.")
    if agg["tracts_missing_in_vintage"]:
        print(f"note: {agg['tracts_missing_in_vintage']} tract(s) absent from this vintage; geography may differ")
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vintage", required=True, help="ACS 5-year end year, for example 2024")
    ap.add_argument("--ring", type=float, default=None, help="ring radius in miles (default: smallest ring with enough tracts)")
    ap.add_argument("--compare-vintage", default=None)
    ap.add_argument("--csv", default=None, help="offline: CSV with GEOID and variable columns such as B01003_001E")
    ap.add_argument("--compare-csv", default=None)
    ap.add_argument("--county", default=None, help="state+county FIPS, default taken from the tract set")
    ap.add_argument("--no-verify-variables", action="store_true", help="not recommended")
    a = ap.parse_args(argv)
    run(a.vintage, a.ring, a.compare_vintage, a.csv, a.compare_csv, a.county, verify=not a.no_verify_variables)


if __name__ == "__main__":
    main()
