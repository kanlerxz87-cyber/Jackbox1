# Jackbox property decision workspace

An **anonymised, source-verified decision workspace** for a single-tenant Jack in the Box
on a triple-net lease in central Los Angeles, expiring somewhere between 2030 and 2035.

The owner's question is: **sell before expiry, or renew?** This repository does not answer it
with a guess. It builds the evidence base, states the decision rule, and identifies exactly
which private documents stand between the evidence and a decision.

**Live site:** https://kanlerxz87-cyber.github.io/Jackbox1/

---

## What this is

| | |
|---|---|
| **Data cut-off** | 2026-11-25 |
| **Official sources** | 22, all government or Federal-Reserve hosted |
| **Tracked data rows** | 210 |
| **Verified rows** | 71, every one with a source link (+4 labelled assumptions) |
| **Deliberately blank rows** | 48, all listed on *Flagged for review* |
| **Flagged items** | 13 irregularities + 16 unverified values |
| **Open decision gates** | 15 of 15 — none can close from public data |
| **Model version** | `v0.1-unbacktested-core` (macro engine back-tested; property engine not) |

## Privacy model

Highest priority, enforced by an automated build check, not just by policy.

- The parcel is **`PARCEL-001`** everywhere. No address, APN, owner identity, guarantor,
  tenant legal entity, lease document, rent figure or personal finance exists anywhere in
  this repository.
- `scripts/validate.mjs` fails the build on address, APN, ZIP, email, phone, SSN or EIN
  patterns in any file.
- The calculator runs **entirely in the reader's browser**: no `fetch`, no storage, no
  cookies, no analytics. Verify it — `assets/js/calc.js` has no dependencies and the
  validator greps it for every one of those calls.

## Verification rule

> Every row carries a `source_id` that resolves to a live official URL. If a value could not
> be confirmed against an official source during the session, it is left **blank**, marked
> `unverified`, and published on the *Flagged for review* page. Nothing is inferred,
> interpolated, or filled from a neighbouring geography.

The validator enforces the inverse too: a row marked `unverified` **must not** carry a value.

## Structure

```
data/            verified datasets — the single source of truth
  sources.json       source register + official-host allowlist
  tradearea.json     W-01 market and trade-area rows
  hazards.json       W-04 seismic, flood, fire (with reproducible queries)
  lease.json         identity-free abstract + notice calendar
  valuation.json     W-02 sell/hold inputs, tax rules, gates
  quotes.json        short-lease discount quote log (all empty, on purpose)
  model.json         versioned model, observations vs assumptions, back-test
  stress.json        compound black-swan stress + mitigations
  questions.json     15 blocking gaps + discovery paths + sequence
  suggestions.json   review board: 4 paths, 12 proposals
  flagged.json       12 irregularities + 16 unverified values
pages/           generated HTML (do not edit by hand)
assets/          css + the browser-only calculator
scripts/
  build.mjs          renders pages from data/
  validate.mjs       line-by-line integrity + privacy gate
```

## Build

```bash
node scripts/build.mjs      # regenerate pages/ from data/
node scripts/validate.mjs   # must pass before publish
```

GitHub Pages serves `main` from the repository root; `index.html` redirects to
`pages/index.html`.

## Static counts are never hardcoded

Every number shown on the dashboard — total rows, verified rows, assumption count, dataset
count, flagged counts — is computed from `data/*.json` at build time. If a dataset grows, the
dashboard moves with it; a stale figure cannot survive a rebuild. This was a real bug caught
during deploy verification and fixed in `scripts/build.mjs`.

## The headline finding

1. **Metro fundamentals are sound but not accelerating.** Unemployment 4.6% (Oct 2026),
   nonfarm employment +0.9% YoY, leisure and hospitality +2.0%.
2. **Metro price growth is at the bottom of its own range.** Latest trailing 5-year HPI CAGR
   is 4.57% — the lowest of 27 rolling windows in an 11.5-year sample — and the index is
   0.82% below its 2026 Q1 peak.
3. **Trailing appreciation does not predict forward appreciation here.** Correlation
   **−0.937** across 7 overlapping five-year pairs. Extrapolating the last five years would
   be systematically wrong in the optimistic direction.
4. **Tail risk is demonstrated, not hypothetical.** The county carried a major wildfire
   disaster declaration in January 2025, six fire-management declarations in 14 months, and
   five storm/flood declarations in two winters.
5. **The exit is taxed more heavily than owners assume.** No California capital-gain
   preference, 25% federal recapture on depreciation, and 3.8% NIIT where it applies.

## What must happen before any decision

Fifteen gates, sequenced on the *Open questions* page. Three cost nothing and one is dated:

1. **Before 2026-11-30** — file the decline-in-value application if assessed value exceeds
   market value (LA County Assessor).
2. **Pin the four lease dates.** A lapsed renewal option is the only irreversible loss in
   this entire project.
3. **Register a free Census API key** so the tract-level trade area can actually be built.

---

*Not investment, legal or tax advice. Engage a licensed appraiser, attorney and CPA before
acting. See `COORDINATION.md` for the task board, sources, verification performed and the
PR/deploy record.*

---

## This session's tree: `/workspace/` (session `arena/2a61b633`)

