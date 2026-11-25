# Privacy model

Personal information privacy is the highest priority in this project and is treated as such
in the build, not only in prose.

## The rule

> Parcel and owner records stay in an access-controlled internal workspace.
> Only aggregate, non-identifying findings are published.

Observed in practice as: **nothing that could identify the parcel, its owner, its occupant's
legal entity, or the owner's finances is committed to this repository or rendered on the
published site.**

## What is never published

| Category | Treatment |
|---|---|
| Street address, APN / AIN | never written; parcel is `PARCEL-001` |
| Owner name, entity, EIN, SSN | never written |
| Franchisee legal entity, guarantor, signatory | never written — only the public brand is named |
| Lease document text, rent schedule, expense stops | never written; rent is a calculator input only |
| Owner income, filing status, basis, net worth | never written; calculator inputs only |
| Insurance policy numbers and lender documents | never written |
| Coordinates of the actual parcel | never written |

The **tenant brand** (Jack in the Box) is named because it is public: the franchisor is an
SEC registrant (CIK 0000807882) and its filings are cited as `S-011` and `S-012`. Naming the
brand does not identify the parcel; there are many Jack in the Box units in Los Angeles.

## What is published, and why it is safe

Aggregate statistics at city, metro, county and state level — Census, BLS, FHFA, Federal
Reserve, FEMA, USGS. These describe millions of people and cannot be reverse-engineered to a
parcel or a person.

Hazard data was queried at a **downtown reference point**, not the parcel, and every such row
is stamped `Ref. point only` in the data and on the site.

## Enforcement

`scripts/validate.mjs` scans every page, dataset and script for:

- street-address patterns
- APN-style triple-group numbers
- ZIP codes adjacent to address words
- email addresses
- telephone numbers
- SSN and EIN patterns
- entity-name-plus-number patterns

Any hit **fails the build**. The build is not published until the check passes.

It also greps `assets/js/calc.js` for `fetch(`, `XMLHttpRequest`, `sendBeacon`,
`localStorage`, `sessionStorage`, `indexedDB`, `document.cookie`, `WebSocket` and
`navigator.geolocation`, and fails if any appears.

## The calculator

The private calculator exists precisely so the owner can model rent, basis, tax position and
financing **without** those numbers entering this repository or any server.

- It is one dependency-free JavaScript file.
- It makes no network requests of any kind.
- It writes nothing to storage or cookies.
- Reloading the page discards every input.
- No analytics, no third-party fonts, no tracking pixels anywhere on the site.

## Private workspace

Anything requiring the real address, the lease, the owner's tax position or the insurance
binder belongs in an access-controlled workspace shared only with authorised advisers
(attorney, CPA, appraiser, broker under NDA) — not here.

## If you are reviewing this repository

If you believe any committed content could identify a person or a parcel, treat that as a
defect of the highest severity and report it before any other issue. The correct fix is
removal from history, not merely from the current revision.
