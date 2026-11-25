# SITE_REVIEW.md — line-by-line review and verification record
**Session:** `S-1552e5d5` · **Branch:** `arena/1552e5d5-jackbox1` · **Date:** 2026-11-25 UTC

## 1. Starting state of the repository

| Path | Finding | Verification |
|---|---|---|
| `README.md` | A 10-byte project-title placeholder (`# Jackbox1`), no trailing newline. | Read byte-for-byte with `cat -A`; no other content. |
| `.git` | Branch from `main` at `4aa9dadd7b97353252132970742afd0532a10925`; remote `origin` = `https://github.com/kanlerxz87-cyber/Jackbox1.git`. | `git status -sb`, `git log`, `git remote -v`. |
| other files | None. No `COORDINATION.md`, no `docs/`, no `private/`, no data, no site. | `find . -path ./.git -prune -o -print`. |
| GitHub Pages | API reported `built`, `legacy`, source `main:/`, `https_enforced: true`, `https://kanlerxz87-cyber.github.io/Jackbox1/`. | `gh api repos/kanlerxz87-cyber/Jackbox1/pages`; this was **not** proof that the requested site existed, because `main` had no site files. |

Five other Arena session branches were observed on the remote before the build:
`arena/2a61b633-jackbox1`, `arena/41ea221b-jackbox1`, `arena/78005353-jackbox1`,
`arena/8c9d9d97-jackbox1`, `arena/f5a16939-jackbox1`. Their boards claimed overlapping
root-level file scopes (`index.html`, `pages/**`, `assets/**`, `data/**`, `site/**`,
`docs/**`, `scripts/**`). To obey the non-overlap rule, this session placed **all** of its
content under `web/**` and only added a small root `index.html` landing page plus
`COORDINATION.md` (append-only §5+) and this review file. No other session's files were
edited, deleted or overwritten.

## 2. Files added by this session

| Path | Purpose |
|---|---|
| `COORDINATION.md` (§5 onward) | Shared task board, session claim, research log, irregularities, change requests, completion records. |
| `SITE_REVIEW.md` | This review. |
| `index.html` | Root landing page (Pages source is `main:/`), links to `web/index.html`. |
| `.nojekyll` | Prevents Jekyll processing of `web/**` assets. |
| `web/index.html` + 15 category pages | Clean dashboard-style UI: Decision / Evidence / Tools / Verification. |
| `web/assets/css/site.css` | Single self-contained stylesheet; no external fonts, scripts or trackers. |
| `web/data/sources.json` | 39 source entries, each with agency, URL, official flag, retrieval status and notes. |
| `web/data/findings.json` | 180+ finding rows with columns: id, group, metric, geography, period, value, unit, status, sources, note. |
| `web/data/questions.json`, `gates.json`, `flagged.json`, `suggestions.json`, `risks.json` | Q&A, decision gates, flagged items, reviewer path selector, risk/scenario register. |
| `web/tools/build.py` | Static generator; fails the build if any row lacks an official source or a blank/verified value is inconsistent. |
| `web/tools/verify.py` | Re-checks sources, blank/verified consistency, official links in rendered `<tr>` rows, privacy patterns, and forbidden storage/network calls. |
| `web/tools/check_links.py` | Checks all internal `href`/`src` targets exist. |

## 3. Verification performed (line by line)

1. **Official-source check.** Every row in every data table carries `sources`; every id resolves
   to `sources.json`; every URL is HTTPS and on a recognised official host (`.gov`, `ca.gov`,
   `scag.ca.gov`, `lacounty.gov`, `lacity.org`, `census.gov`, `bls.gov`, `irs.gov`, `sec.gov`,
   etc.). The single `PORTAL-GITHUB-REPO` row is used only for repository-review facts, never
   for an economic, tax or hazard value.
2. **Value check.** A row marked `verified` must have a non-blank value. A row not marked
   `verified` must have a blank value. No value is inferred from a regional proxy. Blank cells
   render as `UNVERIFIED — left blank` and are republished on **Flagged for Review**.
