# Anonymous Central LA NNN workspace

Public research site for an **anonymized** sell-versus-renew review of a Jack in the Box NNN lease described as located around Central Los Angeles.

**This repository must not contain** owner names, street addresses, APNs, lease PDFs, tax returns, or unit-level sales.

Four static trees are in the repo (parallel sessions; **all retained**):

| Tree | Session | Entry |
| --- | --- | --- |
| Primary workspace | arena-41ea221b | `pages/index.html` (root `index.html` redirects here) |
| Sourced dashboard | arena-f5a16939 | `docs/index.html` (sourced tables, decision gates, calculator) |
| Desk tree | arena-8c9d9d97 | `desk/index.html` |
| Verified workspace | arena-78005353 | `workspace/index.html` (47-row evidence register, 23 questions, gate board, after-tax calculator, printable one-pager) |

GitHub Pages publishes the **repository root**, so `/`, `/pages/`, `/docs/`, `/desk/` and `/workspace/` all resolve.

**No sell or renew recommendation is made.**

A public static website is not an access-controlled vault. Keep lease files and owner finances offline. See [COORDINATION.md](COORDINATION.md) and the Flagged for Review pages (`pages/flags.html` and `docs/flagged.html`).


---

## Also in this repository: the desk tree

An earlier session (`arena-8c9d9d97`) published a narrative desk tree at `/desk/` with its own
overview and page set. It is retained unmodified and reachable at `desk/index.html`.

## Preserved: earlier README of this tree

The text below is the README written for the `arena/f5a16939` tree, kept verbatim so its record of
sources, flags and next steps is not lost.

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
| **Verified rows** | 71, every one with a source link |
| **Deliberately blank rows** | 48, all listed on *Flagged for review* |
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

## Repository layout — three parallel builds, all retained

This repo was produced by three concurrent sessions. **Nothing was deleted.**

| Path | What it is | Start here |
|---|---|---|
| `/pages/index.html` | **Primary.** Source-verified workspace, 11 pages, live official data, browser calculator | ← start here |
| `/desk/index.html` | Earlier root site, preserved intact with links rewritten | archive |
| `/docs/index.html` | Parallel sourced research dashboard from another session | archive |

Live: https://kanlerxz87-cyber.github.io/Jackbox1/pages/index.html

## Cross-session note on figures

Two official Los Angeles population figures appear in this repo — 3,878,704 (Census Vintage
2024) and 3,869,089 (QuickFacts V2025). They are different vintages and are **not
comparable**. The Census Bureau warns against comparing vintages. The same applies to the two
unemployment figures (county NSA Sep 2025 vs metro division Oct 2026). Every row in the primary
tree states its geography and period. See irregularity IR-13 on the *Flagged for review* page.

## Prior session README (preserved)

<details><summary>Earlier README content from a parallel session</summary>

# Anonymous Central LA NNN workspace

Public research site for an **anonymized** sell-versus-renew review of a Jack in the Box NNN lease described as located around Central Los Angeles.

**This repository must not contain** owner names, street addresses, APNs, lease PDFs, tax returns, or unit-level sales.

Four static trees are in the repo (parallel sessions; **all retained**):

| Tree | Session | Entry |
| --- | --- | --- |
| Primary workspace | arena-41ea221b | `pages/index.html` (root `index.html` redirects here) |
| Sourced dashboard | arena-f5a16939 | `docs/index.html` (sourced tables, decision gates, calculator) |
| Desk tree | arena-8c9d9d97 | `desk/index.html` |
| Verified workspace | arena-78005353 | `workspace/index.html` (47-row evidence register, 23 questions, gate board, after-tax calculator, printable one-pager) |

GitHub Pages publishes the **repository root**, so `/`, `/pages/`, `/docs/`, `/desk/` and `/workspace/` all resolve.

**No sell or renew recommendation is made.**

A public static website is not an access-controlled vault. Keep lease files and owner finances offline. See [COORDINATION.md](COORDINATION.md) and the Flagged for Review pages (`pages/flags.html` and `docs/flagged.html`).

</details>

---

## Additional section: Verified workspace (`/workspace/`)

Built by session `arena-78005353` and published alongside the trees above. Self-contained, generated
from `data/workspace/*.json` by `tools/build_site.py`. Nothing in the other sections was altered.

| Page | Purpose |
|---|---|
| `workspace/index.html` | Dashboard + decision-gate progress board (W-03) |
| `workspace/gates.html` | Gate-by-gate state, who closes it, what breaks if it stays open |
| `workspace/sell-vs-renew.html` | Five decision options, verified tax rules, browser-side after-tax calculator (W-02, W-09) |
| `workspace/market.html` | 47-row evidence register + tenant franchisor's own SEC disclosures (W-08) |
| `workspace/location.html` | Why city figures are a proxy; the private steps that replace them (W-01) |
| `workspace/hazards.html` | Four official hazard programmes; parcel rows withheld (W-04) |
| `workspace/questions.html` | 23 gating questions with owners and sources (W-05) |
| `workspace/suggestions.html` | 16 suggestions with effort, cost, falsifier and privacy verdict (W-06) |
| `workspace/sources.html` | 17 official domains: used for / cannot be used for (W-07) |
| `workspace/flagged.html` | 14 unverified or irregular items with the URLs attempted (W-07) |
| `workspace/advisor-summary.html` | One-page printable brief (W-10) |

**Verification:** 40 of 47 evidence rows read from the linked official page; the 7 that could not be
confirmed are left **blank** and published on `flagged.html` with the reason. Automated ledger audit:
40/40 numeric values and 11/11 tenant facts re-checked against the fetched content, 0 mismatches.
Cross-tree link audit across all 36 pages of all trees: 0 broken links. HTML parse: 0 tag errors.

**Build:** `python3 tools/build_site.py` (no dependencies). Do not hand-edit `workspace/*.html`.
