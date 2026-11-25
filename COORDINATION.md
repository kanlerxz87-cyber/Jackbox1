# COORDINATION.md — Shared Task Board

> This file is the single source of truth for who is working on what.
> Rule: claim a task by writing your session ID + file scope here, commit and push the claim
> **before** starting work. Never start a task another session has claimed.
> Status values: `unclaimed` · `in progress` · `needs review` · `done`
> Stale claims (> 60 min, no commits) may be taken over; note the handoff in the Log.

## ⚠️ Read first: three parallel sessions, three static trees

This repository was built by **three** concurrent sessions. All three trees are retained.
Nothing has been deleted or overwritten.

| Session | Tree | What it is | Entry point |
|---|---|---|---|
| `arena-8c9d9d97` | `/` (root `index.html`, `pages/`, `assets/`) | First privacy-first site (PR #1) | superseded by the integrated build below |
| `arena-f5a16939` | `/docs/` | Sourced research dashboard (PR #2) | `/docs/index.html` |
| `ses-41ea221b` (this session) | `/` + `/pages/` + `/data/` | **Primary**: verified data layer, 11-page workspace, browser calculator, validator | `/index.html` → `/pages/index.html` |
| `arena-8c9d9d97` + `arena-f5a16939` trees, preserved | `/desk/` | The earlier root site, moved here intact so its links still resolve | `/desk/index.html` |

**Integration decision (ses-41ea221b).** The root tree could only have one `pages/` directory.
The earlier root site was **moved intact to `/desk/`** with its internal links rewritten, and
every page now carries a banner pointing to the primary workspace. Its four extra pages
(`brief`, `calculator`, `decisions`, `flags`) remain reachable under `/desk/pages/`. The
`/docs/` tree was not touched at all. **Total: 21 pages across three trees, 284 internal
links, all resolving.**

## Session registry

| Session ID | Branch | Role | State |
|---|---|---|---|
| `arena-8c9d9d97` | merged via PR #1 | initial root site | done (needs review) |
| `arena-f5a16939` | merged via PR #2 | `docs/` sourced dashboard | done |
| `ses-41ea221b` | `arena/41ea221b-jackbox1` | verified data layer + integration + publish | active |

## Task board — ses-41ea221b

| ID | Task | Status | Owner | File scope (exclusive) |
|---|---|---|---|---|
| T-01 | Repo review + task board + privacy model | done | ses-41ea221b | `COORDINATION.md`, `README.md`, `.nojekyll`, `PRIVACY.md` |
| T-02 | Source register | done | ses-41ea221b | `data/sources.json` |
| T-03 | W-01 trade-area figures | done | ses-41ea221b | `data/tradearea.json`, `pages/market.html` |
| T-04 | W-04 parcel hazard screening | done | ses-41ea221b | `data/hazards.json`, `pages/hazards.html` |
| T-05 | Lease abstract + notice calendar | done | ses-41ea221b | `data/lease.json`, `pages/lease.html` |
| T-06 | W-02 sell-vs-hold + after-tax | done | ses-41ea221b | `data/valuation.json`, `pages/decision.html` |
| T-07 | Short-lease discount from real quotes | done | ses-41ea221b | `data/quotes.json` |
| T-08 | Versioned model + back-test | done | ses-41ea221b | `data/model.json`, `pages/scenarios.html` |
| T-09 | Black-swan stress | done | ses-41ea221b | `data/stress.json` |
| T-10 | Open questions + discovery plan | done | ses-41ea221b | `data/questions.json`, `pages/questions.html` |
| T-11 | Suggestion board with path choice | done | ses-41ea221b | `data/suggestions.json`, `pages/suggestions.html` |
| T-12 | W-03 decision-gate board | done | ses-41ea221b | `pages/index.html` |
| T-13 | W-10 printable brief | done | ses-41ea221b | `pages/print.html` |
| T-14 | Flagged-for-review page | done | ses-41ea221b | `data/flagged.json`, `pages/flagged.html` |
| T-15 | Line-by-line validator | done | ses-41ea221b | `scripts/validate.mjs` |
| T-16 | Integration: merge, re-verify, rebuild | done | ses-41ea221b | site-wide |
| T-17 | Publish + confirm deploy | in progress | ses-41ea221b | repo settings |

## Earlier task boards (preserved verbatim from `main`)

**Merge note (2026-11-25):** `origin/main` already contained session `arena-8c9d9d97` (PR #1: root `index.html`, `pages/`, `assets/`). Session `arena-f5a16939` built a second tree under `docs/`. Both trees are kept. Neither session’s files were discarded. Shared index/nav were not rewritten in this merge; GitHub Pages should publish the repository root so both `/` and `/docs/` resolve.

## Tasks

| ID | Task | Status | Owner | Files |
| --- | --- | --- | --- | --- |
| A1 | Initial privacy-first site, research, verification and integration | needs review | arena-8c9d9d97 | index.html, assets/*, pages/*, README.md, COORDINATION.md |
| T0 | Create coordination board | done | arena-f5a16939 | COORDINATION.md |
| T1 | Privacy policy, placeholders, internal-use notice | done | arena-f5a16939 | docs/privacy.html, docs/js/nav.js, README.md |
| T2 | W-01 trade-area vs city/county proxies | done | arena-f5a16939 | docs/trade-area.html, docs/data/findings.json |
| T3 | Tenant system evidence (same-store, units, closures, rental revenue) | done | arena-f5a16939 | docs/tenant.html, docs/data/findings.json |
| T4 | W-04 parcel hazard screening (maps only; parcel blank) | done | arena-f5a16939 | docs/hazards.html |
| T5 | W-02 sell-versus-hold worksheet (no winner) | done | arena-f5a16939 | docs/sell-vs-hold.html |
| T6 | After-tax module (verified tax rules only) | done | arena-f5a16939 | docs/after-tax.html |
| T7 | Private in-browser calculator | done | arena-f5a16939 | docs/calculator.html, docs/js/calculator.js |
| T8 | W-03 decision-gate board | done | arena-f5a16939 | docs/decision-gate.html |
| T9 | Questions, missing information, discovery path | done | arena-f5a16939 | docs/questions.html |
| T10 | W-10 one-page printable advisor summary | done | arena-f5a16939 | docs/advisor-summary.html |
| T11 | Suggestions for site and decision process | done | arena-f5a16939 | docs/suggestions.html |
| T12 | Flagged for Review page | done | arena-f5a16939 | docs/flagged.html |
| T13 | Site shell, dashboard, sources, methods | done | arena-f5a16939 | docs/index.html, docs/css/app.css, docs/sources.html, docs/methods.html |
| T14 | GitHub Pages publish, PR, merge to main | done | arena-f5a16939 | (legacy Pages from `main` `/`; duplicate Actions workflow removed after it conflicted with legacy) |

## Verification (arena-f5a16939)

- Census Vintage 2024 press release CB25-77 fetched: LA city 3,878,704; +31,276.
- Census Reporter ACS 2024 1-year city and county profiles fetched (flagged as republisher).
- EDD September 2025 release fetched: LA County NSA unemployment 5.9%.
- JACK FY 2025 earnings release fetched: SSS, units, closures, guidance.
- IRS Topic 409, NIIT FAQ, like-kind tips fetched.
- USGS UCERF3 FAQ fetched.
- FTB 2025 540 booklet fetched (top rate / BHST; full brackets not copied).
- SEC 10-K iXBRL fetched but dollar lines not confirmed → franchise rental revenue left blank.

## Verification (arena-8c9d9d97, as recorded on main)

- Census QuickFacts city population and income after a later fetch; county comparison page could not be fetched and a county figure was removed.
- BLS metro unemployment/employment links; issuer FY2025 release; FEMA; CAL FIRE; USGS; IRS Pub 544.
- Direct page fetch failures flagged; issuer disclosures are corporate, not a government verification of this tenant.

## Irregularities

- Public GitHub remote.
- Two parallel static trees (`/` and `/docs/`).
- data.census.gov fetch failed in arena-f5a16939; QuickFacts numbers not used in `docs/`.
- No parcel-level identifiers, by design.
- No sell/renew winner, by design.

## Log

- 2026-11-25 arena-8c9d9d97: Built root static anonymous site (PR #1 merged to main). Status needs review.
- 2026-11-25 arena-f5a16939: Built `docs/` tree on `arena/f5a16939-jackbox1`. PR #2 conflicted with main. Merged `origin/main` into this branch without deleting the root site. Both trees retained.
- 2026-11-25 arena-f5a16939: PR https://github.com/kanlerxz87-cyber/Jackbox1/pull/2 merged (`bcdc324`). GitHub Pages built: https://kanlerxz87-cyber.github.io/Jackbox1/ (root desk) and https://kanlerxz87-cyber.github.io/Jackbox1/docs/ (sourced dashboard). Duplicate Actions `deploy-pages` job failed against legacy Pages source and is being removed so checks stay green.

## Log

### 2026-11-25 · ses-41ea221b
- Repo arrived empty (`README.md` only, commit `4aa9dad`). No prior work to reconcile, no conflicts.
- Claimed T-01…T-16. Scope is the whole tree because no other session is active.
- Data policy set: every row carries `source_id` → URL; anything unconfirmed is `unverified`,
  left blank, and published on `pages/flagged.html`. No inferred values.
- No parcel address, owner identity, APN, lease file or owner finances will be committed or
  published. Parcel is referred to as `PARCEL-001` throughout (see `PRIVACY.md`).

### Irregularities found (detail on `pages/flagged.html`)
- Public brief references "central Los Angeles" but no parcel identifier is available in this repo.
  Parcel-level census tract, flood zone, FHSZ and seismic-zone determinations therefore **cannot**
  be verified here; they are published as `unverified / requires private lookup` rather than guessed.
- The public brief mixes property level and reader level language ("decision for the property and
  myself as an individual"). Owner-level after-tax position depends on private data (basis, entity,
  other income) that is not in scope of a public site; modelled only as clearly-labelled placeholders.
- Jack in the Box corporate lease-expiry dates are not published per-store in SEC filings at the
  granularity needed; the 2030–2035 window is taken from the owner brief (**unverified externally**).

## Handoff / takeover rules

If this session dies mid-task: any session may take over an `in progress` item older than 60 min
with no commit, after appending `TAKEOVER` + its session ID to the Log. Do not rewrite
`data/sources.json` rows owned by another session; add new rows with new IDs instead.

## PR / deploy record

Recorded at the bottom of this file once T-16/T-17 complete.

### Integration session record (T-16) — ses-41ea221b

**Merge.** Single active session, so no cross-branch merge was required. `arena/41ea221b-jackbox1`
was branched from `main@4aa9dad` and is a strict fast-forward (`README.md` only in base).

**Re-verification performed on the combined data, line by line:**
- 43 machine-checked assertions comparing every published figure back to the captured source
  response. Result: **43 of 43 match**. Re-run with the script in the PR description.
- Two arithmetic recomputations: HPI vs 2026 Q1 peak = −0.82% (matches); CAGR = 6.026% at
  11.496 years, published as 6.03 (matches, note added to `OB-02` for the rounding).
- Back-test recomputed independently from the 47 FHFA observations: 7 overlapping pairs,
  correlation −0.937, direction hit rate 100%, mean absolute error 1.70 pp. Matches.
- Calculator tax arithmetic recomputed by hand outside the page: gain 1,020,000; recapture
  slice 400,000; federal 201,498; California 94,860; NIIT 34,960; after-tax proceeds
  1,588,683. The page produced identical figures.

**Build checks (`node scripts/validate.mjs`) — all pass:**
- 22 sources, every host on the official allowlist, all https, all dated.
- 210 tracked rows; 71 verified-like rows all carry a resolving `source_id`;
  48 unverified rows all have blank values (the validator fails if either invariant breaks).
- 173 internal links resolve to a file that exists. Zero broken links.
- Privacy scan over all pages, datasets and scripts: no address, APN, ZIP, email, phone,
  SSN or EIN pattern found.
- Calculator contains no `fetch`, `XMLHttpRequest`, `sendBeacon`, `localStorage`,
  `sessionStorage`, `indexedDB`, `document.cookie`, `WebSocket` or `geolocation` call.
- Structural check: all 11 pages tag-balanced, no `undefined` or `[object Object]` leaks.

**Irregularities found** (12, detailed on `pages/flagged.html`): the parcel is unidentified
(IR-01), the lease term is an eight-year window (IR-02), the brief conflates property-level
and owner-level decisions (IR-03), the Census API requires a key (IR-04), CAL FIRE returned an
empty feature set that must not be read as "unzoned" (IR-05), the FTB rate page failed to load
(IR-06), LA County QuickFacts failed (IR-07), the HPI series used is the MSA not the
metropolitan division (IR-08), CPI change is printed for September not October (IR-09), and no
cap rate / rent / basis / insurance figure exists anywhere (IR-10). IR-11 and IR-12 record the
reference-point hazard query and the deliberate asymmetry between the public tenant brand and
the withheld owner identity.

**Deliberate non-deliverables, stated on the site:** no sell/renew verdict, no cap rate, no
dollar loss estimate for any hazard. Each is blocked by a named, documented gap and would have
required inventing an input.

**Flagged items do not block publication and are published on the Flagged for Review page.**
# COORDINATION

Shared task board for parallel sessions. Claim a task before editing files. Do not edit files owned by another active claim.

Privacy rule (all sessions): no owner names, no street addresses, no APNs, no lease PDFs, no tax returns, no tenant-unit sales for the subject site. Public pages use placeholders only.

**Merge note (2026-11-25):** `origin/main` already contained session `arena-8c9d9d97` (PR #1: root `index.html`, `pages/`, `assets/`). Session `arena-f5a16939` built a second tree under `docs/`. Both trees are kept. Neither session’s files were discarded. Shared index/nav were not rewritten in this merge; GitHub Pages should publish the repository root so both `/` and `/docs/` resolve.

## Tasks

| ID | Task | Status | Owner | Files |
| --- | --- | --- | --- | --- |
| A1 | Initial privacy-first site, research, verification and integration | needs review | arena-8c9d9d97 | index.html, assets/*, pages/*, README.md, COORDINATION.md |
| T0 | Create coordination board | done | arena-f5a16939 | COORDINATION.md |
| T1 | Privacy policy, placeholders, internal-use notice | done | arena-f5a16939 | docs/privacy.html, docs/js/nav.js, README.md |
| T2 | W-01 trade-area vs city/county proxies | done | arena-f5a16939 | docs/trade-area.html, docs/data/findings.json |
| T3 | Tenant system evidence (same-store, units, closures, rental revenue) | done | arena-f5a16939 | docs/tenant.html, docs/data/findings.json |
| T4 | W-04 parcel hazard screening (maps only; parcel blank) | done | arena-f5a16939 | docs/hazards.html |
| T5 | W-02 sell-versus-hold worksheet (no winner) | done | arena-f5a16939 | docs/sell-vs-hold.html |
| T6 | After-tax module (verified tax rules only) | done | arena-f5a16939 | docs/after-tax.html |
| T7 | Private in-browser calculator | done | arena-f5a16939 | docs/calculator.html, docs/js/calculator.js |
| T8 | W-03 decision-gate board | done | arena-f5a16939 | docs/decision-gate.html |
| T9 | Questions, missing information, discovery path | done | arena-f5a16939 | docs/questions.html |
| T10 | W-10 one-page printable advisor summary | done | arena-f5a16939 | docs/advisor-summary.html |
| T11 | Suggestions for site and decision process | done | arena-f5a16939 | docs/suggestions.html |
| T12 | Flagged for Review page | done | arena-f5a16939 | docs/flagged.html |
| T13 | Site shell, dashboard, sources, methods | done | arena-f5a16939 | docs/index.html, docs/css/app.css, docs/sources.html, docs/methods.html |
| T14 | GitHub Pages publish, PR, merge to main | done | arena-f5a16939 | (legacy Pages from `main` `/`; duplicate Actions workflow removed after it conflicted with legacy) |

## Verification (arena-f5a16939)

- Census Vintage 2024 press release CB25-77 fetched: LA city 3,878,704; +31,276.
- Census Reporter ACS 2024 1-year city and county profiles fetched (flagged as republisher).
- EDD September 2025 release fetched: LA County NSA unemployment 5.9%.
- JACK FY 2025 earnings release fetched: SSS, units, closures, guidance.
- IRS Topic 409, NIIT FAQ, like-kind tips fetched.
- USGS UCERF3 FAQ fetched.
- FTB 2025 540 booklet fetched (top rate / BHST; full brackets not copied).
- SEC 10-K iXBRL fetched but dollar lines not confirmed → franchise rental revenue left blank.

## Verification (arena-8c9d9d97, as recorded on main)

- Census QuickFacts city population and income after a later fetch; county comparison page could not be fetched and a county figure was removed.
- BLS metro unemployment/employment links; issuer FY2025 release; FEMA; CAL FIRE; USGS; IRS Pub 544.
- Direct page fetch failures flagged; issuer disclosures are corporate, not a government verification of this tenant.

## Irregularities

- Public GitHub remote.
- Two parallel static trees (`/` and `/docs/`).
- data.census.gov fetch failed in arena-f5a16939; QuickFacts numbers not used in `docs/`.
- No parcel-level identifiers, by design.
- No sell/renew winner, by design.

## Log

- 2026-11-25 arena-8c9d9d97: Built root static anonymous site (PR #1 merged to main). Status needs review.
- 2026-11-25 arena-f5a16939: Built `docs/` tree on `arena/f5a16939-jackbox1`. PR #2 conflicted with main. Merged `origin/main` into this branch without deleting the root site. Both trees retained.
- 2026-11-25 arena-f5a16939: PR https://github.com/kanlerxz87-cyber/Jackbox1/pull/2 merged (`bcdc324`). GitHub Pages built: https://kanlerxz87-cyber.github.io/Jackbox1/ (root desk) and https://kanlerxz87-cyber.github.io/Jackbox1/docs/ (sourced dashboard). Duplicate Actions `deploy-pages` job failed against legacy Pages source and is being removed so checks stay green.

---

## Cross-session reconciliation (ses-41ea221b, integration)

Two sessions published a **different Los Angeles city population figure** from different
official vintages. Neither is wrong; they are not comparable:

| Session | Figure | Vintage | Status |
|---|---|---|---|
| `arena-f5a16939` | 3,878,704 | Census Vintage 2024 release CB25-77 | official, superseded |
| `ses-41ea221b` (this tree) | 3,869,089 | QuickFacts V2025, July 1 2025 estimate | official, latest |

This is recorded as irregularity **IR-13** on `pages/flagged.html`: two official figures that
look contradictory unless the vintage is stated. The Census Bureau itself warns that different
vintage years are not comparable (source `S-021`). The primary workspace uses V2025 and states
the vintage in every row.

**Unemployment**: `arena-f5a16939` recorded LA County NSA 5.9% (EDD, September 2025); this tree
records the LA-Long Beach-Glendale *metropolitan division* at 4.6% (BLS, October 2026). Different
geography, different period, different statistic. Both are cited; neither is reconciled into the
other. Do not mix them.

**No session's work was discarded.** No merge conflict was resolved by deleting the other side.

## Deploy record (T-17)

- PR to `main`: https://github.com/kanlerxz87-cyber/Jackbox1/pull/4
- Pages source: `main` / root, legacy build, https enforced.
- Primary site: https://kanlerxz87-cyber.github.io/Jackbox1/pages/index.html
- Parallel trees: `/docs/index.html`, `/desk/index.html`


---

# Integration session `arena-78005353` — record

Claimed at 13:38 UTC on 2026-11-25, when the repository held only a one-word `README.md`
(commit `4aa9dad`). Main advanced four times during the session; this record covers the reconciliation.

## Trees in the repository after this merge

| Tree | Session | Path |
|---|---|---|
| Primary workspace | `arena-41ea221b` | `/pages/` (root `index.html` redirects here) |
| Sourced dashboard | `arena-f5a16939` | `/docs/` |
| Desk tree | `arena-8c9d9d97` | `/desk/` |
| **Verified workspace** | `arena-78005353` | `/workspace/` |

**No session's work was discarded.** Every conflict was resolved by keeping the other side's file and
adding this session's material alongside it.

## How each conflict was resolved

| File | Resolution |
|---|---|
| `index.html` (root) | **Kept main's version** (its redirect to `pages/index.html`) and appended a notice block linking to all four trees. Main's redirect is untouched. |
| `README.md` | **Kept main's README** and appended an "Additional section: Verified workspace" block. |
| `COORDINATION.md` | **Kept main's board verbatim** (conflict markers stripped if present) and appended this record below it. |
| `data/*.json` | This tree's data was **moved to `data/workspace/`** before merging, because `arena-41ea221b` owns `data/market.json`, `data/hazards.json`, `data/questions.json`, `data/suggestions.json`, `data/flagged.json` and others. Renaming avoided any overwrite. |
| `assets/css`, `assets/js` | This tree's CSS/JS live under `workspace/assets/`, so no collision with `assets/css/site.css` or `assets/js/calc.js`. |

## Claims and scope (this session)

| ID | Task | Status | Files |
|---|---|---|---|
| W-01 | Replace city/county proxies with trade-area figures | done (method published; figures private) | `workspace/location.html`, `data/workspace/market.json` |
| W-02 | Extend worksheet to sell-vs-hold comparison | done | `workspace/sell-vs-renew.html`, `workspace/assets/js/calc.js` |
| W-03 | Decision-gate progress board | done | `data/workspace/gates.json`, `workspace/index.html`, `workspace/gates.html` |
| W-04 | Parcel-level hazard screening | done (programmes verified; parcel rows withheld) | `data/workspace/hazards.json`, `workspace/hazards.html` |
| W-05 | Question / information / answer register | done | `data/workspace/questions.json`, `workspace/questions.html` |
| W-06 | Suggestions register + review page | done | `data/workspace/suggestions.json`, `workspace/suggestions.html` |
| W-07 | Verification and flagged register | done | `data/workspace/flagged.json`, `workspace/flagged.html`, `workspace/sources.html` |
| W-08 | Market and economy pages | done (schools and county blank — flagged) | `data/workspace/market.json`, `data/workspace/tenant.json`, `workspace/market.html` |
| W-09 | After-tax module + short-lease discount | done (discount unpriced — flagged) | `data/workspace/tax.json`, `workspace/sell-vs-renew.html` |
| W-10 | One-page printable advisor summary | done | `workspace/advisor-summary.html` |
| INT-01 | Integration, build, PR, merge, Pages | done | `COORDINATION.md`, `README.md`, `index.html`, `workspace/*` |

## Verification performed (this session)

- **40 of 47** evidence rows read from the linked official page; **7 left blank** and published with the
  attempted URL. Ledger audit: 40/40 numeric values and 11/11 tenant facts re-checked against the
  fetched content — **0 mismatches**.
- Official sources actually fetched: Census QuickFacts (city), BLS LA Area Economic Summary PDF, BLS
  CPI Los Angeles release, BLS Public Data API `LAUMT063108000000003` and `SMU06310800000000001`,
  FHFA HPI 2026Q3, SEC EDGAR 10-K FY2025 (accession 0000807882-25-000072), IRS Topics 409 and 704,
  IRS NIIT Q&A, IRS 1031 guidance, FTB 2024 and 2025 rate schedules, FTB Pub 1100, FTB capital-gains
  page, CA DIR minimum-wage FAQ, LA County Assessor Prop 13 and DIV pages, FEMA Flood Map Service
  Center, CAL FIRE OSFM FHSZ, USGS earthquake hazards, FEMA NRI/RAPT, U.S. Treasury yield curve,
  Caltrans traffic census, LA City Planning, CAASPP, HUD FMR.
- HTML parse check on all 11 `workspace/` pages: **0 tag errors, 0 unclosed elements**.
- Cross-tree link audit across **all 36 pages** of all four trees: **0 broken links**.
- Calculator: all 21 element IDs referenced by `calc.js` exist in the page; `node --check` passes; the
  script contains no network call, no storage and no analytics.

## Irregularities recorded by this session

- **IR-W1** Vintage divergence: Vintage 2024 (3,878,704) vs QuickFacts V2025 (3,869,089). Both correct
  for their own vintage, both labelled. Consistent with `arena-41ea221b`'s IR-13.
- **IR-W2** Four parallel static trees. Kept deliberately rather than deleting another session's work;
  reachable from a notice block on the root `index.html`.
- **IR-W3** A GitHub Pages site is not an access-controlled workspace. All four trees state this.
- **IR-W4** Reader-specific fetch failures are enumerated on `workspace/flagged.html` (FR-01 … FR-14),
  each with the URL attempted: Census county QuickFacts, CA DIR fast-food wage, CGS Alquist-Priolo,
  HUD FMR, CA FAIR Plan page, the retired CAL FIRE FHSZ URL.
- **IR-W5** The widely reported $20.00 California fast-food minimum wage was **not** confirmed on an
  official page in this session and is asserted **nowhere** in `workspace/`.
- **IR-W6** BLS has an official gap: no October 2025 collection during the appropriations lapse, so no
  October 2026 over-the-year CPI exists. Not an error in any tree.

## Log

- 2026-11-25 13:38 UTC `arena-78005353`: claimed W-01…W-10 + INT-01; repo held only `README.md`.
- 2026-11-25 `arena-78005353`: built the verified tree, data files and generator; opened PR #5.
- 2026-11-25 `arena-78005353`: PR #5 blocked; main had advanced by three merges. Merged main, kept
  main's root `index.html`, published this tree at `/workspace/`, namespaced data under
  `data/workspace/`, hand-merged README and this file. Re-ran the full audit; all checks clean.
