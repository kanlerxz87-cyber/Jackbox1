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
| T14 | GitHub Pages publish, PR, merge to main | in progress | arena-f5a16939 | .github/workflows/pages.yml |

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
