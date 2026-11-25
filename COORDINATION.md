---

## Session `arena/2a61b633-jackbox1` — additive work (PR opening after this merge)

**Scope discipline.** This session arrived to an empty repo (`4aa9dad`) *before* PRs #1–#4 landed.
It rebased onto `main` rather than overwriting: its site is published at **`/workspace/`** so that the
existing `/` and `/docs/` trees are untouched. No file owned by another session was edited.

| ID | Task | Status | Owner | File scope (exclusive to this session) |
|---|---|---|---|---|
| S-01 | Verified data registry with enforced source links | done | `arena/2a61b633` | `data/registry.yaml`, `data/tracts_demo_90015.csv` |
| S-02 | Static generator + integrity checks | done | `arena/2a61b633` | `tools/build.py`, `tools/check.py`, `tools/reverify.py` |
| S-03 | 17-page verified site (W-01…W-14) | done | `arena/2a61b633` | `workspace/` |
| S-04 | Private lease-abstract / notice-calendar / sell-vs-hold templates | done | `arena/2a61b633` | `private/` (gitignored) |

**Irregularities found on `main` and fixed in this merge (see also `workspace/review.html`):**

| # | Finding | Resolution |
|---|---|---|
| M-01 | `README.md` on `main` contained unresolved merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) — the file was published as-is on the live repo | Resolved: primary README kept, earlier root-tree description preserved as a quoted section |
| M-02 | `COORDINATION.md` on `main` contained the same unresolved markers | Resolved: board preserved, conflict block folded into this session section |
| M-03 | Three parallel static trees (`/`, `/docs/`, `/desk/`) plus this session's fourth | Not merged into one; each kept and cross-referenced. Consolidation remains a decision for the owner |

**Verification performed in this session** (all re-checkable via the links in `workspace/sources.html`):

- BLS public API (`api.bls.gov`): LAUS city series, CES metro series, CPI-U metro series — values captured verbatim, `P`/`G`/`X` footnotes preserved.
- SEC EDGAR: JACK 10-K FY2023/FY2024/FY2025 XBRL note pages (units, royalties, rental revenue, segment profit, leases) and the 8-K on the Del Taco sale.
- Census: ACS 2020–2024 5-year via Census Reporter's mirror of the Census API (city, county, metro, 23 tract rows); QuickFacts for the V2025 estimate.
- FRED: DGS10 daily series, re-pulled to 2026-11-23.
- Primary law: Cal. Const. Art. XIII A §§1–2; RTC §§11911, 17043; 26 U.S.C. §168; IRS Topic 409, NIIT, 1031; FTB 2025 schedules; LAHD Measure ULA.
- Hazards: CAL FIRE OSFM FHSZ statute and map vintages; CGS Alquist-Priolo; FEMA NRI v1.20 and NFHL.

**Build/check result at merge:** `python3 tools/build.py` → 17 pages from 72 rows (57 verified / 5 flagged / 10 blank);
`python3 tools/check.py` → all internal links and anchors resolve, every data row carries a badge, no external scripts, no storage calls.

### 2026-11-25 · `arena/2a61b633-jackbox1` — final integration record

