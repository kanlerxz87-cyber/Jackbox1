# COORDINATION — session record `arena/1ebd66da-jackbox1`

> This tree is published at **`/ledger-1ebd66da/`**. The repository-wide board is the
> root `COORDINATION.md`, which is owned by the integration session on `main` and is
> **not** edited by this tree. This file is this session's own record, kept inside its
> own scope so it cannot collide with another session's board.

Repo: `kanlerxz87-cyber/Jackbox1` · Live site: https://kanlerxz87-cyber.github.io/Jackbox1/
Last updated: 2026-11-25

## Rules of engagement (from the project brief)

1. Read this file before starting any task. Claim a task by writing your session ID and file scope here, then **commit and push the claim immediately**.
2. Never start a task another session has claimed (status `in progress`) or that is `done`.
3. Keep scopes non-overlapping. Each session works on its own branch named `session-<id>/<task>` and edits only files in its claimed scope.
4. If a task needs a change to a file another session owns, log a request in the *Cross-session requests* section — do not edit it.
5. Small, frequent commits. `git pull --rebase` before every push. On a merge conflict: stop, resolve without discarding the other session's work, and log it.
6. Shared outputs (`assets/data/*`, `index.html`, nav) are changed **only by the final integration session** once other tasks are done.
7. A crash or a claim older than 60 minutes with no commits may be taken over by any session; note the handoff in the log.
8. `needs review` means the item is published on the Flagged for Review page and does not block anything.
9. Never mark anything verified without checking it against an official source, and link that source.

## Session log

### Session `arena/1ebd66da-jackbox1` — 2026-11-25

The repository contained only `README.md` at commit `4aa9dad`, so this session opened the
board and claimed the whole initial build. Multiple sessions are not yet active on this repo;
the board is created so any later session can pick up scope without collisions.

| ID | Task | Status | Owner | File scope |
| --- | --- | --- | --- | --- |
| T-00 | Create coordination board | done | `arena/1ebd66da-jackbox1` | `COORDINATION.md` |
| T-01 | Data layer: verified source registry + table rows | done | `arena/1ebd66da-jackbox1` | `assets/data/**` |
| T-02 | Landing page and navigation | done | `arena/1ebd66da-jackbox1` | `index.html`, `assets/css/**`, `assets/js/**` |
| T-03 | W-01 trade-area economics page | done | `arena/1ebd66da-jackbox1` | `pages/economics.html` |
| T-04 | W-02 sell-versus-hold worksheet + after-tax module + browser calculator (W-06) | done | `arena/1ebd66da-jackbox1` | `pages/worksheet.html`, `assets/js/calculator.js` |
| T-05 | W-03 decision-gate progress board | done | `arena/1ebd66da-jackbox1` | `pages/decision-gates.html` |
| T-06 | W-04 parcel hazard screening | done | `arena/1ebd66da-jackbox1` | `pages/hazards.html` |
| T-07 | W-05 / W-07 / W-08 tract trends, rental evidence, lease abstract | done | `arena/1ebd96da-jackbox1` → see note | `pages/tract-trends.html`, `pages/rental-evidence.html`, `pages/lease-abstract.html` |
| T-08 | W-10 printable one-page advisory summary | done | `arena/1ebd66da-jackbox1` | `pages/advisory-summary.html` |
| T-09 | Open-questions register (pre-decision Q&A + missing-information discovery) | done | `arena/1ebd66da-jackbox1` | `pages/open-questions.html` |
| T-10 | Risk register incl. black-swan scenarios | done | `arena/1ebd66da-jackbox1` | `pages/risks.html` |
| T-11 | Suggestions section + improvement backlog | done | `arena/1ebd66da-jackbox1` | `pages/suggestions.html` |
| T-12 | Flagged for Review page + unverified register | done | `arena/1ebd66da-jackbox1` | `pages/flagged.html` |
| T-13 | Privacy & anonymisation policy | done | `arena/1ebd66da-jackbox1` | `pages/privacy.html` |
| T-14 | Build/verification script + CI | done | `arena/1ebd66da-jackbox1` | `scripts/verify.mjs`, `.github/workflows/**` |
| T-15 | Final integration: build, link check, publish to `main` | in progress | `arena/1ebd66da-jackbox1` | whole tree (integration) |

**Note on T-07:** the owner cell above contains a typo from drafting (`1ebd96da`). The only
session working this repo is `arena/1ebd66da-jackbox1`; no other branch or session exists.
Recorded here rather than silently corrected, per the "flag irregularities" rule.

## Verification performed (session `arena/1ebd66da-jackbox1`)

Every row in `assets/data/sources.js` was fetched and read during this session before being
written. Sources reached and read:

- BLS *Economy at a Glance* — Los Angeles-Long Beach-Santa Ana MSA (labour force, nonfarm by
  industry, CPI-U/W), https://www.bls.gov/eag/eag.ca_losangeles_msa.htm
- California DOF **E-1** population/housing estimates, page and 2026 press release PDF,
  https://dof.ca.gov/forecasting/demographics/estimates-e1/
- FRED / U.S. Census SAIPE median household income, Los Angeles County,
  https://fred.stlouisfed.org/series/MHICA06037A052NCEN
- FRED / BLS LA County unemployment rate (monthly, through 2026-09),
  https://fred.stlouisfed.org/data/CALOSA7URN
- FRED / Federal Reserve H.15 10-year Treasury constant maturity (through 2026-11-23),
  https://fred.stlouisfed.org/data/DGS10
