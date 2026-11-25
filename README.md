# Jackbox1 — Parcel Decision Workspace

An anonymised, source-linked decision workspace for a **single-tenant quick-service parcel in
central Los Angeles** on a triple-net lease expiring in the 2030–2035 window.

**Live site:** https://kanlerxz87-cyber.github.io/Jackbox1/

---

## What this is

A static, build-free dashboard answering one question: *sell before the lease expires, or renew?*

It does **not** answer that question with a recommendation, because the three numbers a recommendation
requires — rent, price and tax basis — are private and do not exist in this repository. Instead it
publishes:

* what is established, from official sources, with a link on every row;
* what is missing, as a register of gating questions with an owner for each;
* what was attempted and failed, on a **Flagged for Review** page with the URLs that were attempted;
* the machinery to decide the moment the inputs exist, including an after-tax calculator that runs
  entirely in the browser and makes no network calls.

## Privacy rule (non-negotiable)

This repository is public. It contains **no** street address, **no** assessor parcel number, **no**
owner or tenant identifying detail, **no** lease text and **no** owner financials. People and the
property appear only as placeholders:

`OWNER-1` · `TENANT-A` · `PARCEL-A` · `ADVISER-1` … `ADVISER-6`

Private material is specified to live in an offline workspace with a named access list. Anything that
could locate the parcel is deliberately withheld and recorded on the flagged page rather than published.

## Structure

```
index.html            Dashboard + decision-gate board (W-03)
gates.html            Gate-by-gate state and how to move each one
sell-vs-renew.html    Five options, tax rules, after-tax calculator (W-02, W-09)
market.html           Verified city / metro / price evidence + tenant filings
location.html         Why city figures are a proxy, and the private steps that replace them (W-01)
hazards.html          Official hazard programmes, parcel rows withheld (W-04)
questions.html        23 gating questions with owners and sources
suggestions.html      Reviewable suggestion register with effort, cost and falsifier
sources.html          Every official domain, what it is used for and what it cannot be used for
flagged.html          Unverified and irregular items, with attempted URLs
advisor-summary.html  One-page printable brief for advisers (W-10)

data/*.json           Single source of truth — every value, unit, period and source
tools/build_site.py   Generates every HTML page from data/
assets/css/app.css    Styles, including the print sheet
assets/js/calc.js     Browser-side calculator (no network, no storage)
COORDINATION.md       Shared task board for parallel agent sessions
```

## Build

```bash
python3 tools/build_site.py
```

No dependencies, no bundler, no toolchain. The published site makes no runtime network requests at
all: no external CSS, fonts, scripts or analytics.

**Do not hand-edit the generated HTML.** Change `data/*.json` and rebuild, so the data and the
presentation cannot drift apart.

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
depreciation history. See `gates.html` and `questions.html`.
