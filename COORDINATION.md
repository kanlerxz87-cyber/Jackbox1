# COORDINATION

Shared task board for parallel sessions. Claim a task before editing files. Do not edit files owned by
another active claim.

Privacy rule (all sessions): no owner names, no street addresses, no APNs, no lease PDFs, no tax
returns, no tenant-unit sales for the subject site. Public pages use placeholders only.

---

## Merge record — 2026-11-25 (integration session `arena-78005353`)

Three sessions built three independent trees. **Nothing was discarded.**

| Tree | Session | Path | Pages |
|---|---|---|---|
| Desk home + pages | `arena-8c9d9d97` | `/index.html`, `/pages/` | 9 |
| Sourced dashboard | `arena-f5a16939` | `/docs/` | 16 |
| Verified workspace | `arena-78005353` | `/workspace/` | 11 |

**Conflict resolution.** A three-way conflict on `index.html` (root) was resolved by **keeping main's
desk home** rather than overwriting it, and publishing the newer tree as a self-contained
`/workspace/` section. `README.md` and `COORDINATION.md` were merged by hand, retaining both sessions'
records. No file owned by another session was rewritten; the only edit made to a foreign file is a
single navigation strip inserted into `index.html` and `docs/index.html`, which adds links to the
sibling sections and removes nothing.

**Divergence logged.** `arena-f5a16939` recorded "no sell/renew winner, by design"; `arena-78005353`
also issues no recommendation. Both trees use Census figures; the desk tree cites the Vintage 2024
release (3,878,704) while the verified workspace cites QuickFacts V2025 (3,869,089). Both are correct
for their own vintage and are labelled as such — see irregularity I-01 below.

---

## Task board (all sessions)

### `arena-8c9d9d97` — desk home + pages
| ID | Task | Status | Files |
|---|---|---|---|
| A1 | Initial privacy-first site, research, verification and integration | needs review | `index.html`, `assets/*`, `pages/*` |

### `arena-f5a16939` — sourced dashboard
| ID | Task | Status | Files |
|---|---|---|---|
| T0 | Create coordination board | done | `COORDINATION.md` |
| T1 | Privacy policy, placeholders, internal-use notice | done | `docs/privacy.html`, `docs/js/nav.js` |
| T2 | W-01 trade-area vs city/county proxies | done | `docs/trade-area.html`, `docs/data/findings.json` |
| T3 | Tenant system evidence | done | `docs/tenant.html`, `docs/data/findings.json` |
| T4 | W-04 parcel hazard screening (maps only; parcel blank) | done | `docs/hazards.html` |
| T5 | W-02 sell-versus-hold worksheet (no winner) | done | `docs/sell-vs-hold.html` |
| T6 | After-tax module (verified tax rules only) | done | `docs/after-tax.html` |
| T7 | Private in-browser calculator | done | `docs/calculator.html`, `docs/js/calculator.js` |
| T8 | W-03 decision-gate board | done | `docs/decision-gate.html` |
| T9 | Questions, missing information, discovery path | done | `docs/questions.html` |
| T10 | W-10 one-page printable advisor summary | done | `docs/advisor-summary.html` |
| T11 | Suggestions for site and decision process | done | `docs/suggestions.html` |
| T12 | Flagged for Review page | done | `docs/flagged.html` |
| T13 | Site shell, dashboard, sources, methods | done | `docs/index.html`, `docs/sources.html`, `docs/methods.html` |
| T14 | GitHub Pages publish, PR, merge to main | done | legacy Pages from `main` `/` |

### `arena-78005353` — verified workspace (this session)
| ID | Task | Status | Files |
|---|---|---|---|
| W-01 | Replace city/county proxies with trade-area figures | done (method published; figures private) | `workspace/location.html`, `data/market.json` |
| W-02 | Extend private worksheet to sell-vs-hold comparison | done | `workspace/sell-vs-renew.html`, `workspace/assets/js/calc.js` |
| W-03 | Decision-gate progress board | done | `data/gates.json`, `workspace/index.html`, `workspace/gates.html` |
| W-04 | Parcel-level hazard screening | done (programmes verified; parcel rows withheld — FR-03) | `data/hazards.json`, `workspace/hazards.html` |
| W-05 | Question/information/answer register | done | `data/questions.json`, `workspace/questions.html` |
| W-06 | Suggestions register + review page | done | `data/suggestions.json`, `workspace/suggestions.html` |
| W-07 | Verification + flagged register | done | `data/flagged.json`, `workspace/flagged.html`, `workspace/sources.html` |
| W-08 | Market & economy pages | done (schools + county blank — FR-01/FR-04) | `data/market.json`, `data/tenant.json`, `workspace/market.html` |
| W-09 | After-tax module + short-lease discount | done (discount unpriced — FR-09) | `data/tax.json`, `workspace/sell-vs-renew.html` |
| W-10 | One-page printable advisor summary | done | `workspace/advisor-summary.html` |
| INT-01 | Integration: reconcile branches, re-verify, build, PR, merge, Pages | done | this file, `README.md`, `index.html`, `docs/index.html` |

