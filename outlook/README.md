# Outlook and Options module

Session `S-f6ebb740` (branch `arena/f6ebb740-jackbox1`). A self-contained set of pages that adds what the other trees do not cover: official forward-looking projections, a vintage check on how far an official projection moved, dated events, peer and tenant-brand sales trends, an options and black-swan framework with no sell-versus-renew winner, owner-level tax levers, decision gates, a questions register, reviewer suggestions, a flagged list, and a source register.

Live path after Pages deploys: `/Jackbox1/outlook/index.html`.

## Rebuild and check

```
python3 outlook/tools/build.py             # data/*.json -> *.html (deterministic)
python3 outlook/tools/check.py             # data rules, HTML rules, links, privacy; fails if a page is stale
python3 outlook/tools/check.py --selftest  # proves the checker rejects bad input
python3 private-workflow/selftest.py       # offline tests for the private workflow
```

## Rules the checker enforces

- Every source link is `https` and on the official allowlist (`.gov` hosts plus four named hosts, shown with their tier on the Sources page).
- An **observation** row has a source that was actually read (opened or excerpt), plus a quote or a cell locator.
- A **blank** row carries no value, has a flag, and says how to fill it.
- A **framework** or **process** row either cites an official page as context or is flagged as having none.
- Every table row in the built HTML has an official link, or a visible blank marker plus a flag link.
- No script, form, inline style, event handler, plain http reference, address, parcel number, email, phone, coordinate-like number or known stale ZIP.
- Internal links and anchors resolve. Built pages must match the data (`stale` check).

## Files

- `data/*.json`: all content. `sources.json` records how each page was retrieved (opened, excerpt, failed, other-session).
- `tools/common.py`, `tools/build.py`, `tools/check.py`.
- `assets/outlook.css`: one stylesheet, no scripts.
- `*.html`: generated. Do not edit by hand.

## Scope

Exclusive to this session: `outlook/**`, `private-workflow/**`, and the 2026-11-26 block at the top of `COORDINATION.md`. No other tree, root file or shared index was edited. A link from the root landing page to `outlook/index.html` is requested on the board, not made.
