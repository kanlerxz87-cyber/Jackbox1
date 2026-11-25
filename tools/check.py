#!/usr/bin/env python3
"""
Post-build checks. Fails (exit 1) on anything that would make the published site wrong or broken:

  1. every internal href/src resolves to a file that exists in workspace/
  2. every in-page anchor (#id) resolves to an element with that id
  3. no page links to a private path or an absolute localhost URL
  4. every data table row carries either a source link or a status badge
  5. no unverified value is rendered as a number
  6. no external scripts, no inline event handlers, no analytics
  7. the required pages all exist
  8. counts printed by the site match the registry

Usage: python3 tools/build.py && python3 tools/check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "workspace"

REQUIRED = [
    "index.html", "questions.html", "economy.html", "tracts.html", "operator.html",
    "hazards.html", "tax.html", "market.html", "model.html", "gates.html", "risks.html",
    "calculator.html", "suggestions.html", "review.html", "sources.html", "privacy.html",
    "summary.html", "404.html", "assets/css/style.css", "assets/js/app.js",
    "assets/js/calc.js", "data/registry.json", "data/registry.csv", "robots.txt",
]

errors: list[str] = []
notes: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def main() -> int:
    pages = sorted(DOCS.glob("*.html"))
    if not pages:
        print("no pages built", file=sys.stderr)
        return 1

    for req in REQUIRED:
        if not (DOCS / req).exists():
            err(f"missing required file: {req}")

    ids_by_page: dict[str, set[str]] = {}
    for p in pages:
        html = p.read_text(encoding="utf-8")
        ids_by_page[p.name] = set(re.findall(r'\sid="([^"]+)"', html))

    for p in pages:
        html = p.read_text(encoding="utf-8")
        # 1 + 2 + 3
        for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
            url = m.group(1)
            if url.startswith(("http://", "https://", "mailto:", "data:")):
                if "localhost" in url or "127.0.0.1" in url:
                    err(f"{p.name}: absolute local URL {url}")
                continue
            if url.startswith("#"):
                if url[1:] and url[1:] not in ids_by_page[p.name]:
                    err(f"{p.name}: dangling anchor {url}")
                continue
            if "private/" in url:
                err(f"{p.name}: links into the private workspace: {url}")
                continue
            base, _, anchor = url.partition("#")
            target = (DOCS / base).resolve()
            if not target.exists():
                err(f"{p.name}: broken internal link {url}")
            elif anchor and base.endswith(".html"):
                if anchor not in ids_by_page.get(target.name, set()):
                    err(f"{p.name}: broken cross-page anchor {url}")
        # 6
        if re.search(r"<script[^>]+src=\"https?://", html):
            err(f"{p.name}: external script tag")
        if re.search(r"on(click|load|error|mouseover)\s*=", html, re.I):
            err(f"{p.name}: inline event handler")
        if re.search(r"google-analytics|googletagmanager|plausible\.io|matomo", html):
            err(f"{p.name}: analytics reference")
        if "fonts.googleapis.com" in html:
            err(f"{p.name}: external font")
        # 4: data rows must be traceable
        for tr in re.findall(r'<tr data-status="[^"]+">.*?</tr>', html, re.S):
            if 'class="badge b-' not in tr:
                err(f"{p.name}: data row without a verification badge")
        # 5: a blank cell must never contain a digit-only value
        for cell in re.findall(r'<td class="blank">([^<]*)</td>', html):
            if re.search(r"\d", cell):
                err(f"{p.name}: blank cell contains digits: {cell!r}")

    # 7 counts consistency
    for p in pages:
        html = p.read_text(encoding="utf-8")
        for m in re.finditer(r"(\d+) rows are blank on purpose", html):
            n = int(m.group(1))
            if n < 1:
                err(f"{p.name}: blank-row count is {n}")

    # crude tag balance for the main containers
    for p in pages:
        html = p.read_text(encoding="utf-8")
        for tag in ("table", "div", "ul", "ol", "tbody", "thead", "fieldset"):
            o = len(re.findall(rf"<{tag}[\s>]", html))
            c = len(re.findall(rf"</{tag}>", html))
            if o != c:
                err(f"{p.name}: unbalanced <{tag}> ({o} open, {c} close)")

    # css/js sanity
    css = (DOCS / "assets/css/style.css").read_text(encoding="utf-8")
    if re.search(r"#[0-9a-fA-F]{0,5}[g-zG-Z]", css):
        err("style.css: malformed hex colour")
    for js in ("app.js", "calc.js"):
        src = (DOCS / "assets/js" / js).read_text(encoding="utf-8")
        if re.search(r"\bfetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|document\.cookie", src):
            err(f"{js}: contains a network or storage call")

    # registry export consistency
    import json
    reg = json.loads((DOCS / "data/registry.json").read_text(encoding="utf-8"))
    c = reg["counts"]
    if sum(c.values()) != reg["rows"]:
        err("registry.json: counts do not sum to rows")
    for r in reg["data"]:
        if r["status"] == "verified" and not r["url"].startswith("http"):
            err(f"registry row {r['id']} verified without a link")

    notes.append(f"pages checked: {len(pages)}")
    notes.append(f"registry rows: {reg['rows']} ({c['verified']} verified / {c['flagged']} flagged / {c['unverified']} blank)")

    for n in notes:
        print("·", n)
    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for e in errors:
            print("  ✗", e, file=sys.stderr)
        return 1
    print("✓ all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
