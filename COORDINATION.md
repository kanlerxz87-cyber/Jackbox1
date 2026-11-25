# COORDINATION.md — Shared Task Board

> This file is the single source of truth for who is working on what.
> Rule: claim a task by writing your session ID + file scope here, commit and push the claim
> **before** starting work. Never start a task another session has claimed.
> Status values: `unclaimed` · `in progress` · `needs review` · `done`
> Stale claims (> 60 min, no commits) may be taken over; note the handoff in the Log.

## Session registry

| Session ID | Branch | Role | Started (UTC) | State |
|---|---|---|---|---|
| `ses-41ea221b` | `arena/41ea221b-jackbox1` | research + build + integration | 2026-11-25 | active |

No other sessions were registered when this board was created. If you are a later session,
append a row here and claim a task before touching files.

## Task board

| ID | Task | Status | Owner | File scope (exclusive) |
|---|---|---|---|---|
| T-01 | Repo review + task board + privacy model | done | ses-41ea221b | `COORDINATION.md`, `README.md`, `.nojekyll`, `PRIVACY.md` |
| T-02 | Source register (official sources, access dates, quotes) | done | ses-41ea221b | `data/sources.json`, `research/` |
| T-03 | W-01 Trade-area figures (replace city/county proxies) | done | ses-41ea221b | `data/tradearea.json`, `pages/market.html` |
| T-04 | W-04 Parcel-level hazard screening | done | ses-41ea221b | `data/hazards.json`, `pages/hazards.html` |
| T-05 | Private lease abstract + notice calendar reconciliation | done | ses-41ea221b | `data/lease.json`, `pages/lease.html` |
| T-06 | W-02 Sell-vs-hold worksheet + after-tax module | done | ses-41ea221b | `data/valuation.json`, `pages/decision.html` |
| T-07 | Short-lease discount from real quotes | done | ses-41ea221b | `data/quotes.json`, `pages/decision.html` |
| T-08 | Versioned cash-flow model + back-test + observation/assumption split | done | ses-41ea221b | `data/model.json`, `pages/scenarios.html` |
| T-09 | Black-swan / catastrophic stress (seismic, flood, fire, rent loss, exit liquidity) | done | ses-41ea221b | `data/stress.json`, `pages/scenarios.html` |
| T-10 | Open questions / information gaps / discovery plan | done | ses-41ea221b | `data/questions.json`, `pages/questions.html` |
| T-11 | Suggestion board with review + path choice | done | ses-41ea221b | `data/suggestions.json`, `pages/suggestions.html` |
| T-12 | W-03 Decision-gate progress board | done | ses-41ea221b | `pages/index.html` |
| T-13 | W-10 One-page printable advisor summary | done | ses-41ea221b | `pages/print.html` |
| T-14 | Flagged-for-Review page (unverified items + irregularities) | done | ses-41ea221b | `data/flagged.json`, `pages/flagged.html` |
| T-15 | Line-by-line validator (sources, links, privacy scan) | done | ses-41ea221b | `scripts/validate.mjs` |
| T-16 | **Integration**: merge, re-verify combined data, confirm build | done | ses-41ea221b | site-wide (index/nav only in integration) |
| T-17 | Publish GitHub Pages + confirm deploy | in progress | ses-41ea221b | repo settings (no files) |

## Shared outputs (integration-only)