A fourth, independent build, added after PRs #1–#4 landed. It is published at
**https://kanlerxz87-cyber.github.io/Jackbox1/workspace/** and is fully self-contained
(17 pages, its own nav, no shared assets, no links into another session's tree).

Its distinguishing feature is that the site is **generated from a data registry**, so a value cannot
appear on a page without a source link and a verification status:

```
data/registry.yaml        72 rows — id, metric, value, unit, geography, period, source, url, status, note
data/tracts_demo_90015.csv  23 tract-level ACS observations (demonstration set only)
tools/build.py            generator: reads data/, writes workspace/
tools/check.py            link, anchor, tag-balance, traceability and privacy checks
tools/reverify.py         re-pulls every machine-readable source and diffs against the registry
private/                  blank lease-abstract / notice-calendar / sell-vs-hold templates (gitignored)
```

Rebuild and verify:

```bash
pip install --break-system-packages pyyaml
python3 tools/build.py   # idempotent; nothing in workspace/ is hand-edited
python3 tools/check.py   # fails on a broken link, a dangling anchor or an untraceable row
```

Build-time status: **57 verified / 5 flagged / 10 deliberately blank** rows.

The build refuses to run if a row marked `verified` has no source link, and refuses to render a blank
value as anything other than a visible *unverified* cell. No external scripts, no analytics, no
cookies, no storage, and the calculator makes no network calls — all arithmetic happens in the browser.

Its pages: overview, questions register, trade area, tract evidence, tenant strength, hazard screen,
after-tax, short-lease pricing, sell-vs-hold, decision gates, risk register, calculator, suggestions,
flagged for review, sources, privacy, and a one-page printable summary.

---

## Earlier root tree (preserved, not deleted)

An earlier parallel session built a second root site (`index.html`, `pages/`, `assets/`) that now
sits alongside this one. It is kept and reachable; it is not overwritten.

> # Anonymous Central LA NNN workspace
> Public research site for an **anonymized** sell-versus-renew review of a Jack in the Box NNN lease described as located around Central Los Angeles.
> **This repository must not contain** owner names, street addresses, APNs, lease PDFs, tax returns, or unit-level sales.
> Two static trees are in the repo (parallel sessions; both retained):
> | Tree | Session | Entry |
> | --- | --- | --- |
> | Repository root | arena-8c9d9d97 | `index.html`, `pages/`, `assets/` |
> | `docs/` | arena-f5a16939 | `docs/index.html` (sourced tables, decision gates, calculator) |
> GitHub Pages is configured to publish the **repository root**, so both `/` and `/docs/` can resolve.
> **No sell or renew recommendation is made.**
> A public static website is not an access-controlled vault. Keep lease files and owner finances offline. See [COORDINATION.md](COORDINATION.md) and the Flagged for Review pages (`pages/flags.html` and `docs/flagged.html`).

---

## Tree map and independent audit pass (`/audit-78005353/`)

Five parallel sessions have published into this repository. All are retained.

| Tree | Session | Entry |
|---|---|---|
| Primary workspace | `arena-41ea221b` | `pages/index.html` (root `index.html` redirects here) |
| Sourced dashboard | `arena-f5a16939` | `docs/index.html` |
| Desk tree | `arena-8c9d9d97` | `desk/index.html` |
| Second verified workspace | `arena/2a61b633` | `workspace/index.html` |
| **Independent audit pass** | `arena-78005353` | `audit-78005353/site/index.html` |

The audit pass is a separate second opinion on the same question, built from primary sources read
directly in its own session. It is additive: no file in the sections above was altered.

| Page | Purpose |
|---|---|
| `audit-78005353/site/index.html` | Dashboard + decision-gate board |
| `audit-78005353/site/gates.html` | Seven gates, who closes each, what breaks if left open |
| `audit-78005353/site/sell-vs-renew.html` | Five decision options, verified tax rules, browser-side after-tax calculator |
| `audit-78005353/site/market.html` | 47-row evidence register + the franchisor's own SEC disclosures |
| `audit-78005353/site/location.html` | Why city figures are a proxy; the private steps that replace them |
| `audit-78005353/site/hazards.html` | Official hazard programmes; parcel rows withheld |
| `audit-78005353/site/questions.html` | 23 gating questions with owners and sources |
| `audit-78005353/site/suggestions.html` | 16 suggestions with effort, cost, falsifier and privacy verdict |
| `audit-78005353/site/sources.html` | 17 official domains: used for / cannot be used for |
| `audit-78005353/site/flagged.html` | 14 unverified or irregular items with the URLs attempted |
| `audit-78005353/site/advisor-summary.html` | One-page printable brief |

**Verification:** 40 of 47 evidence rows read from the linked official page; the 7 that could not be
confirmed are left **blank** and published on the flagged page with the reason. Ledger audit: 40/40
numeric values and 11/11 tenant facts re-checked against the fetched content, 0 mismatches. Link
audit across all HTML files in the repository: 0 broken links. HTML parse: 0 tag errors. The
calculator makes no network call and stores nothing.

**Build:** `python3 tools/build_site.py` regenerates `audit-78005353/site/` from
`data/audit-78005353/*.json`. No dependencies. Do not hand-edit the generated HTML.

**No sell-or-renew recommendation is made in that pass either.** It states the decision rule, the
gates, and exactly which private documents stand between the evidence and a decision.