- Merged `origin/main` (PRs #1–#4) into this branch; **no other session's file was deleted or overwritten**.
- Resolved the two pre-existing conflict-marker files (`README.md`, `COORDINATION.md`) — recorded as **M-01/M-02**.
- Corrected four stale external links (OSFM ×2, CGS EQ Zapp, FEMA portal) — recorded as **F-11** on `workspace/review.html`.
- Re-verified the combined tree: **772 internal links across all four trees, 0 broken**; HTML nesting checked on
  every page (0 structural errors); `tools/check.py` green.
- Build: 17 pages, 72 registry rows — 57 verified / 5 flagged / 10 blank.
- Publishing target for this session: `/workspace/` (repo root remains the Pages source; additive only).


---

# Audit pass `arena-78005353` — record

Claimed at 13:38 UTC on 2026-11-25 when the repository held only a one-word `README.md` (`4aa9dad`).
Main advanced seven times during the session. This record covers what this pass built and how the
conflicts were resolved.

## Where this tree is published

This pass is published at **`/audit-78005353/site/`**, with its data at **`data/audit-78005353/`**.
It was moved twice during the session to avoid overwriting other sessions' work: first from the repo
root, then from `/workspace/` after another session published a 17-page tree there.

## What makes this pass distinct

It is an independent second opinion on the same question, built from primary sources read directly:

| | |
|---|---|
| **Evidence register** | 47 rows; **40 read from the linked official page**, 7 left blank and published with the attempted URL |
| **Ledger audit** | all 40 numeric values and 11 tenant facts re-checked against the fetched content — **0 mismatches** |
| **Decision gates** | 7 gates; 6 not closed; the single closed gate is the privacy control |
| **Questions** | 23 gating questions, 8 blocking, each with an owner and a source |
| **Suggestions** | 16, each with effort, cost, falsifier and a privacy verdict |
| **Options** | 5 (sell now, renew then sell, hold, 1031, redevelop), each with its own falsifier |
| **Calculator** | after-tax sell-vs-renew, browser-side, no network call, no storage |
| **Print** | one-page advisor brief with a dedicated print stylesheet |

## Sources fetched by this pass (all official)

Census QuickFacts (city); BLS LA Area Economic Summary PDF; BLS CPI Los Angeles release; BLS Public
Data API `LAUMT063108000000003` and `SMU06310800000000001`; FHFA HPI 2026Q3 report; SEC EDGAR Form
10-K FY2025 (accession `0000807882-25-000072`); IRS Topics 409 and 704; IRS NIIT Q&A; IRS 1031
guidance; FTB 2024 and 2025 rate schedules; FTB Publication 1100; FTB capital-gains page; CA DIR
minimum-wage FAQ; LA County Assessor Proposition 13 and decline-in-value pages; FEMA Flood Map
Service Center; CAL FIRE OSFM Fire Hazard Severity Zones; USGS earthquake hazards and NSHM toolbox;
FEMA National Risk Index / RAPT; U.S. Treasury daily par yield curve; Caltrans Traffic Census; LA City
Planning; CAASPP Reporting; HUD FY2026 FMR documentation.

## Checks run at integration

| Check | Result |
|---|---|
| Generator is idempotent (rebuild produces no diff) | pass |
| HTML parse of all 11 pages of this tree | 0 tag errors, 0 unclosed elements |
| Link audit across **all 48 HTML files** in the repo | **0 broken links** |
| Conflict markers anywhere in the repo | none |
| Privacy scan for street-address / APN patterns | none found |
| JS field wiring (21 element IDs) and `node --check` | pass |
| No external CSS / JS / font / analytics in this tree | pass |

## Irregularities recorded by this pass

- **IR-A1** Two official, non-comparable population vintages are in use across trees: Vintage 2024
  (3,878,704) and QuickFacts V2025 (3,869,089). Both are correct for their vintage; consistent with
  `arena-41ea221b`'s IR-13. This tree uses V2025 and states the vintage on every row.
- **IR-A2** Reader-specific fetch failures, each with the attempted URL, are enumerated on
  `audit-78005353/site/flagged.html` (FR-01 … FR-14): Census county QuickFacts, CA DIR fast-food wage,
  CGS Alquist-Priolo, HUD FMR, CA FAIR Plan, and the retired CAL FIRE FHSZ URL.
- **IR-A3** The widely reported **$20.00** California fast-food minimum wage could not be confirmed on
  an official page in this pass and is **asserted nowhere** in this tree. Only the verified $16.90
  general rate is used.
- **IR-A4** BLS has an official gap: no October 2025 collection during the appropriations lapse, so no
  October 2026 over-the-year CPI exists. Not an error in any tree.
- **IR-A5** Five trees now exist in one repository. This is a coordination failure, not a design
  choice; it is recorded rather than tidied away, because tidying it would mean deleting another
  session's published work.
- **IR-A6** A GitHub Pages site is not an access-controlled workspace. Every tree says so.

## Log

- 2026-11-25 13:38 UTC `arena-78005353`: claimed W-01…W-10 + INT-01; repo held only `README.md`.
- 2026-11-25 `arena-78005353`: built the tree, data files and generator; opened PR #5.
- 2026-11-25 `arena-78005353`: PR #5 blocked three times as main advanced. Each time main was merged
  rather than force-pushed; no other session's file was overwritten. Published finally at
  `/audit-78005353/`.
