# Jackbox1 — Property Decision Workspace

Privacy-first, source-verified static workspace for evaluating an anonymized NNN quick-service restaurant lease scenario in the Central Los Angeles area.

## Live Site

This repository is structured for GitHub Pages deployment from the `docs/` folder via GitHub Actions (`.github/workflows/pages.yml`). After merge to `main`, the Pages workflow deploys `docs/`.

## Privacy

- **No personal information is published.** No parcel address, APN, owner name, lease document, rent roll, tax record, or financial identifier is included.
- Any personal information discovered during research must be handled internally and must not appear on the website.
- Public content is limited to anonymized/aggregate context, decision frameworks, missing-input checklists, and flagged unverified items.

## Site Structure

| Page | Purpose |
|---|---|
| `docs/index.html` | Dashboard / workstream status / scenario snapshot |
| `docs/research.html` | Verified public area context, trade-area workflow (W-01) |
| `docs/hazards.html` | Regional hazard context and parcel screening workflow (W-04) |
| `docs/analysis.html` | Sell vs hold template (W-02), after-tax module, risk register, executive summary (W-10) |
| `docs/questions.html` | Decision gates (W-03), questions, known/unknown answers, missing-info discovery plan |
| `docs/suggestions.html` | Review-before-implementation suggestions and private calculator spec |
| `docs/privacy.html` | Data handling and anonymization controls |
| `docs/sources.html` | Official source registry |
| `docs/flagged.html` | Flagged unverified/missing/review items |

## Verification Rules

- Every table row must have an official source link where applicable.
- If a value cannot be confirmed from an official source, it is left blank and flagged as unverified.
- No values are inferred or fabricated.
- Scenario inputs provided by the user are labeled as unverified unless confirmed by evidence.

## Coordination

See [`COORDINATION.md`](COORDINATION.md) for task claims, verification log, irregularities, and handoff notes.

## Local Preview

```bash
python3 -m http.server 8000 --directory docs
# open http://localhost:8000
```

## Status

This workspace does **not** select a sell-or-renew winner. Material property-specific inputs remain unverified and are listed on the Flagged for Review page.