3. **Fetch check.** All numeric/table claims in the site come from pages retrieved and read in
   this session (Census QuickFacts all 4 chunks; BLS EAG all 3 chunks; DOF E-1 press release;
   EDD October 2026 LMI; SCAG 2024 technical report; CDE district profile and largest-district
   list; Caltrans Traffic Census; SEC FY2025 10-K and Q1/Q2/Q3 2025 exhibits; IRS Topics 409/559,
   Pub. 946, Rev. Proc. 2025-32, §1031 tips; FTB capital gains; BOE Pub. 29; LA County TTC;
   CAL FIRE OSFM FHSZ; FEMA flood maps/NFHL/NFIP; CGS seismic program; USGS UCERF3 FAQ;
   CDI Sustainable Insurance Strategy and May 2026 alert; CA AG CCPA; LA City Planning ZIMAS
   guidelines; Census API key page). Official portals that were not fetched are clearly marked
   `manual review only` and contribute **no** published value.
4. **Vintage / preliminary check.** Mixed Census vintages, BLS/EDD preliminary October 2026
   values, the open 2026 SRA FHSZ comment period, and SCAG projection assumptions are all
   flagged. Forecasts are labelled projections, not observations.
5. **Privacy scan.** All published HTML is scanned for APN-with-number patterns, street-address
   patterns, SSN patterns, owner-name patterns, and two specific addresses that appear on
   official pages but must never be reproduced. The site contains no owner/parcel identifiers,
   no lease files, no owner financials, no unit-level operating data. The private calculator
   has no `<form action>`, no external scripts, no cookies, no `localStorage`/`sessionStorage`
   writes, no `fetch`, `XMLHttpRequest` or `sendBeacon` calls.
6. **Link check.** 386 internal links across 17 HTML files resolve; 1 CSS asset present.
   External links open with `rel="noopener noreferrer"`.
7. **Build / HTTP check.** Static site generated; served with `python3 -m http.server` and
   checked: `/`, `/index.html`, `/web/index.html`, nine representative pages, CSS and data
   files all returned HTTP 200.

Command results (2026-11-25):
- `python3 web/tools/build.py` → `Built 16 pages ... Verified 281 table rows against 39 sources. Errors: 0`
- `python3 web/tools/verify.py` → `VERIFICATION PASSED`
- `python3 web/tools/check_links.py` → `LINK CHECK PASSED: no broken internal links.`

## 4. Irregularities flagged (published on Flagged for Review)

G-01 no APN/address/parcel ID · G-02 no lease document (expiry only 2030–2035) · G-03 no owner
financials · G-04 no verified short-lease quote set · G-05 “central Los Angeles” is not a Census
geography · G-06 repo initially only a 10-byte placeholder · G-07 five parallel sessions claimed
overlapping scopes · plus R-08…R-18: mixed Census vintages, preliminary BLS/EDD values, open
2026 SRA comment period, Census API key requirement, systemwide SEC data vs unit data,
statewide CDI insurance counts vs property quotes, SCAG subregional uncertainty, no comparable
history for a back-test, Caltrans AADT coverage limits, CCPA public-record exclusion, and
tax-year/filing-status threshold differences.

All are `needs review` and therefore published on the labelled page; they do not block the
site build or merge, but they do block a decision.

## 5. Decision status

**No sell / renew / hold winner is selected.** Verified public evidence supports a regional
profile, not a parcel-level investment conclusion. The only published recommendation is a
gated process: protect privacy → fix the tract set → abstract the lease and notice calendar →
verify parcel hazards/planning/traffic/schools/competitors → collect real quotes/comps and a
negotiated renewal → compute the after-tax sale case locally → back-test a versioned cash-flow
model only when verified inputs and sufficient comparable history exist → choose a risk-balanced
path privately with authorized advisers.

## 6. Sources, merge and deploy

The machine-readable register is `web/data/sources.json`; the human-readable register with
manual-review links is `web/sources.html`. PR link, merge result and Pages deployment
confirmation are recorded in `COORDINATION.md` §9 after integration.
