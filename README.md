# Jackbox1 — Parcel Decision Workspace

An anonymised, source-linked decision workspace for a **single-tenant quick-service parcel in central
Los Angeles** on a triple-net lease expiring in the 2030–2035 window.

**Live site:** https://kanlerxz87-cyber.github.io/Jackbox1/

---

## Three sections, one workspace

Parallel agent sessions built three independent research trees. **None was discarded.** Each is
self-contained and each is published; the desk home links to all three.

| Section | Path | What it is |
|---|---|---|
| **Desk home + pages** | `/index.html`, `/pages/` | Session `arena-8c9d9d97` — narrative overview, market, decision paths, questions, suggestions, flags, advisor brief. |
| **Sourced dashboard** | `/docs/` | Session `arena-f5a16939` — dashboard shell with per-page data in `docs/data/findings.json`. |
| **Verified workspace** | `/workspace/` | Session `arena-78005353` — 11 generated pages: 47-row evidence register (40 verified), 23 gating questions, 16 suggestions, 14 flags, gate board, after-tax calculator, one-page brief. |

## The question, and the honest answer

*Sell before the lease expires, or renew?*

**No recommendation is issued anywhere in this repository, and each section says why.** The decision
requires three private numbers — rent, price and tax basis. None exists in a public repo. What the
workspace does instead:

* publishes what **is** established, from official sources, with a link on every row;
* enumerates what **is missing** as gating questions with an owner for each;
* publishes what was **attempted and failed**, with the URLs attempted;
* ships the machinery to decide the moment the inputs exist — including an after-tax calculator that
  runs entirely in the browser and makes no network calls.

## Privacy rule (non-negotiable, applies to every section)

This repository is public. It contains **no** street address, **no** assessor parcel number, **no**
owner or tenant identifying detail, **no** lease text and **no** owner financials. People and the
property appear only as placeholders:

`OWNER-1` · `TENANT-A` · `PARCEL-A` · `ADVISER-1` … `ADVISER-6`

Private material is specified to live in an offline workspace with a named access list. Anything that
could locate the parcel is deliberately withheld and recorded on the flagged pages rather than
published.

## Verified workspace (`/workspace/`)

```
workspace/index.html            Dashboard + decision-gate board (W-03)
workspace/gates.html            Gate-by-gate state and how to move each one
workspace/sell-vs-renew.html    Five options, tax rules, after-tax calculator (W-02, W-09)
workspace/market.html           Verified city / metro / price evidence + tenant filings
workspace/location.html         Why city figures are a proxy; the private steps that replace them (W-01)
workspace/hazards.html          Official hazard programmes; parcel rows withheld (W-04)
workspace/questions.html        23 gating questions with owners and sources
workspace/suggestions.html      Reviewable suggestion register with effort, cost and falsifier
workspace/sources.html          17 official domains: used for / cannot be used for
workspace/flagged.html          14 unverified or irregular items, with attempted URLs
workspace/advisor-summary.html  One-page printable brief for advisers (W-10)

data/*.json                     Single source of truth — value, unit, period, source_url, verified
tools/build_site.py             Generates every page in workspace/ from data/
```

Build:

```bash
python3 tools/build_site.py      # writes workspace/*.html
```

No dependencies, no bundler, no toolchain. The published site makes **no runtime network requests**:
no external CSS, fonts, scripts or analytics.

**Do not hand-edit generated HTML** in `workspace/`. Change `data/*.json` and rebuild, so the data and
the presentation cannot drift apart.

## Verification rule

A value is shown only if it was read from the linked official page during the compilation session.
Otherwise the value is `null`, renders as a blank cell with a flagged badge, and appears on
`flagged.html` with the reason. Nothing is inferred, interpolated or averaged into a value field.
Assumptions live in `data/assumptions.json` and are labelled as assumptions in the UI.

Sources are government and statutory bodies only: Census Bureau, BLS, FHFA, SEC EDGAR, IRS,
California FTB, California DIR, LA County Assessor, FEMA, CAL FIRE OSFM, USGS, Caltrans,
LA City Planning, CA Dept of Education, HUD.

## Status

No recommendation is issued. Six of seven decision gates are open or blocked. The blocking inputs are
the private lease abstract, a dated valuation with closed comparables, and the owner's basis and
depreciation history. See `workspace/gates.html` and `workspace/questions.html`.

Coordination, claims and the merge record are in `COORDINATION.md`.
