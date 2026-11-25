# COORDINATION.md — Jackbox1 Shared Task Board

## Protocol
- Before starting, read this file. Claim a task by writing your session ID and file scope, then commit and push the claim immediately.
- Never start a task another session has claimed. Keep scopes non-overlapping.
- If a task requires changing a file owned by another session, log the request here instead of editing it.
- Make small, frequent commits and run `git pull --rebase` before every push.
- If you hit a merge conflict, stop, resolve without discarding other session work, and log what happened.
- When finished, record sources, verification performed, and any irregularities; mark done.
- Never mark anything verified without checking it against an official source and linking that source.
- Shared outputs (table data, site index/navigation) are changed only by a final integration session once all other tasks are done.
- Flagged irregularities and unverified items do not block merge; publish them on "Flagged for Review" page.
- If a claim is >60 minutes old with no commits, another session may take over and note the handoff.

## Current Session
- **Session ID:** `ee4cc19f`
- **Branch:** `arena/ee4cc19f-jackbox1`
- **Base:** `4aa9dadd7b97353252132970742afd0532a10925` (main)
- **Started:** 2026-11-25 (session)
- **Role:** Full delivery + integration (single active session observed)

## Tasks

| Task ID | Task | Status | Owner | Scope (files/dirs) | Started | Last Update | Notes |
|---|---|---|---|---|---|---|---|
| T-001 | Create COORDINATION.md and claim work | done | ee4cc19f | `COORDINATION.md` | 2026-11-25 | 2026-11-25 | Claimed and maintained by ee4cc19f. |
| T-002 | Build static GitHub Pages site scaffold & navigation | done | ee4cc19f | `docs/**`, `.github/workflows/pages.yml`, `README.md` | 2026-11-25 | 2026-11-25 | Static site in `docs/`, Pages workflow added, local link check passed (9 HTML files, 0 missing local refs). |
| T-003 | Privacy & anonymization framework / data-handling policy page | done | ee4cc19f | `docs/privacy.html`, `docs/data/**` | 2026-11-25 | 2026-11-25 | No PII published; placeholders documented; privacy controls table included. |
| T-004 | Official-source research: area demographics/economy/hazards/market | done | ee4cc19f | `docs/research.html`, `docs/hazards.html`, `docs/sources.html` | 2026-11-25 | 2026-11-25 | Verified Census QuickFacts LA city values and USGS LA earthquake probabilities via official pages. BLS/EDD/other tools cited as official sources; dynamic values not pinned where not verified. |
| T-005 | Decision framework: sell vs renew, risks, questions, suggestions | done | ee4cc19f | `docs/analysis.html`, `docs/questions.html`, `docs/suggestions.html` | 2026-11-25 | 2026-11-25 | No sell/renew winner selected; decision gates, missing inputs, after-tax template, risk register, suggestions included. |
| T-006 | Verification pass, flagged review page, build check | done | ee4cc19f | `docs/flagged.html`, `COORDINATION.md`, all docs | 2026-11-25 | 2026-11-25 | Local link check passed; flagged items published; unverified values left blank. |
| T-007 | PR, merge, GitHub Pages deploy confirmation | in_progress | ee4cc19f | repo-wide | 2026-11-25 | 2026-11-25 | Will create PR, merge, and confirm Pages deployment. |

## Requests / Cross-session Notes
| Time (UTC) | From | To | Request | Status |
|---|---|---|---|---|
| 2026-11-25 | ee4cc19f | any | No other active sessions observed. Single-session full delivery. | n/a |

## Verification Log
| Time (UTC) | Task | Source / Check | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | T-004 | https://www.census.gov/quickfacts/fact/table/losangelescitycalifornia/PST045224 | Verified | Confirmed LA city population 3,869,089 (V2025), -0.8% change Apr1 2020 base to Jul1 2025, median HH income $81,939 (2020-2024, 2024 dollars), per capita $47,685, poverty 16.5%, owner-occupied 36.0%, median home value $921,200, median gross rent $1,933, labor force 66.4%, mean travel time 30.7 min, retail sales per capita $21,281 (2022), accommodation/food services sales $17,366,966 ($1,000, 2022). |
| 2026-11-25 | T-004 | https://www.usgs.gov/faqs/what-probability-earthquake-will-occur-los-angeles-area-san-francisco-bay-area | Verified | Confirmed LA region 30-year UCERF3 probabilities: M>=6.7 60%, M>=7 46%, M>=7.5 31%. |
| 2026-11-25 | T-004 | https://www.fema.gov/flood-maps/national-flood-hazard-layer | Verified | Official FEMA NFHL page accessible; used as flood screening workflow reference. Parcel-specific flood zone not screened (no parcel location). |
| 2026-11-25 | T-004 | https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones | Verified | Official CAL FIRE/OSFM FHSZ page accessible; used as fire hazard screening workflow reference. Parcel-specific FHSZ not screened. |
| 2026-11-25 | T-002/T-006 | Local link check: `python3` HTML href/src scan over `docs/**/*.html` | Pass | 9 HTML files, 0 missing local refs. |
| 2026-11-25 | T-003 | Repo content scan for personal identifiers | Pass | No parcel address/APN/owner name/lease/rent roll/tax/financial identifiers published. Scenario kept anonymized and labeled unverified. |

## Irregularities / Flagged Items
| Time (UTC) | Item | Severity | Status | Notes |
|---|---|---|---|---|
| 2026-11-25 | F-001..F-014 | High | Published | All material property-specific inputs unverified/missing; published on `docs/flagged.html`. No sell/renew winner selected. |
| 2026-11-25 | Dynamic data sources not pinned | Medium | Published | BLS/EDD live tables change over time; source links verified but current numeric values not pinned in tables to avoid stale/inferred entries. |

## Handoff Log
| Time (UTC) | Task | From | To | Reason |
|---|---|---|---|---|
|  |  |  |  |  |
