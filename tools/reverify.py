#!/usr/bin/env python3
"""
Re-pull every machine-readable source in the registry and report whether the
published value still appears in the source payload.

This is the "re-runnable verification" the project promises: it is the difference
between a sourced figure and a remembered one.

It does NOT edit the registry. It prints a report so a human can decide whether a
change is a revision (update the row, re-date it) or a failure (remove the value).

NOTE: this script needs outbound internet. The build sandbox used to assemble the
site has no direct socket access (all research was done through a proxied page
fetcher), so this script is intended to be run from a normal machine or CI runner.

Usage:  python3 tools/reverify.py           # all rows with a JSON/CSV endpoint
        python3 tools/reverify.py LAB-01     # one row
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

import yaml

REGISTRY = Path(__file__).resolve().parent.parent / "data" / "registry.yaml"

# endpoints we can re-pull and parse mechanically
PULLABLE = re.compile(r"^https://(api\.bls\.gov|api\.censusreporter\.org|fred\.stlouisfed\.org|data\.sec\.gov)/")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "jackbox1-verification/1.0 (research; contact via repo)",
        "Accept": "application/json,text/csv,text/plain,*/*",
    })
    with urllib.request.urlopen(req, timeout=45) as fh:
        return fh.read().decode("utf-8", "replace")


def numbers_in(text: str) -> set[str]:
    """Every numeric token, normalised to digits-and-dot, so 4,662.8 and 4662.8 match."""
    out = set()
    for tok in re.findall(r"-?\d[\d,]*\.?\d*", text):
        t = tok.replace(",", "")
        if t.endswith("."):
            t = t[:-1]
        out.add(t)
        if "." in t:
            out.add(t.rstrip("0").rstrip("."))
    return out


def main(argv: list[str]) -> int:
    rows = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["rows"]
    only = set(argv)
    checked = matched = skipped = failed = 0

    for r in rows:
        if only and r["id"] not in only:
            continue
        if not r["url"] or not PULLABLE.match(r["url"]):
            skipped += 1
            continue
        if r["value"] == "":
            skipped += 1
            continue
        checked += 1
        try:
            payload = fetch(r["url"])
        except Exception as exc:  # network, 403, timeout
            failed += 1
            print(f"! {r['id']:8s} fetch failed: {exc}")
            continue

        # strings that are not numeric (ratings, classes) get a literal check
        digits = re.sub(r"[^\d.]", "", r["value"].split(" ")[0])
        if digits:
            hit = digits in numbers_in(payload)
        else:
            hit = r["value"].lower() in payload.lower()

        if hit:
            matched += 1
            print(f"✓ {r['id']:8s} {r['value']} — still present")
        else:
            failed += 1
            print(f"✗ {r['id']:8s} {r['value']} — NOT found in current payload; source may have revised")

    print(f"\n{checked} rows re-pulled · {matched} matched · {failed} mismatched or unreachable · {skipped} not machine-pullable")
    print("Rows that are not machine-pullable are HTML pages and filings; check them by hand via the links on sources.html.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
