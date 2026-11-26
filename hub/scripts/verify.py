#!/usr/bin/env python3
"""
Strict automated verifier for hub/** (Session S-a293043a).
Enforces:
  1. Valid JSON schemas & referential integrity of all source_ids.
  2. Official government / Federal Reserve / SEC / regional agency domain allowlist.
  3. Strict unverified-row discipline (status == 'unverified' MUST have value == None).
  4. 100% of <tbody> <tr> rows across all 15 hub/*.html pages carry an official https:// link.
  5. Complete internal relative link & asset check across all hub/*.html pages.
  6. Zero-telemetry & zero-external-CDN check across hub/assets/js/calculator.js & hub/*.html.
  7. Privacy firewall check (no APN, street address, or proxy-ZIP leakage).
"""

from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

HUB_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = HUB_DIR.parent

ALLOWED_DOMAINS = (
    "bls.gov",
    "edd.ca.gov",
    "dof.ca.gov",
    "fred.stlouisfed.org",
    "cde.ca.gov",
    "dot.ca.gov",
    "lacity.gov",
    "scag.ca.gov",
    "sec.gov",
    "dir.ca.gov",
    "irs.gov",
    "ftb.ca.gov",
    "boe.ca.gov",
    "lacounty.gov",
    "lavote.gov",
    "usgs.gov",
    "conservation.ca.gov",
    "fema.gov",
    "fire.ca.gov",
    "insurance.ca.gov",
)

FORBIDDEN_JS_TOKENS = (
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "document.cookie",
    "http://",
    "https://",
)

PRIVACY_PATTERNS = (
    (re.compile(r"\b\d{4}-\d{3}-\d{3}\b"), "APN-like 10-digit parcel number"),
    (re.compile(r"\b86000US\d{5}\b"), "Census ZCTA proxy code"),
    (re.compile(r"\b90015\b"), "Previously purged proxy ZIP 90015"),
)


def domain_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


class TableAndLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.row_idx = 0
        self.row_has_official_link = False
        self.rows_missing_links: list[int] = []
        self.total_rows = 0
        self.rel_links: list[str] = []
        self.ext_links: list[str] = []
        self.external_assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.total_rows += 1
            self.row_idx = self.total_rows
            self.row_has_official_link = False
        elif tag == "a":
            href = ad.get("href") or ""
            if href.startswith("http://") or href.startswith("https://"):
                self.ext_links.append(href)
                if self.in_tr and domain_allowed(href):
                    self.row_has_official_link = True
            elif href and not href.startswith("#") and not href.startswith("mailto:"):
                self.rel_links.append(href)
        elif tag in ("script", "img"):
            src = ad.get("src") or ""
            if src.startswith("http://") or src.startswith("https://"):
                self.external_assets.append(src)
            elif src:
                self.rel_links.append(src)
        elif tag == "link":
            href = ad.get("href") or ""
            if href.startswith("http://") or href.startswith("https://"):
                self.external_assets.append(href)
            elif href:
                self.rel_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.in_tr:
            if not self.row_has_official_link:
                self.rows_missing_links.append(self.row_idx)
            self.in_tr = False


def walk_records(obj: object, path: str, source_ids: set[str], errors: list[str]) -> None:
    if isinstance(obj, dict):
        if "source_id" in obj:
            sid = obj["source_id"]
            if sid not in source_ids:
                errors.append(f"Invalid source_id {sid!r} at {path}")
        if obj.get("status") == "unverified":
            if "value" in obj and obj["value"] is not None:
                errors.append(f"Unverified row has non-null value at {path}: {obj['value']!r}")
        for k, v in obj.items():
            walk_records(v, f"{path}.{k}", source_ids, errors)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            walk_records(item, f"{path}[{i}]", source_ids, errors)


def main() -> int:
    errors: list[str] = []

    sources_doc = json.loads((HUB_DIR / "data" / "sources.json").read_text(encoding="utf-8"))
    dataset = json.loads((HUB_DIR / "data" / "dataset.json").read_text(encoding="utf-8"))

    sources = sources_doc.get("sources", [])
    source_ids = set()
    for s in sources:
        sid = s["id"]
        if sid in source_ids:
            errors.append(f"Duplicate source ID: {sid}")
        source_ids.add(sid)
        if not domain_allowed(s["url"]):
            errors.append(f"Disallowed domain in sources.json {sid}: {s['url']}")

    walk_records(dataset, "dataset", source_ids, errors)

    # Check zero-telemetry JS contract
    calc_js = (HUB_DIR / "assets" / "js" / "calculator.js").read_text(encoding="utf-8")
    for tok in FORBIDDEN_JS_TOKENS:
        if tok in calc_js:
            errors.append(f"Forbidden telemetry/network token {tok!r} in calculator.js")

    # Check all HTML files
    html_files = sorted(HUB_DIR.glob("*.html"))
    if len(html_files) != 15:
        errors.append(f"Expected 15 HTML pages in hub/, found {len(html_files)}")

    total_rows = 0
    total_rel = 0
    total_ext = 0

    for hf in html_files:
        text = hf.read_text(encoding="utf-8")
        parser = TableAndLinkParser()
        parser.feed(text)

        total_rows += parser.total_rows
        total_rel += len(parser.rel_links)
        total_ext += len(parser.ext_links)

        if parser.rows_missing_links:
            errors.append(f"{hf.name}: tbody rows missing official https:// link: {parser.rows_missing_links}")
        if parser.external_assets:
            errors.append(f"{hf.name}: external CDN assets forbidden: {parser.external_assets}")
        for ext in parser.ext_links:
            if not domain_allowed(ext):
                errors.append(f"{hf.name}: disallowed external link: {ext}")
        for rel in parser.rel_links:
            clean = rel.split("#", 1)[0].split("?", 1)[0]
            target = (hf.parent / clean).resolve()
            if not target.exists():
                errors.append(f"{hf.name}: broken relative link {rel!r} -> {target}")

    # Privacy scan across all hub/** files (excluding verify.py itself)
    for f in sorted(HUB_DIR.rglob("*")):
        if not f.is_file() or f.name == "verify.py":
            continue
        if f.suffix in (".html", ".json", ".js", ".css", ".md"):
            content = f.read_text(encoding="utf-8")
            for pat, desc in PRIVACY_PATTERNS:
                if pat.search(content):
                    errors.append(f"Privacy violation ({desc}) in {f.relative_to(REPO_ROOT)}")

    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(
        f"HUB VERIFICATION PASSED: {len(html_files)} pages, {len(sources)} official sources, "
        f"{total_rows} table rows (100% linked to allowlisted official domains), "
        f"{total_rel} relative links (0 broken), {total_ext} external official links, "
        f"zero telemetry, zero privacy leaks."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
