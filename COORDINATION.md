# COORDINATION.md — Shared task board

**Repo:** `kanlerxz87-cyber/Jackbox1`
**Board owner convention:** one row per task; status ∈ `unclaimed | in progress | needs review | done`.
`needs review` items are published on the site's **Flagged for Review** page and do not block the merge.

**Session IDs in use**

| Session ID | Branch | Role | Started |
|---|---|---|---|
| `S-2a61b633` | `arena/2a61b633-jackbox1` | Research + build + final integration (this session) | 2026-11-25 |

> No other session has claimed work as of the first commit. Any later session must add a row with its own ID and a
> **non-overlapping file scope** before editing. If a task needs a file owned by another session, log the request in the
> *Change requests* section below instead of editing it.

---

## 1. Task board

| ID | Task | Status | Owner | File scope | Sources verified | Notes |
|---|---|---|---|---|---|---|
| T-00 | Board, session claim, repo scaffold | done | S-2a61b633 | `COORDINATION.md`, `README.md`, `.gitignore`, `docs/_config.yml` | n/a | Initial claim committed before any data work |
| W-01 | Replace city/county proxies with trade-area figures | in progress | S-2a61b633 | `docs/data/*`, `docs/economy.html` | Census ACS/BLS/CA DOF/EDD | Tract + place level, not county |
| W-02 | Extend private worksheet to sell-vs-hold | in progress | S-2a61b633 | `private/worksheet-sell-vs-hold.csv`, `docs/model.html` | IRS/FTB/LA County | Private file is **not** published |
| W-03 | Decision-gate progress board | in progress | S-2a61b633 | `docs/gates.html` | n/a (framework) | Gate status driven by verified-input register |
| W-04 | Parcel-level hazard screening | in progress | S-2a61b633 | `docs/hazards.html`, `docs/data/hazards.json` | CalFire / FEMA / USGS / CGS / CalOES | Parcel ID unknown → zone status left blank + flagged |
| W-05 | Same-store sales / units / closures / franchise rental evidence | in progress | S-2a61b633 | `docs/data/operator.json`, `docs/operator.html` | SEC EDGAR (JACK 10-K/10-Q) | Direction over multi-year series |
| W-06 | Private lease abstract + notice calendar | in progress | S-2a61b633 | `private/lease-abstract-template.md`, `private/notice-calendar.csv` | CA Civil Code | **Never published** |
| W-07 | After-tax module | in progress | S-2a61b633 | `docs/data/tax.json`, `docs/tax.html`, `docs/assets/js/tax.js` | IRS / CA FTB / LA County | Rates cited to primary law |
| W-08 | Price short-lease discount from real quotes | needs review | S-2a61b633 | `docs/data/market.json`, `docs/market.html` | — | No verified quote set available offline → flagged, no value published |
| W-09 | Questions / missing-information register | in progress | S-2a61b633 | `docs/questions.html`, `docs/data/questions.json` | n/a (framework) | Answers only where sourced |
| W-10 | One-page printable advisor summary | in progress | S-2a61b633 | `docs/summary.html` | all of the above | Print CSS |
| W-11 | Browser-only private calculator | in progress | S-2a61b633 | `docs/calculator.html`, `docs/assets/js/calc.js` | IRS/FTB | No network calls, no storage |
| W-12 | Neighbourhood/tract trend evidence | in progress | S-2a61b633 | `docs/tracts.html`, `docs/data/tracts.json` | Census, CA DOF, EDD, CDE, Caltrans | Regional figures kept alongside |
| W-13 | Risk register incl. black-swan events | in progress | S-2a61b633 | `docs/risks.html`, `docs/data/risks.json` | CalFire, FEMA, USGS, CDI/FAIR Plan | Scenario library, explicitly illustrative |
| W-14 | Suggestions section (reviewer can choose a path) | in progress | S-2a61b633 | `docs/suggestions.html` | n/a (advisory) | Advisory only; no data claims |
| W-15 | Privacy policy + anonymisation rules | in progress | S-2a61b633 | `docs/privacy.html` | CA CCPA/CPRA (leginfo) | No owner/parcel identifiers anywhere |
| T-90 | Final integration: merge branches, re-verify rows, link check, build, publish Pages, PR + merge, record PR link | in progress | S-2a61b633 | all of `docs/` | — | Runs last |

---

## 2. Research log (what was actually checked, and where)

Format: `task — claim — source URL — retrieved — result`.

- **W-05** — Los Angeles–Long Beach–Glendale metro area labour force / employment / unemployment rate / total nonfarm,
  May–Oct 2026. Source: <https://www.bls.gov/eag/eag.ca_losangeles_md.htm> — retrieved 2026-11-25. Result: table values
  captured verbatim (LAUS series `LAUDV06310840000000x`, CES series `SMU06310840000000001`). Oct-2026 figures marked
  preliminary (`p`) by BLS and recorded as such.

(rows appended as tasks complete — see §4 "Completion records")

---

## 3. Irregularities flagged

| # | Item | Why it matters | Status |
|---|---|---|---|
| F-01 | No street address, APN or parcel identifier was supplied | Parcel-level findings (hazard zone status, zoning, AADT, TRA tax rate, comps) **cannot** be verified. Every parcel-specific cell is left blank and marked `unverified`. | published on Flagged for Review |
| F-02 | No lease document supplied | Rent, escalations, options, co-tenancy, assignment, ROFR, holdover, and expiration year (given only as a range 2030–2035) are unverified. | published |
| F-03 | No verified arm's-length quote set for a short-lease QSR in central LA | The short-lease discount cannot be priced; no number is published (W-08). | published |
| F-04 | No assessed value, basis, purchase date, depreciation schedule, or loan terms supplied | After-tax sale comparison cannot produce a dollar result; only the mechanics are published. | published |
| F-05 | "Central Los Angeles" is not a Census geography | Trade area must be fixed to specific tracts before W-01/W-12 values can be attached to *this* parcel; representative tract sets are published as examples only. | published |

---

## 4. Completion records

(appended per task: sources, verification performed, irregularities, handoff notes)
