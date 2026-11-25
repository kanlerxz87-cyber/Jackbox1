# Jack in the Box — NNN leasehold decision workspace

A decision file for one asset: a single-tenant Jack in the Box under a triple-net lease in central Los Angeles,
with an expiration the owner reports only as a range (2030–2035). It separates what is **verified from an official
source** from what is **still missing**, and it refuses to print a number it cannot source.

**Live site:** <https://kanlerxz87-cyber.github.io/Jackbox1/>

- **Published site:** `docs/` → GitHub Pages (aggregate, non-identifying)
- **Private templates:** `private/` → never published, placeholders only, gitignored
- **Data registry:** `data/registry.yaml` → every published value, with its source link and status
- **Task board and verification log:** `COORDINATION.md`

## What is where

```
data/registry.yaml            72 rows: id, metric, value, unit, geo, period, source, url, status, note
data/tracts_demo_90015.csv    23 tract-level ACS observations (demonstration set only)
tools/build.py                static site generator — reads data/, writes docs/
tools/check.py                link, anchor, tag-balance, traceability and privacy checks
tools/reverify.py             re-pulls machine-readable sources and diffs against the registry
docs/                         the published site (17 pages + machine-readable exports)
private/                      blank templates: lease abstract, notice calendar, sell-vs-hold worksheet
```

## Rebuild and verify

```bash
pip install --break-system-packages pyyaml     # only dependency
python3 tools/build.py                         # regenerate docs/ from data/registry.yaml
python3 tools/check.py                         # fails on broken links, dangling anchors, untraceable rows
python3 tools/reverify.py                      # needs internet: re-pull and diff every machine-readable source
```

The build is idempotent: the same registry produces the same site. Nothing in `docs/` is hand-edited.

## The integrity rules the build enforces

1. A row marked `verified` must carry an `http(s)` source link, or the build refuses to run.
2. A row with a blank value is rendered as a visible **unverified** cell — never dropped, never estimated.
3. No unverified cell may contain a digit (checked post-build).
4. Every table row carries a verification badge (checked post-build).
5. No external scripts, no analytics, no fonts, no cookies, no storage, no network calls from the calculator.
6. `private/` is gitignored and never read by the generator.

## Verification status at build time

| Status | Rows | Meaning |
|---|---|---|
| verified | 57 | value traced to the official page or endpoint that displays it |
| flagged | 5 | published, but the caveat materially affects its use |
| blank / unverified | 10 | deliberately empty rather than inferred |

## What is deliberately absent

No street address, APN, owner name, tenant entity, rent figure, lease term, loan balance, tax-return detail, adviser name,
valuation, capitalisation rate or short-lease discount. Those are missing inputs, not oversights — see the
[review page](docs/review.html) and the [questions register](docs/questions.html).

## Scope limits

This is an analytical working file. It is not an appraisal, not tax advice, not legal advice and not an investment
recommendation, and it publishes no forecast. Figures marked preliminary or flagged carry caveats that are material to
their use. Every value is traceable to an official source; anything that could not be traced was left blank.
