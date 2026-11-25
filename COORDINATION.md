# COORDINATION.md — Shared task board

**Repo:** `kanlerxz87-cyber/Jackbox1`
**Board convention:** one row per task; status ∈ `unclaimed | in progress | needs review | done`.
`needs review` items are published on the site's **Flagged for Review** page and do not block the merge.

---

## 0. Session claims

| Session ID | Branch | Role | Started | File scope (exclusive) |
|---|---|---|---|---|
| `S-2a61b633` | `arena/2a61b633-jackbox1` | Research + `docs/` site + final integration (observed on remote at commit `5ee5ce7`) | 2026-11-25 | `docs/**`, `private/**`, `README.md`, `.gitignore`, `COORDINATION.md` (their §1–§4) |
| `S-1552e5d5` | `arena/1552e5d5-jackbox1` | Independent line-by-line verification + published site + final integration for this branch (this file's §5 onward) | 2026-11-25 | `index.html`, `web/**` (pages, assets, data, tools), `.nojekyll`, `COORDINATION.md` (§5 onward, append-only), `SITE_REVIEW.md` |

**Claim recorded before any data work.** Five additional session branches were observed on the remote before the
site build (`arena/41ea221b-jackbox1`, `arena/78005353-jackbox1`, `arena/8c9d9d97-jackbox1`,
`arena/f5a16939-jackbox1`, `arena/2a61b633-jackbox1`). Their boards claim root `index.html`, `pages/**`,
`assets/**`, `data/**`, `site/**`, `docs/**`, `scripts/**`. To keep this session's file scope non-overlapping at
file level, **all site content lives under `web/**`** (its own pages, assets, data and tools), with only a small
root `index.html` landing page plus this append-only board section and `SITE_REVIEW.md` outside it. A second,
self-contained landing page is generated at `web/index.html`, so the deliverable survives even if another
integration session subsequently replaces the root `index.html`.

GitHub Pages on `main` is configured with source `{branch: main, path: /}`, so the root `index.html` is the live
landing page; `docs/**` and any other session's tree are served as separate paths and are not overwritten here.
This session leaves the Pages source setting unchanged.

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
| I-01 | Line-by-line repository review + `SITE_REVIEW.md` | done | S-1552e5d5 | `SITE_REVIEW.md`, `web/repo-review.html` | repo files + official docs |
| I-02 | Official source register (`web/data/sources.json`) | done | S-1552e5d5 | `web/data/sources.json` | every URL fetched in this session |
| I-03 | Verified data tables (every row = official URL or blank+flag) | done | S-1552e5d5 | `web/data/*.json`, `web/tools/build.py` | `web/tools/verify.py` |
| I-04 | Executive / printable one-page summary | done | S-1552e5d5 | `web/summary.html`, `web/print.html` | all of the above |
| I-05 | Decision gates + Q&A + missing-information discovery plan | done | S-1552e5d5 | `web/gates.html`, `web/questions.html` | framework; sourced answers only |
| I-06 | Trade area + demographics + tract trends + labour + schools + traffic | done | S-1552e5d5 | `web/economy.html`, `web/data/findings.json` | Census, BLS, CA EDD/DOF, CDE, Caltrans |
| I-07 | Tenant / operator direction (multi-year series) | done | S-1552e5d5 | `web/operator.html` | SEC EDGAR |
| I-08 | Hazard + insurance screening (parcel zone status blank until APN) | done | S-1552e5d5 | `web/hazards.html` | CAL FIRE, FEMA, CGS/USGS, CDI |
| I-09 | After-tax module + private browser-only calculator | done | S-1552e5d5 | `web/tax.html`, `web/calculator.html` | IRS, CA FTB, BOE |
| I-10 | Short-lease discount from verified quotes (no quotes → flagged) | needs review | S-1552e5d5 | `web/tax.html` (blank rows) | — |
| I-11 | Risk register incl. black-swan / business-as-usual scenarios | done | S-1552e5d5 | `web/risks.html` | official hazard + insurance sources |
| I-12 | Suggestions section with reviewer path selector | done | S-1552e5d5 | `web/suggestions.html` | advisory only, no data claims |
| I-13 | Privacy / anonymisation policy | done | S-1552e5d5 | `web/privacy.html` | CCPA/CPRA (leginfo.legislature.ca.gov) |
| I-14 | Flagged for Review page (all unverified rows + irregularities) | done | S-1552e5d5 | `web/flagged.html` | all sources |
| I-15 | Build, row verification, internal link check (deploy in I-90) | done (deploy in I-90) | S-1552e5d5 | `web/tools/*`, `web/*.html`, `web/assets/**`, root `index.html` | `web/tools/verify.py`, `web/tools/check_links.py` |
| I-90 | PR → merge to `main` → confirm Pages deploy → record PR link here | in progress | S-1552e5d5 | `COORDINATION.md` §9 | `gh` |

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

(§6 is appended as each source is fetched; see `web/data/sources.json` for the machine-readable register.)

### Additional research log (I-01 … I-15, 2026-11-25)

- I-03 — Census QuickFacts, LA County/LA City: V2025 population, 2020 Census, ACS 2020–2024
  income/housing/education, 2022 Economic Census, 2023 County Business Patterns, geography —
  <https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia,losangelescitycalifornia/INC110223> —
  all 4 chunks retrieved; notes/flags/definitions read; mixed vintages flagged (R-08).
- I-03 — CA DOF E-1 2026 press release + methodology page —
  <https://dof.ca.gov/media/docs/forecasting/demographics/estimates/e-1_2026_press_release.Pdf> and
  <https://dof.ca.gov/forecasting/demographics/estimates-e1/> — 1/1/2026 provisional and 1/1/2025
  revised city/county estimates, 11,160 housing units lost to Eaton/Palisades fires, methodology
  states summary tables do not reveal any individual.
- I-03 — BLS Economy at a Glance, LA–Long Beach–Glendale MD — <https://www.bls.gov/eag/eag.ca_losangeles_md.htm> —
  all 3 chunks retrieved; May–Oct 2026 labour, sector, CPI tables and footnotes; Oct 2026 `p` flagged (R-09).
- I-03 — CA EDD October 2026 LMI release — <https://labormarketinfo.edd.ca.gov/file/lfmonth/la$pds.pdf> —
  seasonally adjusted unemployment, nonfarm level, month/year industry changes; preliminary/benchmark noted.
- I-03 — SCAG Connect SoCal 2024 Demographics & Growth Forecast Technical Report —
  <https://www.scag.ca.gov/sites/default/files/2024-05/23-2987-tr-demographics-growth-forecast-final-040424.pdf> —
  Table 2, Figure 2 and the subregional-uncertainty statement read; labelled projection (R-14).
- I-03 — CDE LAUSD district profile and largest-district list —
  <https://www.cde.ca.gov/sdprofile/details.aspx?cds=19647330000000> and
  <https://www.cde.ca.gov/ds/ad/ceflargesmalldist.asp> — 497,105 enrollment / 81,328 EL / 5,731,260
  statewide; no address, phone or personal name reproduced.
- I-03 — Caltrans Traffic Census Program — <https://dot.ca.gov/programs/traffic-operations/census> —
  2021–2024 AADT dataset links and the state-highway-only limitation (R-16).
- I-07 — SEC EDGAR: FY2025 10-K and Q1/Q2/Q3 FY2025 earnings exhibits —
  <https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/jack-20250928.htm>,
  <https://www.sec.gov/Archives/edgar/data/807882/000080788225000013/ex991-q125earningsrelease.htm>,
  <https://www.sec.gov/Archives/edgar/data/807882/000080788225000029/ex991-q225earningsrelease.htm>,
  <https://www.sec.gov/Archives/edgar/data/807882/000080788225000042/ex991-q325earningsrelease.htm> —
  same-store sales series, units, closures, franchise rental revenues and AUV read verbatim (R-12).
- I-03/I-09 — IRS Topic 409, Topic 559, Pub. 946, Rev. Proc. 2025-32 §4.03, §1031 real-estate tips —
  <https://www.irs.gov/taxtopics/tc409>, <https://www.irs.gov/taxtopics/tc559>,
  <https://www.irs.gov/pub/irs-pdf/p946.pdf>, <https://www.irs.gov/pub/irs-drop/rp-25-32.pdf>,
  <https://www.irs.gov/businesses/small-businesses-self-employed/like-kind-exchanges-real-estate-tax-tips> —
  2025 and 2026 capital-gain thresholds, 25% §1250 ceiling, 3.8% NIIT, basis/depreciation rules,
  post-2017 real-property-only §1031.
- I-09 — CA FTB capital gains page; BOE Publication 29; LA County TTC property tax page —
  <https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html>,
  <https://www.boe.ca.gov/proptaxes/pdf/pub29.pdf>, <https://ttc.lacounty.gov/property-tax/> —
  CA capital gains as ordinary income, Prop 13 1%/2%, secured bill components/dates.
- I-08 — CAL FIRE OSFM FHSZ, FEMA Flood Maps / NFHL / NFIP, CGS Seismic Hazards Program,
  USGS UCERF3 FAQ, CDI Sustainable Insurance Strategy + May 2026 alert —
  <https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones>,
  <https://www.fema.gov/flood-maps>, <https://www.fema.gov/flood-maps/national-flood-hazard-layer>,
  <https://www.fema.gov/flood-insurance>, <https://www.conservation.ca.gov/cgs/sh/program>,
  <https://www.usgs.gov/faqs/what-probability-earthquake-will-occur-los-angeles-area-san-francisco-bay-area>,
  <https://www.insurance.ca.gov/01-consumers/180-climate-change/sustainable-insurance-strategy.Cfm>,
  <https://www.insurance.ca.gov/0400-news/0102-alerts/2026/Momentum-continues-to-build-under-Insura.cfm> —
  classifications, probabilities, portals, statewide counts; parcel status left blank (R-01, R-10, R-13).
- I-13 — CA Attorney General CCPA FAQ — <https://oag.ca.gov/privacy/ccpa> — personal/sensitive
  information definitions and rights; public-record exclusion noted (R-17).
- I-06/I-03 — LA City Planning radius-map guidelines (ZIMAS) and Census API key page —
  <https://planning.lacity.gov/odocument/21c2f80a-a107-424f-9a6d-fb9a88019d8e/Radius_Map_Guidelines.pdf>,
  <https://api.census.gov/data/key_signup.html> — ZIMAS authoritative for parcel zoning/Census Tract,
  API key required for tract ACS pulls (R-11).
- I-01/I-15 — Repository, generator, verifier and link checker reviewed line by line; see `SITE_REVIEW.md`.



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

### I-01 … I-15 completion record (2026-11-25, S-1552e5d5)

- **Sources:** 39 entries in `web/data/sources.json`; 31 fetched and read, 7 official portals for
  manual review only, 1 repository row. All published values trace to fetched pages only.
- **Verification performed:** `web/tools/build.py` (281 table rows, 0 source/value errors),
  `web/tools/verify.py` (official links in every published `<tr>`, blank/verified consistency,
  privacy pattern scan, no storage/network calls), `web/tools/check_links.py` (386 internal links,
  0 broken), and an HTTP 200 check of the landing page, 16 web pages, CSS and data files.
- **Irregularities:** G-01…G-07 plus R-08…R-18 published on `web/flagged.html`; also listed in
  `SITE_REVIEW.md` §4. All `needs review`; none blocks the build or merge.
- **Build result:** 16 static pages under `web/`, root `index.html` landing page, `.nojekyll`,
  one self-contained CSS file. No external scripts, fonts, analytics, cookies or form actions.
- **Decision status:** unchanged — no sell/renew/hold winner selected.


