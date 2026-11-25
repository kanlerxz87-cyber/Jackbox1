# Jackbox1 — Hold or Sell Decision Workspace

A source-verified research workspace for a single decision: **sell a central-Los Angeles
Jack in the Box property before its NNN lease expires, negotiate a renewal, or hold to expiry?**

Live: **https://kanlerxz87-cyber.github.io/Jackbox1/ledger-1ebd66da/**

Published as `ledger-1ebd66da/` inside a repository that holds several parallel research trees from
independent sessions. This one is additive: it does not modify any other tree. See
[`COORDINATION.session.md`](COORDINATION.session.md) for the reconciliation record.

---

## What this is

A static site, built from a small verified dataset, that does three things:

1. **Publishes what can be verified** — population, income, labour, price, tenant-credit
   and tax evidence, each row transcribed from an official source with the supporting text quoted.
2. **Leaves what cannot be verified blank** — and flags it, rather than estimating. Every empty cell
   names the official tool that would close it.
3. **Sequences the work** — a six-gate decision board showing which evidence clears which gate, so no
   irreversible commitment happens before the cheap information purchases are made.

It contains **no** parcel identifier, street address, owner name, lease term, or personal financial
figure. That exclusion is enforced by the build script, which fails if any of those patterns appear in
a published page.

## Structure

> Run all commands from **inside this directory** (`ledger-1ebd66da/`), not the repo root.

```
index.html                  landing page — the decision, the findings, the sequence
pages/
  economics.html            W-01  trade-area economics
  worksheet.html            W-02  sell-versus-hold + after-tax module + private calculator
  decision-gates.html       W-03  decision-gate progress board
  hazards.html              W-04  parcel hazard screening
  tract-trends.html         W-05  tract-level evidence and the official queries
  rental-evidence.html      W-07  pricing the short-lease discount
  lease-abstract.html       W-08  lease abstract schema and notice reconciliation
  advisory-summary.html     W-10  one-page printable brief
  risks.html                       full risk register incl. tail scenarios
  open-questions.html              22-question pre-decision register
  suggestions.html                 scored improvement backlog
  flagged.html                     irregularities and unverified items
  sources.html                     official source register
  privacy.html                     privacy and anonymisation policy
data/
  sources.mjs               official source registry (24 publishers)
  records.mjs               55 metric rows (44 verified, 11 deliberately blank)
assets/
  css/style.css             dependency-free stylesheet
  js/nav.js                 nav state + table filter
  js/calculator.js          the private, offline sell-versus-hold calculator
scripts/
  build.mjs                 regenerates nav, metric tables, source table, flagged table
  verify.mjs                the deploy gate (see below)
  serve.mjs                 local preview server
  test-calculator.mjs       headless functional test for the calculator
COORDINATION.session.md     this session's board record + reconciliation of the parallel trees
```

## Local development

```bash
cd ledger-1ebd66da
node scripts/build.mjs     # regenerate the derived sections (idempotent)
node scripts/verify.mjs    # run the deploy gate
node scripts/serve.mjs     # preview at http://localhost:4173/ledger-1ebd66da/
```

Optional, for the calculator's functional test:

```bash
npm install --no-save jsdom
node scripts/test-calculator.mjs
```

## The deploy gate

`scripts/verify.mjs` fails the build — and therefore the deploy — if any of these is true:

- a metric row cites a source that is not in the register;
- a source URL is not HTTPS or is not on the official-domain allow-list;
- a metric row has no quoted evidence string;
- an `unverified` row carries a value instead of a blank, or has no flag reference;
- an internal link points to a file that does not exist;
- a page has no `<title>`, or does not load the stylesheet;
- a page contains a street address, coordinate pair, phone number, email address, SSN pattern,
  or card-number-like sequence;
- a page references a metric ID that does not exist;
- a required page is missing.

There is no separate "publish anyway" path. A failing check blocks the site.

## Design rules the dataset follows

| State | Meaning |
| --- | --- |
| **Verified** | Transcribed from the linked official page, with the supporting text quoted in the same row. |
| **Derived** | Arithmetic on two or more verified observations. The operation is stated and both inputs are quoted. |
| **Unverified** | The cell is **empty**. No estimate, no proxy, no interpolation. A flag names the source that would close it. |

Nothing on the site is a forecast presented as a fact. Where a projection would be needed, the
*method* is specified in full and no *number* is published.

## What is deliberately absent

No capitalisation rate for the submarket, no property valuation, no forward projection, no
school ranking, no competitor density, and no probability assigned to any risk — because none of
those can be confirmed from an official source. Each is listed on the
[suggestions page](pages/suggestions.html) with the evidence that would be required to add it
properly.

## Licensing and attribution

Site text and code: this repository. Data: each figure remains the property of its publishing agency
(BLS, Census Bureau, California DOF, SEC, IRS, FTB, City of Los Angeles, CAL FIRE, CGS, FEMA) and is
reproduced in summary with attribution and a direct link on every row.

## Disclaimer

This is a research workspace, not legal, tax, engineering, or investment advice. Every figure is
cited so a licensed professional can check it before any commitment.
