#!/usr/bin/env python3
"""Internal-link checker for the static site (no network calls)."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT.parent
files = sorted(ROOT.glob("*.html")) + [SITE / "index.html"]
assets = sorted((ROOT / "assets").rglob("*"))
missing = []
checked = 0

for p in files:
    text = p.read_text(encoding="utf-8")
    for attr in ("href", "src"):
        for target in re.findall(rf'{attr}="([^"]+)"', text):
            u = urlparse(target)
            if u.scheme or target.startswith("#") or target.startswith("mailto:"):
                continue
            clean = unquote(u.path.lstrip("/"))
            if not clean:
                clean = "index.html"
            # paths are relative to the file's own directory
            if p.parent == SITE:
                base = SITE / clean
            else:
                base = p.parent / clean
            checked += 1
            if not base.exists():
                # Also allow root-relative resolution from web/
                alt = SITE / clean
                if alt.exists():
                    continue
                missing.append(f"{p.relative_to(SITE)} → {target} (resolved {base.relative_to(SITE)})")

# Check generated asset references specifically
for p in files:
    text = p.read_text(encoding="utf-8")
    for css in re.findall(r'href="([^"]+\.css)"', text):
        if not (p.parent / css).exists() and not (SITE / css).exists():
            missing.append(f"{p.name} → missing CSS {css}")

print(f"Checked {checked} internal links across {len(files)} HTML files; {len([a for a in assets if a.is_file()])} asset files present.")
if missing:
    print("BROKEN LINKS:")
    for m in missing:
        print("  -", m)
    sys.exit(1)
print("LINK CHECK PASSED: no broken internal links.")
