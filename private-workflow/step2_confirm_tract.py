#!/usr/bin/env python3
"""Step 2 (optional): confirm the containing census tract with ONE request to the Census Geocoder.

Default is a DRY RUN that prints a masked request and sends nothing. With --online the
coordinates are sent to a Census Bureau server, which may log them. Skip this step if that matters.

  python3 private-workflow/step2_confirm_tract.py            # dry run
  python3 private-workflow/step2_confirm_tract.py --online   # one request
"""
import argparse
import csv
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pw_common as pw  # noqa: E402

BASE = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
PARAMS = "benchmark=Public_AR_Current&vintage=Current_Current&format=json"


def build_url(lat, lon, masked=False):
    x, y = ("REDACTED", "REDACTED") if masked else (f"{lon}", f"{lat}")
    return f"{BASE}?x={x}&y={y}&{PARAMS}"


def parse_tract(obj):
    """Shape verified 2026-11-26: result.geographies['Census Tracts'][0].GEOID"""
    try:
        return obj["result"]["geographies"]["Census Tracts"][0]["GEOID"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("response has no census tract")


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "private-workflow/1.0 (local use)"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed https host)
        return json.loads(r.read().decode("utf-8"))


def run(online=False, paths=None, fetch=http_get_json):
    paths = paths or pw.Paths()
    pw.require_private_ignored(paths)
    lat, lon = pw.load_location(paths)
    if not online:
        print("dry run: nothing sent. The request would be:")
        print("  " + build_url(lat, lon, masked=True))
        print("add --online to send ONE request; the coordinates would reach a Census server")
        return None
    geoid = parse_tract(fetch(build_url(lat, lon)))
    rec = {"tract_geoid": geoid, "source": "Census Geocoder (geographies by coordinates)", "benchmark": "Public_AR_Current",
           "vintage": "Current_Current", "retrieved": date.today().isoformat()}
    pw.write_private(paths, "out/parcel_tract.json", json.dumps(rec, indent=1) + "\n")
    in_set = None
    f = paths.out / "trade_area_tracts.csv"
    if f.exists():
        with open(f, encoding="utf-8") as fh:
            in_set = any(r["GEOID"] == geoid for r in csv.DictReader(fh))
    print("tract confirmed and stored privately" + ("" if in_set is None else f"; inside the step 1 tract set: {'yes' if in_set else 'NO - review the rings'}"))
    return geoid


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--online", action="store_true", help="actually send the single request")
    a = ap.parse_args(argv)
    run(online=a.online)


if __name__ == "__main__":
    main()
