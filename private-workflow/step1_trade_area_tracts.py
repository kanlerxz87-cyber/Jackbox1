#!/usr/bin/env python3
"""Step 1: choose trade-area census tracts OFFLINE from the public Census Gazetteer file.

Nothing is sent anywhere. The tract is selected by its internal point (an approximation of
'tract inside the ring'), which is stated in the metadata file.

  python3 private-workflow/step1_trade_area_tracts.py --gazetteer PATH --county 06037 [--radii 1,3,5]
"""
import argparse
import csv
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pw_common as pw  # noqa: E402


def select_tracts(rows, lat, lon, radii, county_prefix=None):
    """Return [(geoid, distance_miles, ring_miles)] sorted by distance for tracts inside the largest radius."""
    if not rows:
        pw.die("the gazetteer file has no rows")
    gcol = pw.pick_col(rows[0], "GEOID", "GEOID_TRACT")
    latc = pw.pick_col(rows[0], "INTPTLAT")
    lonc = pw.pick_col(rows[0], "INTPTLONG", "INTPTLON")
    if not (gcol and latc and lonc):
        pw.die("could not find GEOID, INTPTLAT and INTPTLONG columns in the gazetteer file")
    radii = sorted(radii)
    chosen = []
    for r in rows:
        geoid = r[gcol].strip()
        if county_prefix and not geoid.startswith(county_prefix):
            continue
        try:
            d = pw.haversine_miles(lat, lon, float(r[latc]), float(r[lonc]))
        except ValueError:
            continue
        if d <= radii[-1]:
            ring = next(x for x in radii if d <= x)
            chosen.append((geoid, round(d, 3), ring))
    chosen.sort(key=lambda t: t[1])
    return chosen


def run(gazetteer, county, radii, paths=None, quiet=False):
    radii = sorted(float(r) for r in radii)
    paths = paths or pw.Paths()
    pw.require_private_ignored(paths)
    lat, lon = pw.load_location(paths)
    rows = pw.read_gazetteer(gazetteer)
    chosen = select_tracts(rows, lat, lon, radii, county)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["GEOID", "distance_mi", "ring_mi"])
    w.writerows(chosen)
    pw.write_private(paths, "out/trade_area_tracts.csv", buf.getvalue())
    counts = {str(r): sum(1 for _, _, ring in chosen if ring <= r) for r in sorted(radii)}
    meta = {"method": "tract internal point (Gazetteer INTPTLAT/INTPTLONG) within ring distance; approximation of boundary overlap",
            "radii_mi": sorted(radii), "county_prefix": county, "tract_counts_cumulative": counts,
            "gazetteer_file": Path(gazetteer).name, "note": "contains no coordinates; the tract list file next to it is private"}
    pw.write_private(paths, "out/trade_area_meta.json", json.dumps(meta, indent=1) + "\n")
    if not quiet:
        print("tracts selected (cumulative by ring, miles): " + ", ".join(f"{k}: {v}" for k, v in counts.items()))
        small = [k for k, v in counts.items() if v < pw.MIN_TRACTS_PUBLIC]
        if small:
            print(f"note: ring(s) {', '.join(small)} hold fewer than {pw.MIN_TRACTS_PUBLIC} tracts and cannot back a public aggregate")
        print("written to private/out/ (git-ignored)")
    return chosen, counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gazetteer", required=True, help="Gazetteer tracts file (.zip or .txt) downloaded from census.gov")
    ap.add_argument("--county", default=None, help="state+county FIPS prefix, for example 06037")
    ap.add_argument("--radii", default="1,3,5", help="comma-separated ring radii in miles")
    a = ap.parse_args(argv)
    try:
        radii = [float(x) for x in a.radii.split(",") if x.strip()]
    except ValueError:
        pw.die("--radii must be numbers")
    if not radii or min(radii) <= 0:
        pw.die("--radii must be positive numbers")
    run(a.gazetteer, a.county, radii)


if __name__ == "__main__":
    main()
