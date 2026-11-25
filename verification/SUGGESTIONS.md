# Suggestions and reviewer decision paths

Reviewers shortlist suggestions and choose a path on `audit/suggestions.html`; the board is memory-only.

| ID | Category | Proposal | Rationale | Effort | Status | Official source |
|---|---|---|---|---|---|---|
| S-01 | Site | Give every table row an explicit source ID, retrieval date and official URL (not a generic 'Official reference' link). | Generic links do not support the claim in each row; row-level provenance is auditable. | low | proposed | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| S-02 | Site | Add a machine-readable dataset and a validator that fails the build on missing source links or unflagged blank values. | Automated line-by-line verification prevents silent inference. | low | proposed | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| S-03 | Site | Publish a versioned change log and a retrieval date on every page. | Official series are revised (BLS marks data preliminary); readers need the vintage. | low | proposed | https://www.bls.gov/eag/eag.ca_losangeles_md.htm |
| S-04 | Site | Add a print stylesheet and a one-page advisor brief that contains no identifiers. | Advisers need a shareable summary without exposing private records. | low | proposed | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |
| S-05 | Site | Add an in-browser reviewer board that lets a person shortlist suggestions and choose a path before implementation, with no network calls or persistence. | Keeps the decision gate explicit and preserves privacy. | medium | proposed | https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5 |
| S-06 | Site | Separate OBSERVATION / ASSUMPTION / UNVERIFIED badges on every value. | Prevents assumptions from being mistaken for verified facts. | low | proposed | https://www.census.gov/programs-surveys/acs/data/data-via-api.html |
| S-07 | Research | Commission a private lease abstract and build a dated notice calendar before any commitment. | The 2030–2035 window is unverified; every other gate depends on it. | high | proposed | https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm |
| S-08 | Research | Fix the trade area privately, lock tract IDs and vintages, then pull ACS/LEHD/OnTheMap series. | City and county proxies do not measure the property's neighbourhood. | high | proposed | https://onthemap.ces.census.gov/ |
| S-09 | Research | Run parcel flood, fire and seismic lookups and record the map version and date. | CAL FIRE's 2026 SRA update is in public comment; zone status can change. | medium | proposed | https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones |
| S-10 | Research | Obtain at least three dated, written broker quotes for as-is and renewed cases and paired short-lease quotes. | No official source publishes the short-lease discount for this parcel. | medium | proposed | https://planning.lacity.gov/ |
| S-11 | Research | Have a CPA produce a private after-tax computation, including California ordinary-rate treatment and depreciation recapture. | California provides no preferential capital-gain rate; owner inputs are private. | medium | proposed | https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html |
| S-12 | Research | Build a dated comparable-sales ledger and back-test the cash-flow model before trusting any projection. | A projection without sufficient verified history is an assumption, not evidence. | high | proposed | https://www.bea.gov/data/gdp/gdp-by-county |
| S-13 | Research | Extend the issuer series each quarter and annually; never conclude direction from one quarter. | Same-store sales, closures and rental revenue move over multiple years. | low | proposed | https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R33.htm |
| S-14 | Risk | Stress lost rent, repairs, insurance deductibles and exit liquidity together, including wildfire, earthquake and flood scenarios. | Joint stress matters more than isolated single-peril estimates. | medium | proposed | https://www.fema.gov/flood-maps/products-tools/national-risk-index |
| S-15 | Risk | Verify tenant credit and any guaranty privately before treating renewal as the low-risk path. | Issuer-level closures and same-store declines do not identify the actual tenant entity. | medium | proposed | https://www.sec.gov/Archives/edgar/data/807882/000080788225000070/ex991-q425earningsrelease.htm |
| S-16 | Process | Set a hard, privately recorded decision deadline tied to the verified expiry and option windows; review gates monthly. | Deferral without a deadline silently destroys options. | low | proposed | https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm |
| S-17 | Privacy | Run an automated personal-information scan on every published file before each deploy. | Privacy is the highest-urgency requirement; manual review alone is insufficient. | low | proposed | https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5 |
| S-18 | Coordination | Consolidate the incompatible COORDINATION.md boards into one append-only board that preserves every session's rows. | Multiple sessions created different board schemas; merges risk discarding claims. | medium | proposed | https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages |

## Paths

| Path | Description |
|---|---|
| A | Verification first — recommended process decision |
| B | Build the sale track first |
| C | Build the renewal track first |
| D | No site changes yet |
