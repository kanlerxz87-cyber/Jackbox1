# Repository review — line by line

Session: `S-62b1c0c2` · Retrieved: `2026-11-25`.

Baseline `4aa9dad`: `README.md` contained one line (`# Jackbox1`), no trailing newline. No data, no site, no board.

`main` at `673c9a8` (PR #1 from another session) contained: `COORDINATION.md`, `README.md`, `index.html`, `assets/app.js`, `assets/style.css`, and nine pages under `pages/`. Each HTML/CSS file is minified to one line, so line references below are file-level.

GitHub Pages was verified with `gh api repos/kanlerxz87-cyber/Jackbox1/pages`: source `main` / `/`, `build_type: legacy`, public, HTTPS enforced.

Eight session branches were visible on the remote; several claimed overlapping scopes (`docs/**`, `pages/**`, `site/**`, `data/**`, `tools/**`) and created incompatible COORDINATION.md board schemas. This session revised its scope to the unclaimed `audit/**` and `verification/**` namespaces and edits no other session's files.

## Irregularities

| ID | Item | Why flagged | Action | Official link |
|---|---|---|---|---|
| F-01 | No street address, APN or parcel identifier supplied | Parcel-level findings cannot be verified; every parcel-specific cell is blank. | Private Assessor/deed lookup; nothing published. | https://assessor.lacounty.gov/ |
| F-02 | No lease document supplied | Expiry, options, rent and notice mechanics are unverified (2030–2035 is a user-supplied range). | Private lease abstract and notice calendar. | https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm |
| F-03 | No verified short-lease quote set | The short-lease discount cannot be priced from official sources. | Solicit dated written quotes privately. | https://planning.lacity.gov/ |
| F-04 | No assessed value, basis, depreciation schedule or loan terms | No dollar after-tax result can be published. | CPA reconstruction offline. | https://www.irs.gov/publications/p946 |
| F-05 | 'Central Los Angeles' is not a Census geography | Trade area must be fixed to specific tracts before local figures can be attached. | Define and lock a private tract set. | https://www.census.gov/programs-surveys/acs/data/data-via-api.html |
| F-06 | Census QuickFacts direct fetch blocked in this environment | Values were transcribed from indexed official Census page content, not a direct fetch; links need manual review. | Open each official QuickFacts link and confirm the value and vintage. | https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia/INC110223 |
| F-07 | Legacy QuickFacts path used for housing values | The older /quickfacts/table/ path may redirect. | Verify owner-occupied rate, median value, median rent and permits on the current QuickFacts page. | https://www.census.gov/quickfacts/table/INC110214/06037 |
| F-08 | BLS October 2026 figures are preliminary | BLS marks the October 2026 column (p); later revisions are expected. | Re-check the next BLS release before a commitment. | https://www.bls.gov/eag/eag.ca_losangeles_md.htm |
| F-09 | CAL FIRE 2026 SRA FHSZ update in public comment | Zone designations can change during the 2026-11-09 to 2027-01-08 comment period. | Record the map version and effective date at private lookup. | https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones |
| F-10 | PeMS is being upgraded | Historical reporting tools are limited during the upgrade. | Confirm station data availability before relying on traffic series. | https://pems.dot.ca.gov/ |
| F-11 | Published root site uses mismatched generic 'Official reference' links | Some rows cite an official page that does not support the specific claim (e.g. a tax publication for lease notice dates). | Replace with row-specific official sources; see Repo Review. | https://planning.lacity.gov/ |
| F-12 | Published root site has no row-level retrieval dates or per-value URLs | Values are not individually auditable. | Adopt a row-level source register. | https://www.census.gov/quickfacts/fact/table/losangelescitycalifornia/INC110223 |
| F-13 | No .nojekyll on main | Legacy Jekyll build processes a static site; files with leading underscores would be skipped. | Add .nojekyll at the Pages root or switch to a workflow build. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| F-14 | Multiple sessions claimed overlapping file scopes | data/**, pages/**, site/**, tools/** and docs/** were claimed by more than one session; merge conflicts are likely. | Consolidate COORDINATION.md and keep disjoint scopes. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| F-15 | Incompatible COORDINATION.md boards across branches | Different schemas will conflict on merge and could discard claims. | Preserve every session's rows in one append-only board. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| F-16 | GitHub Pages source is main / (root) | A docs/ or site/ build by another session is not the live landing page unless the source setting is changed. | Integration session confirms the live URL and links all published namespaces. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| F-17 | Public static site is not an access-controlled workspace | Private records must never be committed to a public repository, even in a hidden folder. | Keep all private material offline with authorized advisers. | https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5 |
| F-18 | GitHub Actions Pages workflow uploads only docs/ while Pages source is legacy main / | A publish-path mismatch: if the Pages source is switched to GitHub Actions, the docs/-only artifact would omit every other published tree, including audit/. | Keep Pages source as legacy main / (verified via gh api) or change the workflow artifact path to the repository root; confirm every tree resolves after each deploy. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| F-19 | Two successive COORDINATION.md conflicts while main advanced during PR #17 | Multiple sessions edited the shared board concurrently; a naive merge could discard claims. | Both conflicts were resolved by appending this session's rows after the newest main board, preserving all other rows; see the merge resolution note in COORDINATION.md. | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |

## Manual review links

- Repository: https://github.com/kanlerxz87-cyber/Jackbox1
- Published site: https://kanlerxz87-cyber.github.io/Jackbox1/
- Pages settings: https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages
- COORDINATION.md (shared board): https://github.com/kanlerxz87-cyber/Jackbox1/blob/main/COORDINATION.md

## Verification performed

1. `verification/build.py` generated every page from `verification/data/dataset.json`.
2. `verification/check.py` validated row-level official source links, blank/unverified cells, internal links, external domain allowlist, JavaScript privacy constraints and personal-information patterns.
3. Results are recorded in `verification/REPORT.md` and reflected on `audit/flagged.html`.
4. No value was inferred; values that could not be confirmed are blank and flagged.