---

## Verification performed by `arena-78005353`

- **40 of 47** market rows read from the linked official page; **7 left blank** and published with the
  attempted URL. Automated ledger audit: 40/40 numeric values and 11/11 tenant facts re-checked against
  the fetched content — **0 mismatches**.
- Official sources actually fetched: Census QuickFacts (city), BLS LA Area Economic Summary PDF, BLS
  CPI Los Angeles release, BLS Public Data API series `LAUMT063108000000003` and `SMU06310800000000001`,
  FHFA HPI 2026Q3 report, SEC EDGAR 10-K FY2025 (CIK 0000807882, accession 0000807882-25-000072), IRS
  Topics 409 and 704, IRS NIIT Q&A, IRS 1031 guidance, FTB 2024 and 2025 rate schedules, FTB Pub 1100,
  FTB capital-gains page, CA DIR minimum-wage FAQ, LA County Assessor Proposition 13 and DIV pages,
  FEMA Flood Map Service Center, CAL FIRE OSFM FHSZ, USGS earthquake hazards, FEMA NRI/RAPT, U.S.
  Treasury daily yield curve, Caltrans traffic census, LA City Planning, CAASPP reporting, HUD FMR.
- HTML parse check on all 11 workspace pages: **0 tag errors, 0 unclosed elements**.
- Cross-tree link audit over **all 36 pages** of all three trees: **0 broken links**.
- Calculator verified: all 21 element IDs referenced by `calc.js` exist; `node --check` passes; no
  network call, storage or analytics in the script.

## Irregularities across the whole repository

- **I-01 Vintage divergence.** Desk tree cites Census Vintage 2024 (LA city 3,878,704); verified
  workspace cites QuickFacts V2025 (3,869,089). Both are correct for their own vintage and each is
  labelled. Neither is wrong; they are not interchangeable.
- **I-02 Three static trees** (`/`, `/pages/`, `/docs/`, `/workspace/`). Kept deliberately rather than
  discarding another session's work. Unified by a navigation strip on all three index pages.
- **I-03 Public GitHub remote.** A GitHub Pages site is not an access-controlled workspace; private
  material must never be committed here. All three trees state this.
- **I-04 Reader-specific fetch failures** are enumerated on `workspace/flagged.html` (FR-01 … FR-14),
  including Census county QuickFacts, CA DIR fast-food wage, CGS Alquist-Priolo, HUD FMR and the CA
  FAIR Plan page. Each carries the attempted URL.
- **I-05** The old CAL FIRE FHSZ URL is a 404; the programme is confirmed at the OSFM domain.
- **I-06** BLS has an official gap: no October 2025 collection because of the appropriations lapse, so
  no October 2026 over-the-year CPI exists. Not an error in any tree.

## Log

- 2026-11-25 `arena-8c9d9d97`: built root static anonymous site. PR #1 merged. Status needs review.
- 2026-11-25 `arena-f5a16939`: built `docs/` tree. PR #2 merged after merging main without deleting the
  root site. Legacy Pages from `/` confirmed.
- 2026-11-25 `arena-78005353`: claimed W-01…W-10 + INT-01 at 13:38 UTC when the repo held only a
  one-word README and no claims. Built the verified workspace tree, data files and generator.
- 2026-11-25 `arena-78005353`: opened PR #5; merge blocked because main had advanced by two merges.
  Fetched main, merged it, **kept main's root `index.html`** rather than overwriting the desk home,
  published the new tree at `/workspace/`, added the cross-section navigation strip to all three index
  pages, hand-merged README and this file retaining every session's record. Re-ran the full audit:
  build clean, 0 broken links across 36 pages, 0 tag errors.
