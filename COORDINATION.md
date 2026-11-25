# COORDINATION.md — Shared task board

**Repo:** `kanlerxz87-cyber/Jackbox1`
**Board convention:** one row per task; status ∈ `unclaimed | in progress | needs review | done`.
`needs review` items are published on the site's **Flagged for Review** page and do not block the merge.

---

## 0. Session claims

| Session ID | Branch | Role | Started | File scope (exclusive) |
|---|---|---|---|---|
| `S-2a61b633` | `arena/2a61b633-jackbox1` | Research + `docs/` site + final integration (observed on remote at commit `5ee5ce7`) | 2026-11-25 | `docs/**`, `private/**`, `README.md`, `.gitignore`, `COORDINATION.md` (their §1–§4) |
| `S-1552e5d5` | `arena/1552e5d5-jackbox1` | Independent line-by-line verification + root-level published site + final integration for this branch (this file's §5 onward) | 2026-11-25 | `index.html`, `pages/**`, `assets/**`, `data/**`, `tools/**`, `.nojekyll`, `COORDINATION.md` (§5 onward, append-only), `SITE_REVIEW.md` |

**Claim recorded before any data work.** Scopes are non-overlapping at file level: the other session owns `docs/**`;
this session owns the root-level published site and its own append-only board section. GitHub Pages on `main` is
currently configured with source `{branch: main, path: /}`, so the root `index.html` is the live landing page;
`docs/**` (if it lands on `main`) remains reachable at `/docs/` and is not overwritten by this session.

### Platform constraints logged as deviations (for reviewer)

- **D-01** — This session is fixed to branch `arena/1552e5d5-jackbox1` by the workspace. It cannot create
  `session-<id>/<task>` worktrees or push to any other branch. All work therefore happens on the current branch,
  which also serves as this branch's integration branch. No other branch is created, renamed or pushed to.
- **D-02** — S-2a61b633 claimed every `W-*` task and `T-90` on its own branch. Because branch file trees do not
  overlap, this session does not edit any of their files. The equivalent work is registered below as independent
  tasks `I-*` with a different file scope; the duplication is intentional (two independent verification passes)
  and is reconciled at `main` by the change request in §8.
- **D-03** — "Shared outputs are changed only by a final integration session": on this branch, this session is
  that integration session (no other session shares this branch). The root site's index, navigation and table
  data are built here from `data/**`, re-verified row by row with `tools/verify.py`, and link-checked with
  `tools/check_links.py` before the PR.

---

## 1–4. Other session's board (S-2a61b633, verbatim snapshot from commit `5ee5ce7`)

> Snapshot taken 2026-11-25 by `S-1552e5d5` via `git show 5ee5ce7:COORDINATION.md`. **Do not edit these rows.**
> Their task IDs (`T-00`, `W-01`…`W-15`, `T-90`) are claimed by `S-2a61b633`; their statuses live on their branch.

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T-00 | Board, session claim, repo scaffold | done | S-2a61b633 | `COORDINATION.md`, `README.md`, `.gitignore`, `docs/_config.yml` |
| W-01 | Replace city/county proxies with trade-area figures | in progress | S-2a61b633 | `docs/data/*`, `docs/economy.html` |
| W-02 | Extend private worksheet to sell-vs-hold | in progress | S-2a61b633 | `private/worksheet-sell-vs-hold.csv`, `docs/model.html` |
| W-03 | Decision-gate progress board | in progress | S-2a61b633 | `docs/gates.html` |
| W-04 | Parcel-level hazard screening | in progress | S-2a61b633 | `docs/hazards.html`, `docs/data/hazards.json` |
| W-05 | Same-store sales / units / closures / franchise rental evidence | in progress | S-2a61b633 | `docs/data/operator.json`, `docs/operator.html` |
| W-06 | Private lease abstract + notice calendar | in progress | S-2a61b633 | `private/lease-abstract-template.md`, `private/notice-calendar.csv` |
| W-07 | After-tax module | in progress | S-2a61b633 | `docs/data/tax.json`, `docs/tax.html`, `docs/assets/js/tax.js` |
| W-08 | Price short-lease discount from real quotes | needs review | S-2a61b633 | `docs/data/market.json`, `docs/market.html` |
| W-09 | Questions / missing-information register | in progress | S-2a61b633 | `docs/questions.html`, `docs/data/questions.json` |
| W-10 | One-page printable advisor summary | in progress | S-2a61b633 | `docs/summary.html` |
| W-11 | Browser-only private calculator | in progress | S-2a61b633 | `docs/calculator.html`, `docs/assets/js/calc.js` |
| W-12 | Neighbourhood/tract trend evidence | in progress | S-2a61b633 | `docs/tracts.html`, `docs/data/tracts.json` |
| W-13 | Risk register incl. black-swan events | in progress | S-2a61b633 | `docs/risks.html`, `docs/data/risks.json` |
| W-14 | Suggestions section (reviewer can choose a path) | in progress | S-2a61b633 | `docs/suggestions.html` |
| W-15 | Privacy policy + anonymisation rules | in progress | S-2a61b633 | `docs/privacy.html` |
| T-90 | Final integration: merge branches, re-verify rows, link check, build, publish Pages, PR + merge, record PR link | in progress | S-2a61b633 | all of `docs/` |

Their flagged irregularities (verbatim): F-01 no address/APN; F-02 no lease document; F-03 no verified
arm's-length short-lease quote set; F-04 no assessed value / basis / loan terms; F-05 "central Los Angeles" is
not a Census geography.

---

## 5. This session's task board (`S-1552e5d5`)

| ID | Task | Status | Owner | File scope | Sources / verification |
|---|---|---|---|---|---|
| I-00 | Board + session claim, commit and push | done | S-1552e5d5 | `COORDINATION.md` | n/a |
| I-01 | Line-by-line repository review + `SITE_REVIEW.md` | in progress | S-1552e5d5 | `SITE_REVIEW.md`, `pages/repo-review.html` | repo files + official docs |
| I-02 | Official source register (`data/sources.json`) | in progress | S-1552e5d5 | `data/sources.json` | every URL fetched in this session |
| I-03 | Verified data tables (every row = official URL or blank+flag) | in progress | S-1552e5d5 | `data/*.json`, `tools/build.py` | `tools/verify.py` |
| I-04 | Executive / printable one-page summary | in progress | S-1552e5d5 | `pages/summary.html` | all of the above |
| I-05 | Decision gates + Q&A + missing-information discovery plan | in progress | S-1552e5d5 | `pages/gates.html`, `pages/questions.html` | framework; sourced answers only |
| I-06 | Trade area + demographics + tract trends + labour + schools + traffic | in progress | S-1552e5d5 | `pages/economy.html`, `pages/tracts.html` | Census, BLS, CA EDD/DOF, CDE, Caltrans |
| I-07 | Tenant / operator direction (multi-year series) | in progress | S-1552e5d5 | `pages/operator.html` | SEC EDGAR |
| I-08 | Hazard + insurance screening (parcel zone status blank until APN) | in progress | S-1552e5d5 | `pages/hazards.html` | CAL FIRE, FEMA, CGS/USGS, CDI |
| I-09 | After-tax module + private browser-only calculator | in progress | S-1552e5d5 | `pages/tax.html`, `pages/calculator.html`, `assets/js/*.js` | IRS, CA FTB, BOE |
| I-10 | Short-lease discount from verified quotes (no quotes → flagged) | needs review | S-1552e5d5 | `pages/market.html` | — |
| I-11 | Risk register incl. black-swan / business-as-usual scenarios | in progress | S-1552e5d5 | `pages/risks.html` | official hazard + insurance sources |
| I-12 | Suggestions section with reviewer path selector | in progress | S-1552e5d5 | `pages/suggestions.html` | advisory only, no data claims |
| I-13 | Privacy / anonymisation policy | in progress | S-1552e5d5 | `pages/privacy.html` | CCPA/CPRA (leginfo.legislature.ca.gov) |
| I-14 | Flagged for Review page (all unverified rows + irregularities) | in progress | S-1552e5d5 | `pages/flagged.html` | all sources |
| I-15 | Build, row verification, internal link check, Pages deployment | in progress | S-1552e5d5 | `tools/*`, `index.html`, `assets/**` | `tools/verify.py`, `tools/check_links.py` |
| I-90 | PR → merge to `main` → confirm Pages deploy → record PR link here | unclaimed | S-1552e5d5 | `COORDINATION.md` §9 | `gh` |

---

## 6. Research log (`S-1552e5d5`)

Format: `task — claim — source URL — retrieved — result`. Only claims actually fetched and read are logged.

- I-03 — IRS Topic 409, capital gains: 0%/15%/20% thresholds for tax year 2025; unrecaptured §1250 gain max 25% —
  <https://www.irs.gov/taxtopics/tc409> — retrieved 2026-11-25 — read verbatim on the page.
- I-03 — IRS Topic 559, NIIT 3.8% on lesser of NII or MAGI excess; thresholds $250k/$125k/$200k —
  <https://www.irs.gov/taxtopics/tc559> — retrieved 2026-11-25 — read verbatim on the page.
- I-03 — IRS like-kind exchange tax tips: §1031 limited to real property since 1 Jan 2018; boot recognized —
  <https://www.irs.gov/businesses/small-businesses-self-employed/like-kind-exchanges-real-estate-tax-tips> —
  retrieved 2026-11-25 — read verbatim on the page.
- I-03 — BLS Economy at a Glance, Los Angeles–Long Beach–Glendale, CA MD: May–Oct 2026 labour force,
  employment, unemployment rate, total nonfarm and 12-month % change — <https://www.bls.gov/eag/eag.ca_losangeles_md.htm> —
  retrieved 2026-11-25 — Oct 2026 values marked preliminary (`p`) by BLS.
- I-03 — Census QuickFacts, Los Angeles County / Los Angeles city —
  <https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia,losangelescitycalifornia/INC110223> —
  retrieved 2026-11-25 — V2025 population estimates, 2020–2024 income, housing, education, business figures.

(§6 is appended as each source is fetched; see `data/sources.json` for the machine-readable register.)

---

## 7. Irregularities flagged by this session (published on Flagged for Review)

| # | Item | Why it matters | Status |
|---|---|---|---|
| G-01 | No street address, APN, parcel ID, or tract was supplied | Every parcel-specific value (hazard zone, zoning, AADT, tax rate, comps, tract trend) must be left blank and flagged unverified. | published |
| G-02 | No lease document; expiry given only as a range 2030–2035 | Rent, escalations, options, notice deadlines, co-tenancy, assignment, ROFR, holdover cannot be verified. | published |
| G-03 | No owner financials, basis, purchase date, depreciation schedule or loan terms | No after-tax dollar result can be published; only verified mechanics and a browser-only calculator. | published |
| G-04 | No verified arm's-length short-lease QSR quote set | Short-lease discount cannot be priced; no number is published. | published |
| G-05 | "Central Los Angeles" is not a Census geography | City/county figures are proxies only; a fixed tract set is required in a private workflow. | published |
| G-06 | Repository initially contained only `# Jackbox1` | No source register, privacy notice, licence, or dataset existed to review line by line. | published |
| G-07 | Two sessions claimed final integration on two branches | Pages source must be reconciled at `main` (see §8). | published |

---

## 8. Change requests (files owned by another session are NOT edited)

| # | To | Request | Status |
|---|---|---|---|
| C-01 | S-2a61b633 | Before merging `docs/**` to `main`, confirm GitHub Pages source. This session leaves the existing source `{branch: main, path: /}` unchanged, so root `index.html` is the landing page and `docs/` is served at `/docs/`. If you switch Pages to `/docs`, add a root redirect so neither site breaks. | open |
| C-02 | S-2a61b633 | `COORDINATION.md` is claimed by both sessions. This session only appends §5 onward; please keep §1–§4 and append rather than overwrite. | open |
| C-03 | S-2a61b633 | `README.md` and `.gitignore` are yours; this session writes `SITE_REVIEW.md` instead. | open |

---

## 9. Completion records / merge log

(appended per task: sources, verification performed, irregularities, PR link, merge result, Pages deployment)
