# COORDINATION

Shared task board for parallel sessions. Claim a task before editing files. Do not edit files owned by another active claim.

**Repo branch for this Arena session:** `arena/f5a16939-jackbox1`  
**Session ID:** `arena-f5a16939`  
**Started:** 2026-11-25  

Privacy rule (all sessions): no owner names, no street addresses, no APNs, no lease PDFs, no tax returns, no tenant-unit sales for the subject site. Public pages use placeholders only.

## Tasks

| ID | Task | Status | Owner | Files |
| --- | --- | --- | --- | --- |
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
| T14 | GitHub Pages publish, PR, merge to main | in progress | arena-f5a16939 | .github/workflows/pages.yml |

## Verification performed

- Census Vintage 2024 press release CB25-77 fetched: LA city 3,878,704; +31,276.
- Census Reporter ACS 2024 1-year city and county profiles fetched (flagged as republisher).
- EDD September 2025 release fetched: LA County NSA unemployment 5.9%.
- JACK FY 2025 earnings release fetched: SSS, units, closures, guidance.
- IRS Topic 409, NIIT FAQ, like-kind tips fetched.
- USGS UCERF3 FAQ fetched.
- FTB 2025 540 booklet fetched (top rate / BHST; full brackets not copied).
- SEC 10-K iXBRL fetched but dollar lines not confirmed → franchise rental revenue left blank.

## Irregularities

- Public GitHub remote.
- data.census.gov and census.gov QuickFacts fetches failed; QuickFacts numbers not used.
- No parcel-level anything, by design.
- No sell/renew winner, by design.

## Log

- 2026-11-25 arena-f5a16939: Repo contained only README.md. Created this board. Claimed T1–T13.
- 2026-11-25 arena-f5a16939: Published static site under docs/. T1–T13 done. Starting T14 PR/merge/Pages.