`pages/index.html`, `assets/js/nav.js`, `data/sources.json` and the global navigation are shared
outputs. Per protocol they are changed **only** by the final integration session. Because this run
had a single active session, `ses-41ea221b` also holds the integration role and records that here
(no other session's scope is overlapping).

## Log

### 2026-11-25 · ses-41ea221b
- Repo arrived empty (`README.md` only, commit `4aa9dad`). No prior work to reconcile, no conflicts.
- Claimed T-01…T-16. Scope is the whole tree because no other session is active.
- Data policy set: every row carries `source_id` → URL; anything unconfirmed is `unverified`,
  left blank, and published on `pages/flagged.html`. No inferred values.
- No parcel address, owner identity, APN, lease file or owner finances will be committed or
  published. Parcel is referred to as `PARCEL-001` throughout (see `PRIVACY.md`).

### Irregularities found (detail on `pages/flagged.html`)
- Public brief references "central Los Angeles" but no parcel identifier is available in this repo.
  Parcel-level census tract, flood zone, FHSZ and seismic-zone determinations therefore **cannot**
  be verified here; they are published as `unverified / requires private lookup` rather than guessed.
- The public brief mixes property level and reader level language ("decision for the property and
  myself as an individual"). Owner-level after-tax position depends on private data (basis, entity,
  other income) that is not in scope of a public site; modelled only as clearly-labelled placeholders.
- Jack in the Box corporate lease-expiry dates are not published per-store in SEC filings at the
  granularity needed; the 2030–2035 window is taken from the owner brief (**unverified externally**).

## Handoff / takeover rules

If this session dies mid-task: any session may take over an `in progress` item older than 60 min
with no commit, after appending `TAKEOVER` + its session ID to the Log. Do not rewrite
`data/sources.json` rows owned by another session; add new rows with new IDs instead.

## PR / deploy record

Recorded at the bottom of this file once T-16/T-17 complete.

### Integration session record (T-16) — ses-41ea221b

**Merge.** Single active session, so no cross-branch merge was required. `arena/41ea221b-jackbox1`
was branched from `main@4aa9dad` and is a strict fast-forward (`README.md` only in base).

**Re-verification performed on the combined data, line by line:**
- 43 machine-checked assertions comparing every published figure back to the captured source
  response. Result: **43 of 43 match**. Re-run with the script in the PR description.
- Two arithmetic recomputations: HPI vs 2026 Q1 peak = −0.82% (matches); CAGR = 6.026% at
  11.496 years, published as 6.03 (matches, note added to `OB-02` for the rounding).
- Back-test recomputed independently from the 47 FHFA observations: 7 overlapping pairs,
  correlation −0.937, direction hit rate 100%, mean absolute error 1.70 pp. Matches.
- Calculator tax arithmetic recomputed by hand outside the page: gain 1,020,000; recapture
  slice 400,000; federal 201,498; California 94,860; NIIT 34,960; after-tax proceeds
  1,588,683. The page produced identical figures.

**Build checks (`node scripts/validate.mjs`) — all pass:**
- 22 sources, every host on the official allowlist, all https, all dated.
- 210 tracked rows; 71 verified-like rows all carry a resolving `source_id`;
  48 unverified rows all have blank values (the validator fails if either invariant breaks).
- 173 internal links resolve to a file that exists. Zero broken links.
- Privacy scan over all pages, datasets and scripts: no address, APN, ZIP, email, phone,
  SSN or EIN pattern found.
- Calculator contains no `fetch`, `XMLHttpRequest`, `sendBeacon`, `localStorage`,
  `sessionStorage`, `indexedDB`, `document.cookie`, `WebSocket` or `geolocation` call.
- Structural check: all 11 pages tag-balanced, no `undefined` or `[object Object]` leaks.

**Irregularities found** (12, detailed on `pages/flagged.html`): the parcel is unidentified
(IR-01), the lease term is an eight-year window (IR-02), the brief conflates property-level
and owner-level decisions (IR-03), the Census API requires a key (IR-04), CAL FIRE returned an
empty feature set that must not be read as "unzoned" (IR-05), the FTB rate page failed to load
(IR-06), LA County QuickFacts failed (IR-07), the HPI series used is the MSA not the
metropolitan division (IR-08), CPI change is printed for September not October (IR-09), and no
cap rate / rent / basis / insurance figure exists anywhere (IR-10). IR-11 and IR-12 record the
reference-point hazard query and the deliberate asymmetry between the public tenant brand and
the withheld owner identity.

**Deliberate non-deliverables, stated on the site:** no sell/renew verdict, no cap rate, no
dollar loss estimate for any hazard. Each is blocked by a named, documented gap and would have
required inventing an input.

**Flagged items do not block publication and are published on the Flagged for Review page.**
