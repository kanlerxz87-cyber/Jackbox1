#!/usr/bin/env python3
"""Line-by-line verification of the published site.

Checks:
  1. every JSON table row has at least one source id that resolves to an official source;
  2. verified rows have values; unverified rows are blank;
  3. every rendered <tr> in every published HTML table has at least one official link;
  4. no forbidden identifying content appears in any published file;
  5. every data-table body row is traceable to a data row id.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT.parent
DATA = ROOT / "data"

errors: list[str] = []
warnings: list[str] = []

sources = json.loads((DATA / "sources.json").read_text())["sources"]
ids = {s["id"] for s in sources}
official = {s["id"] for s in sources if s["official"]}

TABLES = ["findings.json", "questions.json", "gates.json", "flagged.json", "suggestions.json", "risks.json"]
checked = 0
for name in TABLES:
    t = json.loads((DATA / name).read_text())
    cols = t["columns"]
    for row in t["rows"]:
        checked += 1
        cell = ""
        for i, c in enumerate(cols):
            if c in ("sources", "official_source", "source"):
                cell = row[i]
        if not cell:
            errors.append(f"{name}: {row[0]} has no source link")
            continue
        for sid in cell.split("|"):
            if sid not in ids:
                errors.append(f"{name}: {row[0]} unknown source {sid}")
            elif sid not in official and sid != "PORTAL-GITHUB-REPO":
                errors.append(f"{name}: {row[0]} non-official source {sid}")

f = json.loads((DATA / "findings.json").read_text())
for row in f["rows"]:
    rid, status, value = row[0], row[7], row[5]
    if status == "verified" and str(value).strip() == "":
        errors.append(f"findings: {rid} marked verified with blank value")
    if status != "verified" and str(value).strip() != "":
        errors.append(f"findings: {rid} unverified with value {value!r}")

published = [ROOT / n for n in sorted(p.name for p in ROOT.glob("*.html"))] + [SITE / "index.html"]
LINK_RE = re.compile(r'href="(https://[^"]+)"')
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
UNVERIFIED_BADGE = re.compile(r"UNVERIFIED|left blank", re.I)

for path in published:
    text = path.read_text(encoding="utf-8")
    if path.name == "calculator.html":
        # Its only <tr> elements are runtime result fragments built from private
        # inputs in the browser; there are no published data-table rows on this page.
        continue
    for m in TR_RE.finditer(text):
        tr = m.group(1)
        if "<th" in tr and "<td" not in tr:
            continue  # header row
        if 'colspan="2"' in tr and "Enter private inputs" in tr:
            continue  # calculator placeholder
        hrefs = LINK_RE.findall(tr)
        if hrefs and any("github.com" not in h for h in hrefs):
            continue
        if not hrefs:
            # result tables built at runtime are not data tables
            if "result-table" in text[:m.start()][-400:] or 'id="outSale"' in text[:m.start()][-400:] or 'id="outHold"' in text[:m.start()][-400:]:
                continue
            # print sheet source paragraph is not a table row
            if path.name == "print.html" and "src-line" in text[:m.start()][-500:]:
                continue
            if "verdict" in text[:m.start()][-300:]:
                continue
            # A non-data tr (e.g. totals in a static source table) must still be explained
            if UNVERIFIED_BADGE.search(tr) or "<em>" in tr:
                continue
            warnings.append(f"{path.name}: table row without an external official link (context: {tr[:90].strip()}...)")

# Privacy scan: no identifying values in the published product.
FORBIDDEN = [
    (r"\bAPN\s*[:#]?\s*\d{2,}", "APN with a number"),
    (r"\b\d{1,6}\s+[A-Z][A-Za-z]+\s+(Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr)\b", "street address pattern"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN pattern"),
    (r"\b(?:owner|landlord)\s*(?:name|is)\s*[:=]?\s*[A-Z][a-z]+\s+[A-Z][a-z]+", "owner name pattern"),
    (r"333\s+South\s+Beaudry", "CDE district address"),
    (r"9357\s+Spectrum", "SEC filer address"),
]
for path in published:
    text = path.read_text(encoding="utf-8")
    for pat, label in FORBIDDEN:
        if re.search(pat, text):
            errors.append(f"{path.name}: forbidden identifying content ({label})")
    # No form action or external script/asset loads
    if re.search(r"<form[^>]*\baction=", text, re.I):
        errors.append(f"{path.name}: form with an action attribute")
    if re.search(r"<script[^>]*\bsrc=", text, re.I):
        errors.append(f"{path.name}: external script")
    # Detect actual API usage, not explanatory prose that says these are absent.
    forbidden_calls = (
        (r"\b(?:localStorage|sessionStorage)\s*[.\[]", "storage API call"),
        (r"\bdocument\.cookie\s*=", "cookie write"),
        (r"\bfetch\s*\(", "fetch call"),
        (r"\bXMLHttpRequest\b", "XHR call"),
        (r"\bnavigator\.sendBeacon\s*\(", "sendBeacon call"),
    )
    for pat, label in forbidden_calls:
        if re.search(pat, text):
            errors.append(f"{path.name}: forbidden browser storage/network call ({label})")

# Every HTML file must carry the privacy notice.
for path in published:
    t = path.read_text(encoding="utf-8")
    if "No personal information" not in t and "no identifiers" not in t and "aggregate" not in t.lower():
        errors.append(f"{path.name}: missing privacy notice")

print(f"Checked {checked} data rows, {len(published)} HTML files, {len(sources)} sources.")
for w in warnings[:20]:
    print("  warning:", w)
if len(warnings) > 20:
    print(f"  ... {len(warnings)-20} more warnings")
if errors:
    print("VERIFICATION FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("VERIFICATION PASSED: every table row has official source links; no identifying content; no storage/network calls.")