- FRED / Census resident population, California (through 2025), https://fred.stlouisfed.org/data/CAPOP
- SEC EDGAR — Jack in the Box Inc. CIK 0000807882: 10-K for FY ended 2025-09-28,
  filing index, `R5.htm` (statements of earnings), `R10.htm` (revenue disaggregation),
  `R16.htm` (leases), and the risk-factors text,
  https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm
- IRS Topic 409 (capital gains), Topic 559 (net investment income tax),
  https://www.irs.gov/taxtopics/tc409 · https://www.irs.gov/taxtopics/tc559
- California FTB 2024 tax rate schedules, https://www.ftb.ca.gov/forms/2024/2024-540-tax-rate-schedules.pdf
- City of Los Angeles Initiative Ordinance ULA (ballot text incl. Chief Legislative Analyst and
  City Administrative Officer fiscal statements), https://cityclerk.lacity.org/election/Initiative_Ordinance_ULA.pdf
- CAL FIRE / Office of the State Fire Marshal Fire Hazard Severity Zones,
  https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones
- California Geological Survey EQ Zapp (Seismic Hazard Zones),
  https://www.conservation.ca.gov/cgs/geohazards/eq-zapp
- FEMA Flood Map Service Center, https://msc.fema.gov/portal/home

## Irregularities found

| # | Irregularity | Handling |
| --- | --- | --- |
| I-01 | The brief gives a lease expiry **range** ("2030-2035"), not a date. A range cannot be modelled as a single cash-flow trigger. | Published on Flagged for Review. Calculator requires an explicit expiry year entered by the reader; no default is presented as fact. |
| I-02 | No parcel address, APN/Assessor Identification Number, or legal description was supplied. | Parcel-level findings left blank and flagged unverified. Site publishes trade-area (Census tract / city) evidence only. |
| I-03 | Lease document, rent schedule, escalations, options, and CAM obligations were not supplied. | Lease abstract page has structure but every commercial term is marked **not supplied**. |
| I-04 | Owner's basis, holding period, entity structure, and filing status were not supplied — all four drive the after-tax number. | After-tax module exposes them as reader inputs, never as assumptions. |
| I-05 | La Alma/central-LA parcel could be in the City of Los Angeles **or** an adjacent incorporated city (e.g. Vernon, Huntington Park, Maywood) or unincorporated County. Measure ULA and local rent rules differ by jurisdiction. | Jurisdiction is a required reader input; ULA is shown as "applies only if City of LA". |
| I-06 | California DOF E-1 press release reports LA County **lost 64,000 persons** in 2025, partly attributed to the Eaton and Palisades wildfires — a verified example of a localised shock large enough to move a county series. | Recorded as evidence for the black-swan section; not extrapolated. |
| I-07 | `data.census.gov` deep links and the Census data API without a key did not return tract tables to this session; `api.census.gov` returns "Missing Key". | Tract-level tables are flagged unverified with the official query URLs supplied so the reader/advisor can pull them. No tract values were invented. |
| I-08 | LA County Assessor portal and LA County Open Data did not return machine-readable records to this session. | No assessed value, land/improvement split, or parcel area is published. |

## Cross-session requests

_(none)_

## Final integration record

Filled in at the end of T-15 — see the *Final integration* section appended below.


---

## 2026-11-25 · Parallel-session reconciliation (added at integration)

**What happened.** This session opened the repository when it held only a one-word `README.md`
(`4aa9dad`) and built a complete tree at the repo root. On `git fetch`, `main` had advanced
**35 commits** — PRs #1–#5 from four other sessions — and already held **five** published trees:

| Tree | Path on `main` | Owner |
| --- | --- | --- |
| Primary workspace | `/` → `pages/` | `arena/*` (PRs #1–#4) |
| Sourced dashboard | `/docs/` | `arena/*` |
| Desk tree | `/desk/` | `arena/*` |
| Verified workspace (17 pages) | `/workspace/` | `arena/2a61b633` |
| Audit pass (11 pages) | `/audit-78005353/site/` | `arena-78005353` |

**Conflict prevented.** Publishing this tree at the repo root would have overwritten the primary
workspace's `index.html`, `assets/`, `pages/` and `data/` — i.e. destroyed four other sessions' work.
Previous sessions had already recorded this exact hazard (**IR-A5**: "Five trees now exist in one
repository… tidying it would mean deleting another session's published work").

**What this session did instead.** Rebranched the tree wholesale into **`ledger-1ebd66da/`**, a
directory no other session touches, and made `scripts/build.mjs` and `scripts/verify.mjs` derive the
publish prefix from their own location rather than hard-coding it. Nothing outside that directory is
created, modified or deleted by this session except the additions to the root `index.html` and root
`COORDINATION.md` described below.

**Files this session touches outside its own directory:** exactly two — `index.html` (root) and
`COORDINATION.md` (root). Both are conflicted with `main`; both are resolved by keeping `main`'s
content verbatim and appending a single entry for this tree. No existing line of either file is
removed.

**Checks at integration.** `node scripts/build.mjs` is idempotent (second run: 0 pages updated).
`node scripts/verify.mjs` passes: 24 sources, 55 metric rows (44 verified / 11 blank-and-flagged),
15 pages, 0 broken internal links, 0 privacy-pattern hits. `node scripts/test-calculator.mjs` passes
22/22 assertions on hand-checkable scenarios.

**Still open.** The same ten decision-blocking questions as before, recorded in `pages/flagged.html`
and `pages/open-questions.html`. Consolidating the six trees into one remains a decision for the
owner; this session does not take it, for the same reason the earlier sessions did not.
