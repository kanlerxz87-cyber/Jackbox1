#!/usr/bin/env python3
"""Step 4: write a BLANK private hazard checklist for the real parcel. Nothing is queried.

Why no automated lookup: the FEMA flood service failed (HTTP 500) when tested on 2026-11-26 and the CAL FIRE
service on services.gis.ca.gov still lists 2007 and DRAFT layers, so an automated answer could be wrong or stale.
Fill the checklist by hand from the official viewers, record the map date, and keep it in private/.

  python3 private-workflow/step4_hazard_checklist.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pw_common as pw  # noqa: E402

ROWS = [
    ("Flood", "FEMA Map Service Center", "https://msc.fema.gov/portal/home", "flood zone code, panel number, effective date"),
    ("Wildfire", "State Fire Marshal / CAL FIRE hazard severity zone viewer", "https://osfm.fire.ca.gov", "zone class, responsibility area, map date"),
    ("Earthquake: fault, liquefaction, landslide", "California Geological Survey EQ Zapp", "https://www.conservation.ca.gov/cgs/geohazards/eq-zapp", "each zone flag (yes/no) and map date"),
    ("Insurance", "policy documents and broker", "none", "perils covered, earthquake included or not, limits, deductibles, vacancy conditions"),
    ("Lease allocation", "lease abstract", "none", "who insures, rent abatement, termination rights, rebuild obligation"),
]


def build():
    lines = ["# Parcel hazard checklist (PRIVATE - never commit, never publish the filled version)", "",
             "Nothing here was queried. Fill each result by hand and record the map date.", "",
             "| Peril | Where to look | Link | What to record | Result | Date checked | Checked by |", "|---|---|---|---|---|---|---|"]
    for peril, where, link, rec in ROWS:
        lines.append(f"| {peril} | {where} | {link} | {rec} |  |  |  |")
    lines += ["", "Publishing rule: only a yes/no 'screened' flag per peril may be shared publicly, never the zone values.", ""]
    return "\n".join(lines)


def run(paths=None):
    paths = paths or pw.Paths()
    pw.require_private_ignored(paths)
    p = pw.write_private(paths, "out/hazard_checklist.md", build())
    print("blank checklist written to private/out/hazard_checklist.md (nothing was queried)")
    return p


if __name__ == "__main__":
    run()
