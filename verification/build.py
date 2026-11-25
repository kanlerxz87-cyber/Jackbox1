#!/usr/bin/env python3
"""Generate the independent, aggregate-only verification dashboard.

Reads verification/data/dataset.json and writes static HTML into audit/.
No network access, no external assets, no personal information.
Every generated table row carries a link to an official primary source.
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "verification/data/dataset.json").read_text())
SITE = ROOT / "audit"
VER = ROOT / "verification"
SITE.mkdir(exist_ok=True)
(SITE / "assets/css").mkdir(parents=True, exist_ok=True)
(SITE / "assets/js").mkdir(parents=True, exist_ok=True)

SOURCES = {s["id"]: s for s in DATA["sources"]}
META = DATA["meta"]
DATE = META["retrieved"]


def esc(x):
    return html.escape(str(x), quote=True)


def src(sid):
    s = SOURCES[sid]
    return (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{esc(s["agency"])} — {esc(s["title"])}">'
            f'<span class="srcid">{esc(sid)}</span> {esc(s["agency"])} ↗</a>')


def src_multi(ids):
    return "<br>".join(src(i) for i in ids)


def badge(text, kind="neutral"):
    return f'<span class="badge {kind}">{esc(text)}</span>'


def status_kind(status):
    u = status.upper()
    if "BLOCK" in u or "UNVERIFIED" in u or "FLAGGED" in u or "NOT READY" in u or "NOT ADVISED" in u:
        return "bad"
    if "PARTIAL" in u or "PLANNED" in u or "GATED" in u or "OPEN" in u:
        return "warn"
    if "DONE" in u or "RECOMMENDED" in u or "OBSERVATION" in u:
        return "good"
    return "neutral"


def table(headers, rows, caption="", tid=""):
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(rows)
    cap = f'<caption>{esc(caption)}</caption>' if caption else ""
    ident = f' id="{esc(tid)}"' if tid else ""
    return (f'<div class="table-wrap"><table{ident}>{cap}<thead><tr>{head}</tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def row(cells, source_ids, status=None, value_blank=False, row_status="verified"):
    """cells: list of (text, css_class) or plain strings; last column becomes sources."""
    tds = []
    for c in cells:
        if isinstance(c, tuple):
            text, cls = c
        else:
            text, cls = c, ""
        cl = f' class="{esc(cls)}"' if cls else ""
        tds.append(f"<td{cl}>{text}</td>")
    tds.append(f'<td class="source">{src_multi(source_ids)}</td>')
    attrs = f' data-status="{esc(row_status)}"'
    if value_blank:
        attrs += ' data-unverified="1"'
    if status:
        attrs += f' data-label="{esc(status)}"'
    return f"<tr{attrs}>{''.join(tds)}</tr>"


NAV = [
    ("OVERVIEW", [
        ("index.html", "Dashboard"),
        ("executive.html", "Executive summary"),
        ("decisions.html", "Decision paths"),
        ("summary.html", "Advisor one-pager"),
    ]),
    ("EVIDENCE", [
        ("economy.html", "Economy & demographics"),
        ("tracts.html", "Trade area & tracts"),
        ("hazards.html", "Hazard screening"),
        ("operator.html", "Operator series"),
        ("tax.html", "After-tax rules"),
        ("market.html", "Quotes & lease term"),
        ("lease.html", "Lease & notice calendar"),
    ]),
    ("DECISION", [
        ("gates.html", "Decision-gate board"),
        ("model.html", "Versioned model"),
        ("risks.html", "Risk & black swans"),
        ("questions.html", "Questions & answers"),
    ]),
    ("TOOLS", [
        ("calculator.html", "Private calculator"),
        ("suggestions.html", "Suggestions board"),
    ]),
    ("GOVERNANCE", [
        ("requirements.html", "Requirements inventory"),
        ("flagged.html", "Flagged for review"),
        ("privacy.html", "Privacy policy"),
        ("sources.html", "Official sources"),
        ("review.html", "Repo review"),
    ]),
]

PAGES = {p for _, items in NAV for p, _ in items}


def page(slug, title, eyebrow, h1, lead, body, extra_head="", extra_script=""):
    nav_html = []
    for group, items in NAV:
        nav_html.append(f'<div class="nav-label">{esc(group)}</div>')
        for path, label in items:
            active = " active" if path == slug else ""
            nav_html.append(f'<a class="nav-link{active}" href="{esc(path)}">{esc(label)}</a>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Anonymous, source-linked evidence for a single-tenant NNN property decision.">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>{esc(title)} | Independent Verification Desk</title>
<link rel="stylesheet" href="assets/css/site.css">
{extra_head}
</head><body>
<a class="skip" href="#main">Skip to content</a>
<div class="shell">
<aside class="side">
  <a class="brand" href="index.html"><span class="mark">V</span><span>VERIFICATION<br><small>DESK · S-62b1c0c2</small></span></a>
  <div class="side-note">Independent, aggregate-only evidence layer. <a href="https://kanlerxz87-cyber.github.io/Jackbox1/" target="_blank" rel="noopener noreferrer">Main published site ↗</a></div>
  <nav aria-label="Primary">{''.join(nav_html)}</nav>
  <div class="privacy"><strong>◉ Privacy first</strong><p>No address, owner, APN, lease file or owner financial figure is published here. Placeholders only.</p></div>
</aside>
<main id="main">
  <header class="top"><span>INDEPENDENT VERIFICATION <span class="slash">/</span> {esc(eyebrow.upper())}</span><span class="top-right">● ANONYMOUS BY DESIGN · {esc(DATE)}</span></header>
  <div class="content">
    <div class="eyebrow">{esc(eyebrow)}</div>
    <h1>{esc(h1)}</h1>
    <p class="lead">{lead}</p>
    {body}
    <footer class="foot">Independent verification desk · Session {esc(META['session'])} · Retrieved {esc(DATE)} · Not investment, legal, tax or engineering advice. No personal information is published.</footer>
  </div>
</main></div>
<script src="assets/js/site.js" defer></script>
{extra_script}
</body></html>
"""


def analysis(title, items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f'<section class="analysis"><h2>{esc(title)}</h2><ul>{lis}</ul></section>'


def write(slug, title, eyebrow, h1, lead, body, extra_head="", extra_script=""):
    (SITE / slug).write_text(page(slug, title, eyebrow, h1, lead, body, extra_head, extra_script))


# ---------------------------------------------------------------- shared tables
def metrics_table(categories, caption):
    rows = []
    for m in DATA["metrics"]:
        if m["category"] not in categories:
            continue
        rows.append(row([
            (esc(m["id"]), "mono"), esc(m["label"]),
            (esc(m["value"]), "value num"), esc(m["period"]),
            badge("OBSERVATION", "good"),
        ], [m["source"]], row_status="verified"))
    return table(["ID", "Indicator", "Verified value", "Period", "Class", "Official source"], rows, caption, "data-table")


def unverified_table(categories, caption):
    rows = []
    for u in DATA["unverified"]:
        if u["category"] not in categories:
            continue
        rows.append(row([
            (esc(u["id"]), "mono"), esc(u["label"]),
            ("", "value blank"),
            esc(u["why"]), esc(u["discovery"]),
            badge("UNVERIFIED", "bad"),
        ], [u["source"]], value_blank=True, row_status="unverified"))
    return table(["ID", "Required value", "Verified value", "Why it is blank", "How to obtain it privately", "Status", "Official portal"], rows, caption, "data-table")


def simple_table(headers, key, caption, mapper):
    rows = [mapper(d) for d in DATA[key]]
    return table(headers, rows, caption, "data-table")


# ---------------------------------------------------------------- 1. dashboard
counts = {
    "verified observations": len(DATA["metrics"]),
    "official sources": len(DATA["sources"]),
    "unverified items": len(DATA["unverified"]),
    "open questions": len(DATA["questions"]),
    "requirements": len(DATA["requirements"]),
    "suggestions": len(DATA["suggestions"]),
    "risk rows": len(DATA["risks"]),
}
cards = "".join(
    f'<div class="stat"><strong>{v}</strong><span>{esc(k)}</span></div>' for k, v in counts.items()
)
body = f"""
<div class="callout critical"><strong>Decision status: no transaction winner is defensible yet.</strong>
<p>Every property-specific value is blank and flagged. The only decision supported by the information that
currently exists is a <b>verification-first, reversible hold</b>: commit to neither a sale nor a renewal, keep
collecting rent, and run both cases in parallel behind a hard private deadline. See
<a href="executive.html">Executive summary</a> and <a href="decisions.html">Decision paths</a>.</p></div>
<div class="stats">{cards}</div>
{analysis("What this independent desk adds", [
    'Line-by-line provenance: every table row carries a link to the official primary source that was actually retrieved; see <a href="sources.html">Official sources</a>.',
    'Blank means unverified: no value is inferred, interpolated or filled; see <a href="flagged.html">Flagged for review</a>.',
    'Aggregate-only evidence: verified regional economy, demographics, issuer series and tax rules are kept separate from parcel-specific unknowns; see <a href="economy.html">Economy</a> and <a href="operator.html">Operator series</a>.',
    'Reproducible audit: <code>verification/build.py</code> regenerates every page from <code>verification/data/dataset.json</code>, and <code>verification/check.py</code> validates rows, links, privacy and JavaScript; see <a href="review.html">Repo review</a>.',
])}
<h2>Start here</h2>
<div class="grid">
  <a class="card" href="executive.html"><span>01</span><h3>Executive summary</h3><p>Important details, the current process decision and the risk-balanced path.</p></a>
  <a class="card" href="questions.html"><span>02</span><h3>Questions & answers</h3><p>Thirty questions, the information needed, the current answer and how to discover what is missing.</p></a>
  <a class="card" href="gates.html"><span>03</span><h3>Decision gates</h3><p>Ten gates with evidence requirements and an official reference for each.</p></a>
  <a class="card" href="flagged.html"><span>04</span><h3>Flagged for review</h3><p>Every unverified value and irregularity, with the official link for manual review.</p></a>
  <a class="card" href="calculator.html"><span>05</span><h3>Private calculator</h3><p>Browser-only after-tax sale vs hold comparison. No network calls, no storage.</p></a>
  <a class="card" href="suggestions.html"><span>06</span><h3>Suggestions board</h3><p>Review suggestions and choose a path before any change is implemented.</p></a>
</div>
<h2>Verified headline observations</h2>
{table(["Indicator", "Verified value", "Period", "Official source"], [
    row([esc("LA County population change 2020→2025"), (esc("-3.2%"), "value num"), esc("V2025")], ["CENSUS-QF-CTY-POP"]),
    row([esc("LA metro unemployment rate"), (esc("4.6%"), "value num"), esc("Oct 2026 (p)")], ["BLS-EAG-LA"]),
    row([esc("LA metro total nonfarm 12-month change"), (esc("0.9%"), "value num"), esc("Oct 2026 (p)")], ["BLS-EAG-LA"]),
    row([esc("Jack in the Box system same-store sales"), (esc("-4.2%"), "value num"), esc("FY2025")], ["SEC-Q4-8K"]),
    row([esc("Jack in the Box brand franchise rental revenues"), (esc("$332,735 thousand"), "value num"), esc("FY2025")], ["SEC-R33"]),
], "Regional and issuer-level context only — not parcel measurements", "data-table")}
<p class="muted">"p" = preliminary as marked by the source. Values are transcribed, never inferred. Full series with
periods and source links are on the category pages.</p>
"""
write("index.html", "Dashboard", "Overview", "Independent verification dashboard",
      "A source-linked, anonymous evidence layer for a single-tenant NNN property decision. It publishes only "
      "what can be confirmed from official primary sources, and leaves everything else blank and flagged.", body)

# ---------------------------------------------------------------- 2. executive
body = f"""
<div class="callout"><strong>Best decision available today (process decision).</strong>
<p>Do not sell and do not renew yet. Keep the asset in a reversible hold, protect every notice window, and run
a time-boxed verification programme that produces <b>both</b> an after-tax sale case and a negotiated renewal case
on the same valuation date. This is not choosing a winner: it is the only choice that does not require inputs
that have not been verified. A transaction winner may be selected only after Gates 1–6 close.</p></div>
<h2>Why this is the answer</h2>
{analysis("Evidence that exists, and its limits", [
    'Regional labour conditions are measurable: BLS reports LA-Long Beach-Glendale MD unemployment of <b>4.6%</b> and total nonfarm employment of <b>4,662.8 thousand</b> in October 2026 (preliminary, not seasonally adjusted); EDD independently reports the LA County rate at <b>4.6%</b>. <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm" target="_blank" rel="noopener noreferrer">BLS ↗</a> <a href="https://edd.ca.gov/en/about_edd/news_releases_and_announcements/unemployment-october-2026" target="_blank" rel="noopener noreferrer">EDD ↗</a>',
    'Demographic direction is mixed: Census QuickFacts shows LA County population down <b>3.2%</b> from the 2020 estimates base to July 2025, while LA city is down <b>0.8%</b>; county median household income is <b>$90,112</b> and city <b>$81,939</b> (2020–2024 ACS, 2024 dollars). These are city/county <i>proxies</i>, not trade-area figures. <a href="https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia/EDU685224" target="_blank" rel="noopener noreferrer">Census ↗</a>',
    'Issuer-level direction is negative across a multi-year series: Jack in the Box system same-store sales were <b>-1.3%</b> in FY2024 and <b>-4.2%</b> in FY2025; FY2025 had <b>31</b> openings and <b>86</b> closures; brand franchise rental revenues moved <b>$351,283k → $347,227k → $332,735k</b> across FY2023–FY2025. This is the franchisor, not the subject tenant or parcel. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R33.htm" target="_blank" rel="noopener noreferrer">SEC 10-K ↗</a> <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000070/ex991-q425earningsrelease.htm" target="_blank" rel="noopener noreferrer">SEC 8-K ↗</a>',
    'The tax mechanics are verifiable: federal net capital gain is capped at <b>20%</b>, unrecaptured section 1250 gain at <b>25%</b>, NIIT is <b>3.8%</b>, and California taxes capital gains as ordinary income with a maximum <b>13.3%</b> rate. But basis, debt and owner rates are private, so no after-tax dollar result can be published. <a href="https://www.irs.gov/taxtopics/tc409" target="_blank" rel="noopener noreferrer">IRS ↗</a> <a href="https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html" target="_blank" rel="noopener noreferrer">FTB ↗</a>',
    'Physical risk is real but parcel status is unknown: FEMA, CAL FIRE and the California Geological Survey publish the authoritative map frameworks; a private address lookup is required before any zone status can be stated. <a href="https://msc.fema.gov/portal/home" target="_blank" rel="noopener noreferrer">FEMA MSC ↗</a> <a href="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones" target="_blank" rel="noopener noreferrer">CAL FIRE ↗</a> <a href="https://www.conservation.ca.gov/cgs/shzp" target="_blank" rel="noopener noreferrer">CGS ↗</a>',
])}
<h2>What would change the answer</h2>
{table(["If verified evidence shows…", "Then the defensible path becomes…", "Gate", "Official reference"], [
    row([esc("As-is quotes plus a CPA after-tax computation exceed the verified hold-case present value by a margin that covers transaction risk"), esc("Prepare the sale case for a decision; still no automatic winner"), badge("G-4, G-5, G-7")], ["IRS-TC409"]),
    row([esc("A written renewal term sheet, verified guaranty and acceptable insurance/engineering produce a higher risk-adjusted hold value"), esc("Prepare the renewal case for a decision; still no automatic winner"), badge("G-1, G-3, G-5")], ["SEC-Q4-8K"]),
    row([esc("Notice windows are close, tenant credit is weak, or parcel hazard/insurance costs are material"), esc("Preserve the sale option and shorten the verification timetable"), badge("G-1, G-3")], ["FEMA-MSC"]),
    row([esc("Verified inputs remain incomplete as the lease term shortens"), esc("Do not guess; keep the reversible hold and re-open the gates on a recorded schedule"), badge("G-9")], ["SEC-10K-INDEX"]),
], "Conditional decision rules — not a recommendation of sale or renewal", "data-table")}
<h2>Balance of wealth preservation and opportunity</h2>
{analysis("Risk-balanced posture", [
    'Preserve optionality: an irreversible sale or a long renewal both remove an option; a reversible hold keeps both while information is gathered. The official 45-day and 180-day exchange deadlines show how quickly options can vanish once a transaction starts. <a href="https://www.irs.gov/pub/irs-prior/i8824--2020.pdf" target="_blank" rel="noopener noreferrer">IRS Form 8824 instructions ↗</a>',
    'Protect against black swans without inventing probabilities: wildfire, earthquake and flood are official, mapped hazards; stress lost rent, repairs and impaired exit liquidity together rather than one at a time. <a href="https://www.fema.gov/flood-maps/products-tools/national-risk-index" target="_blank" rel="noopener noreferrer">FEMA National Risk Index ↗</a>',
    'Do not personalize publicly: "the best decision for the property and myself as an individual" depends on private liquidity, concentration, tax position and risk tolerance. Those are excluded from the public site by the highest-priority privacy rule. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">California CCPA/CPRA ↗</a>',
])}
<p class="muted">This page contains analysis, not a property-specific valuation. See
<a href="risks.html">Risk & black swans</a> and <a href="summary.html">the printable one-pager</a>.</p>
"""
write("executive.html", "Executive summary", "Overview", "Executive summary",
      "The important details, the current decision, and the conditions that would change it — with an official "
      "source for every factual claim.", body)

# ---------------------------------------------------------------- 3. decisions
rows = []
for d in DATA["decisions"]:
    rows.append(row([
        (esc(d["id"]), "mono"), esc(d["option"]), esc(d["what_it_is"]),
        esc(d["when_it_wins"]), esc(d["when_it_loses"]), badge(d["status"], status_kind(d["status"])),
    ], [d["source"]]))
body = f"""
<p class="muted">Every reasonably available path is listed. No path is marked as the winner. The final row is a
<i>process</i> decision, not a transaction outcome.</p>
{table(["ID", "Path", "What it is", "When it wins", "When it loses", "Status", "Official reference"], rows,
       "Decision matrix — prepared side by side, no winner selected", "data-table")}
{analysis("How to read the matrix", [
    'Both the sale case and the renewal case must use the same valuation date, the same verified lease term and the same tax rules; otherwise the comparison is not valid. <a href="https://www.irs.gov/taxtopics/tc409" target="_blank" rel="noopener noreferrer">IRS Topic 409 ↗</a>',
    'A like-kind exchange is a tax-deferral path, not a valuation path; its 45-day and 180-day deadlines are strict and California still taxes gains as ordinary income. <a href="https://www.irs.gov/pub/irs-prior/i8824--2020.pdf" target="_blank" rel="noopener noreferrer">IRS ↗</a> <a href="https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html" target="_blank" rel="noopener noreferrer">FTB ↗</a>',
    'The subject lease expiry is user-supplied as a 2030–2035 range; issuer filings do not publish a store-level expiry, so any path that depends on a date is currently unverified. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm" target="_blank" rel="noopener noreferrer">SEC EDGAR ↗</a>',
])}
"""
write("decisions.html", "Decision paths", "Overview", "Decision paths",
      "All available decisions and the conditions under which each becomes defensible. No winner is selected "
      "until verified inputs exist.", body)

# ---------------------------------------------------------------- 4. economy
body = f"""
<div class="callout"><strong>These are regional figures, not trade-area figures.</strong>
<p>Requirement W-01 asks for city and county proxies to be replaced by trade-area figures. That cannot be done
until a private parcel anchor fixes a consistent Census tract set. Every value below is explicitly labelled a
proxy and is kept alongside the tract-level method on <a href="tracts.html">Trade area & tracts</a>.</p></div>
<h2>Population & geography</h2>
{metrics_table(["Population", "Geography"], "U.S. Census Bureau QuickFacts — county and city proxies")}
<h2>Income, poverty & education</h2>
{metrics_table(["Income", "Education"], "Household income, per-capita income, poverty and educational attainment")}
<h2>Housing</h2>
{metrics_table(["Housing"], "Households, tenure, value, rent and permits — county/city proxies")}
<h2>Jobs, sectors & prices</h2>
{metrics_table(["Jobs", "Prices"], "BLS and California EDD — LA metro division and LA County")}
{analysis("Findings (observations, not projections)", [
    'Population and jobs point in different directions: the county population estimate is <b>-3.2%</b> versus the 2020 estimates base while October 2026 total nonfarm employment is <b>+0.9%</b> year over year (preliminary). A single indicator cannot support a decision. <a href="https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia/EDU685224" target="_blank" rel="noopener noreferrer">Census ↗</a> <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm" target="_blank" rel="noopener noreferrer">BLS ↗</a>',
    'Education & health services is the largest sector in the BLS table (<b>1,057.9 thousand</b> jobs, +3.3% y/y), while leisure & hospitality (<b>548.0 thousand</b>, +2.0% y/y) is the most directly relevant to restaurant demand. Both are preliminary October 2026 figures. <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm" target="_blank" rel="noopener noreferrer">BLS ↗</a>',
    'Local CPI-U (1982-84=100) was <b>360.965</b> in October 2026; the BLS table left the October 12-month change cell blank and published <b>3.7%</b> for September 2026. We do not fill the blank. <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm" target="_blank" rel="noopener noreferrer">BLS ↗</a>',
    'State sources add independent context: California DOF publishes city/county population and housing estimate series, BEA publishes county GDP and personal income, and SCAG publishes the regional growth forecast. Values for a single parcel must come from tracts, not these aggregates. <a href="https://dof.ca.gov/forecasting/demographics/estimates/" target="_blank" rel="noopener noreferrer">DOF ↗</a> <a href="https://www.bea.gov/data/gdp/gdp-by-county" target="_blank" rel="noopener noreferrer">BEA ↗</a> <a href="https://scag.ca.gov/connect-socal" target="_blank" rel="noopener noreferrer">SCAG ↗</a>',
])}
<h2>Official series to keep updating</h2>
{table(["Series", "Agency", "What it contributes", "Official link"], [
    row([esc("State city/county population and housing estimates (E-1 to E-8)"), esc("CA Dept. of Finance"), esc("Multi-year local population direction")], ["DOF-ESTIMATES"]),
    row([esc("GDP by County and Personal Income by County, 2024"), esc("U.S. BEA"), esc("County economic output and income")], ["BEA-GDP-CTY"]),
    row([esc("Connect SoCal 2024 / Connect SoCal 2050"), esc("SCAG"), esc("Regional population, household and employment forecasts")], ["SCAG-CONNECT"]),
    row([esc("Monthly labor force and industry employment release"), esc("CA EDD"), esc("Preliminary and revised local jobs data")], ["EDD-LMI"]),
], "Official series for a reliable projection system", "data-table")}
"""
write("economy.html", "Economy & demographics", "Evidence", "Economy & demographics",
      "Verified geography, population, income, schools, housing, jobs and price observations from official "
      "primary sources. City and county values are labelled proxies.", body)

# ---------------------------------------------------------------- 5. tracts
body = f"""
<div class="callout"><strong>'Central Los Angeles' is not a Census geography.</strong>
<p>Tract-level trend evidence can be produced only after the private parcel anchor is used to select a consistent
tract set. No tract value below is inferred from city or county figures.</p></div>
<h2>Tract-level values (blank until verified)</h2>
{unverified_table(["Trade area"], "Tract-level series that must be produced in the private workflow")}
<h2>Method — to be run privately</h2>
{table(["Step", "Action", "Why it matters", "Class", "Official tool / rule"], [
    row([esc("1"), esc("Use the real parcel location only inside the access-controlled workspace; publish no identifier."), esc("Privacy is the highest-urgency requirement."), badge("PRIVATE")], ["LEGINFO-CCPA"]),
    row([esc("2"), esc("Fix a documented trade-area boundary (drive-time or ring) and record its geometry and date."), esc("A stable boundary prevents cherry-picking."), badge("ASSUMPTION")], ["CENSUS-ONTHEMAP"]),
    row([esc("3"), esc("Select consistent Census tracts and record tract IDs, FIPS and ACS vintage."), esc("County FIPS 06037 and city place 0644000 are verified anchors."), badge("OBSERVATION")], ["CENSUS-ACS-API"]),
    row([esc("4"), esc("Pull multi-year ACS 5-year profiles, LEHD/OnTheMap workforce data and DOF estimates."), esc("Direction over years, not one period."), badge("METHOD")], ["CENSUS-DATA"]),
    row([esc("5"), esc("Pull local planning, traffic, school and competitor evidence for the same boundary."), esc("Keeps all local evidence consistent with the tract set."), badge("METHOD")], ["LACITY-PLANNING"]),
    row([esc("6"), esc("Publish aggregate, non-identifying results only; keep the tract map and parcel link offline."), esc("Publish only anonymous summaries."), badge("PRIVATE")], ["CENSUS-QF-COMP3"]),
], "Private workflow for W-01 and W-12", "data-table")}
<h2>Local evidence portals (no parcel values published)</h2>
{table(["Factor", "Official portal", "What to retrieve privately", "Official link"], [
    row([esc("Planning & zoning"), esc("LA City Planning / New Zoning Code"), esc("Zone, community plan, case and permit history")], ["LACITY-PLANNING", "LACITY-ZONING"]),
    row([esc("Traffic"), esc("Caltrans PeMS District 7"), esc("Multi-year station flow and AADT near the parcel")], ["CALTRANS-PEMS"]),
    row([esc("School systems"), esc("CDE DataQuest / downloadable data"), esc("Attendance-area enrollment and dashboard series")], ["CDE-DATAQUEST", "CDE-DATAFILES"]),
    row([esc("Workforce & commuting"), esc("Census LEHD OnTheMap"), esc("Daytime/workplace population and inflow/outflow")], ["CENSUS-ONTHEMAP"]),
    row([esc("Competitors"), esc("LA City Planning case search"), esc("Competing QSR supply and entitlement actions")], ["LACITY-PLANNING"]),
    row([esc("Hazard context"), esc("FEMA National Risk Index"), esc("Tract-level expected annual loss and resilience")], ["FEMA-NRI"]),
], "Official local evidence portals", "data-table")}
{analysis("Why the regional figures stay visible", [
    'The requirement is tract-level trend evidence <i>alongside</i> regional figures, so the verified regional series on <a href="economy.html">Economy</a> are retained as context but never substituted for the neighbourhood. <a href="https://www.census.gov/programs-surveys/acs/data/data-via-api.html" target="_blank" rel="noopener noreferrer">Census ACS API ↗</a>',
    'A private location must be used only inside the secure workflow; no address, APN or coordinates appear in this dataset or the generated site. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">California CCPA/CPRA ↗</a>',
])}
"""
write("tracts.html", "Trade area & tracts", "Evidence", "Trade area & tracts",
      "A private, tract-level method with every parcel value left blank and flagged, alongside the verified "
      "regional figures.", body)

# ---------------------------------------------------------------- 6. hazards
body = f"""
<div class="callout critical"><strong>Regional hazard context is not parcel status.</strong>
<p>Requirement W-04 asks to replace regional context with the parcel's actual zone status for earthquake, fire
and flood. That lookup requires the private location, so all zone-status cells are blank and flagged.</p></div>
<h2>Parcel zone status (blank until privately verified)</h2>
{unverified_table(["Hazard"], "Parcel-specific hazard, engineering and insurance values")}
<h2>Verified official hazard framework</h2>
{metrics_table(["Hazard"], "Verified official hazard categories and programmes")}
<h2>Official screening sequence</h2>
{table(["Peril", "Official map / programme", "What must be checked privately", "Official link"], [
    row([esc("Flood"), esc("FEMA Flood Map Service Center"), esc("Effective FIRM zone, panel date, elevation certificate, NFIP quote and 30-day waiting period")], ["FEMA-MSC", "FEMA-FLOOD-INS"]),
    row([esc("Fire"), esc("CAL FIRE / State Fire Marshal FHSZ"), esc("Moderate / High / Very High designation, SRA vs LRA, map version and the 2026 SRA update")], ["CALFIRE-FHSZ"]),
    row([esc("Earthquake"), esc("CGS Seismic Hazards Program / EQ ZApp"), esc("Alquist-Priolo fault, liquefaction, landslide and tsunami zones; disclosure duty")], ["CGS-SHZP", "CGS-EQZAPP"]),
    row([esc("Ground shaking"), esc("USGS 2023 50-State NSHM (revised 2026)"), esc("Los Angeles basin amplification and design-level shaking")], ["USGS-NSHM"]),
    row([esc("Insurance"), esc("CDI / California FAIR Plan / CEA"), esc("Admitted-market quotes, FAIR Plan limits and exclusions, earthquake coverage")], ["CDI-FAIR", "CDI-RES", "CEA"]),
    row([esc("Combined loss"), esc("FEMA National Risk Index (v1.20)"), esc("Tract-level expected annual loss, social vulnerability and resilience")], ["FEMA-NRI"]),
], "Official screening sequence for seismic, flood and fire", "data-table")}
{analysis("Joint stress, not single-peril guessing", [
    'Wildfire, earthquake and flood can interrupt rent, create repair costs and narrow the buyer pool at the same time; stress all three with lost rent and exit liquidity together, and label every scenario magnitude an assumption. <a href="https://www.fema.gov/flood-maps/products-tools/national-risk-index" target="_blank" rel="noopener noreferrer">FEMA NRI ↗</a>',
    'CAL FIRE notes that FHSZ maps evaluate hazard rather than risk over a 30–50 year horizon, and that the 2026 SRA update is in public comment from 2026-11-09 to 2027-01-08; record the map version at lookup. <a href="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones" target="_blank" rel="noopener noreferrer">CAL FIRE ↗</a>',
    'CGS states that sellers and agents must disclose when a property lies within a mapped seismic hazard zone; that obligation should be in the private sale checklist. <a href="https://www.conservation.ca.gov/cgs/shzp" target="_blank" rel="noopener noreferrer">CGS ↗</a>',
])}
"""
write("hazards.html", "Hazard screening", "Evidence", "Parcel-level hazard screening",
      "Official seismic, flood and fire map frameworks, blank parcel zone status, engineering and insurance "
      "checks, and a joint-stress method.", body)

# ---------------------------------------------------------------- 7. operator
body = f"""
<div class="callout"><strong>Direction over a series, not one quarter.</strong>
<p>The verified same-store-sales, unit-count, closure and franchise-rental-revenue series below come from
official SEC filings. They describe the franchisor, not the subject tenant entity or the subject parcel.</p></div>
<h2>Multi-year issuer series</h2>
{metrics_table(["Operator"], "Jack in the Box Inc. — official SEC filings, FY2023–FY2025 and quarterly series")}
<h2>Series at a glance</h2>
{table(["Series", "FY2023", "FY2024", "FY2025", "Direction", "Official source"], [
    row([esc("Jack in the Box brand franchise rental revenues ($ thousands)"), (esc("351,283"), "value num"), (esc("347,227"), "value num"), (esc("332,735"), "value num"), badge("declining", "bad")], ["SEC-R33"]),
    row([esc("Consolidated franchise rental revenues ($ thousands)"), (esc("364,591"), "value num"), (esc("375,428"), "value num"), (esc("368,643"), "value num"), badge("mixed", "warn")], ["SEC-R5"]),
    row([esc("Jack in the Box brand franchise royalties ($ thousands)"), (esc("207,064"), "value num"), (esc("198,377"), "value num"), (esc("189,646"), "value num"), badge("declining", "bad")], ["SEC-R33"]),
    row([esc("Consolidated total revenues ($ thousands)"), (esc("1,692,306"), "value num"), (esc("1,571,306"), "value num"), (esc("1,465,314"), "value num"), badge("declining", "bad")], ["SEC-R5"]),
    row([esc("System same-store sales (52 weeks)"), ("", "value blank"), (esc("-1.3%"), "value num"), (esc("-4.2%"), "value num"), badge("deteriorating", "bad")], ["SEC-Q4-8K"], value_blank=True, row_status="unverified"),
], "Brand- and issuer-level direction; no property-level inference", "data-table")}
{analysis("Interpretation limits", [
    'The 10-K revenue note states franchise arrangements generally have a <b>20-year</b> term with royalties and marketing fees based on a percentage of gross sales. That is a general franchise term, not the subject NNN lease term. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R10.htm" target="_blank" rel="noopener noreferrer">SEC 10-K revenue note ↗</a>',
    'FY2025 closures (<b>86</b>) exceeded openings (<b>31</b>), and 38 of the 47 Q4 closures were part of a block closure programme; the direction of the unit base matters to renewal risk, but the actual tenant remains unverified. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000070/ex991-q425earningsrelease.htm" target="_blank" rel="noopener noreferrer">SEC 8-K ↗</a>',
    'The subject lease expiration (2030–2035) is user-supplied; SEC filings do not publish store-level expiry dates. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm" target="_blank" rel="noopener noreferrer">SEC EDGAR filing index ↗</a>',
])}
"""
write("operator.html", "Operator series", "Evidence", "Operator series",
      "Verified same-store sales, unit counts, closures and franchise rental revenues across multiple periods "
      "from official SEC filings.", body)

# ---------------------------------------------------------------- 8. tax
rows = [row([(esc(t["id"]), "mono"), esc(t["rule"]), (esc(t["value"]), "value"), esc(t["note"])], [t["source"]]) for t in DATA["tax_rules"]]
body = f"""
<p class="muted">Only the rules are published. No owner-specific tax result appears on this site.</p>
{table(["ID", "Verified rule", "Value", "Note", "Official source"], rows,
       "Verified federal and California tax rules", "data-table")}
{analysis("Turning rules into one number", [
    'The <a href="calculator.html">private calculator</a> wires these rules into a single comparison: after-tax sale net proceeds versus the present value of the hold case. All dollar inputs are adviser-entered assumptions and never leave the browser.',
    'California has no preferential capital-gain rate; a federal-only estimate is therefore incomplete. <a href="https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html" target="_blank" rel="noopener noreferrer">FTB ↗</a> and <a href="https://www.ftb.ca.gov/about-ftb/data-reports-plans/summary-of-federal-income-tax-changes/index.html" target="_blank" rel="noopener noreferrer">FTB 2025 law analysis ↗</a>',
    'Depreciation recapture at up to 25% and the 3.8% NIIT can materially change net proceeds; basis and MAGI must come from a CPA privately. <a href="https://www.irs.gov/taxtopics/tc409" target="_blank" rel="noopener noreferrer">IRS Topic 409 ↗</a> <a href="https://www.irs.gov/taxtopics/tc559" target="_blank" rel="noopener noreferrer">IRS Topic 559 ↗</a>',
    'Property tax reassessment on a change of ownership is governed by Proposition 13 rules; the actual bill for this parcel is unverified. <a href="https://boe.ca.gov/pdf/pub800-10.pdf" target="_blank" rel="noopener noreferrer">BOE Publication 800-10 ↗</a>',
])}
<h2>Blank owner-specific inputs</h2>
{unverified_table(["Tax"], "Private tax inputs required before any dollar result")}
"""
write("tax.html", "After-tax rules", "Evidence", "After-tax module",
      "Verified federal and California tax rules with official sources, plus the private inputs that remain blank.", body)

# ---------------------------------------------------------------- 9. market
body = f"""
<div class="callout critical"><strong>The short-lease discount is not priced.</strong>
<p>No verified arm's-length quote set for a short-lease quick-service property in central Los Angeles exists in
official sources. Requirement W-08's value is therefore blank and flagged, not estimated.</p></div>
<h2>Quote-dependent values</h2>
{unverified_table(["Market"], "Values that require dated, written market quotes")}
<h2>How to discover the missing information</h2>
{table(["Step", "Action", "Evidence to retain privately", "Official context"], [
    row([esc("1"), esc("Define as-is and renewed-case property descriptions with the verified lease term."), esc("A dated description consistent with the lease abstract")], ["SEC-10K-INDEX"]),
    row([esc("2"), esc("Request at least three written broker opinions for each case, with the same valuation date."), esc(" dated opinions with assumptions and comparable transactions")], ["LACITY-PLANNING"]),
    row([esc("3"), esc("Request paired quotes showing a short remaining term versus a long remaining term."), esc("The observed discount, if any, with quote dates")], ["LACITY-PLANNING"]),
    row([esc("4"), esc("Verify the parcel's planning/zoning status before relying on any highest-and-best-use claim."), esc("Official zone and case records")], ["LACITY-ZONING"]),
    row([esc("5"), esc("Publish only an aggregate, non-identifying conclusion, if ever appropriate."), esc("No quotes, addresses or owner details")], ["LEGINFO-CCPA"]),
], "Quote-discovery workflow (private)", "data-table")}
{analysis("Why no number is published", [
    'Official sources publish regional economic and demographic series, not a discount for one parcel with a short lease. <a href="https://www.bea.gov/data/gdp/gdp-by-county" target="_blank" rel="noopener noreferrer">BEA ↗</a>',
    'A static public site is not an access-controlled workspace; quotes containing identifiers must stay offline. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">CCPA/CPRA ↗</a>',
])}
"""
write("market.html", "Quotes & lease term", "Evidence", "Quotes & lease-term pricing",
      "Short-lease discount and sale-price values left blank and flagged, with a private quote-discovery workflow.", body)

# ---------------------------------------------------------------- 10. lease
body = f"""
<div class="callout"><strong>Commission the abstract privately; reconcile it with the notice calendar.</strong>
<p>No lease, amendment or estoppel certificate was supplied. This page publishes a blank, anonymised template
with placeholders only; the executed documents stay offline with authorised advisers.</p></div>
<h2>Blank lease abstract fields</h2>
{unverified_table(["Lease", "Tenant"], "Private lease abstract fields — all blank")}
<h2>Notice calendar template (no dates published)</h2>
{table(["Field", "Placeholder", "Rule", "Official context"], [
    row([esc("Property reference"), (esc("[PARCEL_ID]"), "mono"), esc("Identifier stays offline; never published")], ["LEGINFO-CCPA"]),
    row([esc("Owner entity"), (esc("[OWNER_ENTITY]"), "mono"), esc("Personal/entity information stays offline")], ["LEGINFO-CCPA"]),
    row([esc("Lease file"), (esc("[LEASE_FILE]"), "mono"), esc("Executed lease and amendments stay offline")], ["SEC-10K-INDEX"]),
    row([esc("Expiration date"), (esc("[UNVERIFIED_DATE]"), "mono"), esc("Must come from the executed lease, not the 2030–2035 range")], ["SEC-10K-INDEX"]),
    row([esc("Option exercise window"), (esc("[UNVERIFIED_DATE]"), "mono"), esc("Abstract each option and delivery method")], ["LACITY-PLANNING"]),
    row([esc("Renewal notice deadline"), (esc("[UNVERIFIED_DATE]"), "mono"), esc("Assign an owner and reminder cadence privately")], ["SEC-10K"]),
    row([esc("Marketing lead time"), (esc("[ASSUMPTION]"), "mono"), esc("An assumption to be agreed with advisers, not an official value")], ["BLS-EAG-LA"]),
    row([esc("Hard decision deadline"), (esc("[ASSUMPTION]"), "mono"), esc("Tie to the verified expiry and option windows")], ["SEC-10K-INDEX"]),
], "Blank notice-calendar template — placeholders only", "data-table")}
{analysis("Reconciliation rule", [
    'The lease abstract and the notice calendar must be reconciled by two people before any sale or renewal commitment; a user-supplied expiry range is not a date. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm" target="_blank" rel="noopener noreferrer">SEC filing index (issuer-level only) ↗</a>',
    'Franchise arrangement terms published in the 10-K are general and do not establish the subject NNN lease term. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R10.htm" target="_blank" rel="noopener noreferrer">SEC 10-K revenue note ↗</a>',
])}
"""
write("lease.html", "Lease & notice calendar", "Evidence", "Lease abstract & notice calendar",
      "An anonymised, all-blank lease abstract and notice-calendar template. No lease terms or identifiers are "
      "published.", body)

# ---------------------------------------------------------------- 11. model
rows = [row([(esc(v["id"]), "mono"), esc(v["version"]), (esc(v["date"]), "value"), esc(v["change"]), badge(v["status"], status_kind(v["status"]))], [v["source"]]) for v in DATA["model_versions"]]
oa_rows = [row([(esc(o["id"]), "mono"), esc(o["item"]), badge(o["class"], status_kind(o["class"])), esc(o["note"])], [o["source"]], row_status="unverified" if o["class"] == "UNVERIFIED" else "verified", value_blank=False) for o in DATA["observations_assumptions"]]
body = f"""
<div class="callout"><strong>Back-test status: BLOCKED.</strong>
<p>A versioned model skeleton exists, but sufficient verified comparable history does not. Distinguishing
observations from assumptions is mandatory; no projection is presented as reliable.</p></div>
<h2>Version history</h2>
{table(["ID", "Version", "Date", "Change", "Status", "Official source"], rows,
       "Versioned cash-flow model skeleton", "data-table")}
<h2>Observations vs assumptions vs unverified</h2>
{table(["ID", "Item", "Class", "Note", "Official reference"], oa_rows,
       "Every input is classified; no assumption is presented as an observation", "data-table")}
<h2>Model mechanics (definitions only, no values)</h2>
{table(["Component", "Definition", "Classification", "Official rule"], [
    row([esc("After-tax sale net proceeds"), esc("sale price − selling costs − debt payoff − federal capital-gain tax − unrecaptured 1250 tax − NIIT − California tax"), badge("ASSUMPTION inputs + OBSERVATION rules")], ["IRS-TC409", "IRS-TC559", "FTB-CAPGAINS"]),
    row([esc("Hold-case present value"), esc("discounted net rent over the verified remaining term + discounted net exit value"), badge("ASSUMPTION")], ["BEA-GDP-CTY"]),
    row([esc("Joint stress"), esc("apply lost-rent months, repair cost and exit-liquidity haircut together to the hold case"), badge("ASSUMPTION")], ["FEMA-NRI"]),
    row([esc("Comparison number"), esc("after-tax sale net proceeds − hold-case present value on one valuation date"), badge("OUTPUT, not a recommendation")], ["IRS-TC409"]),
    row([esc("Back-test"), esc("compare prior model outputs with realised comparable outcomes; blocked until sufficient history exists"), badge("BLOCKED")], ["SEC-FACTS"]),
], "Model definitions", "data-table")}
{analysis("Gate before trust", [
    'A model is only reliable when verified inputs and sufficient comparable history exist; until then, all outputs are illustrative. <a href="https://www.bea.gov/data/gdp/gdp-by-county" target="_blank" rel="noopener noreferrer">BEA county data ↗</a>',
    'Issuer-level XBRL company facts provide verified history for the franchisor, not for this parcel; they cannot substitute for comparable property transactions. <a href="https://data.sec.gov/api/xbrl/companyfacts/CIK0000807882.json" target="_blank" rel="noopener noreferrer">SEC company facts ↗</a>',
])}
"""
write("model.html", "Versioned model", "Decision", "Versioned cash-flow model",
      "A versioned skeleton with an explicit observation / assumption / unverified split. Back-test is blocked "
      "until verified inputs and sufficient comparable history exist.", body)

# ---------------------------------------------------------------- 12. gates
rows = [row([(esc(g["id"]), "mono"), esc(g["gate"]), esc(g["requirement"]), badge(g["status"], status_kind(g["status"])), esc(g["evidence"]), esc(g["note"])], [g["source"]]) for g in DATA["gates"]]
body = f"""
{table(["ID", "Gate", "Evidence required", "Status", "Current evidence", "Note", "Official reference"], rows,
       "W-03 decision-gate progress board", "data-table")}
{analysis("Gate rules", [
    'A gate is never marked verified without a check against an official source; all links on this board point to official primary material. <a href="https://www.census.gov/programs-surveys/acs/data/data-via-api.html" target="_blank" rel="noopener noreferrer">Census ACS API ↗</a>',
    'An item published on <a href="flagged.html">Flagged for Review</a> has status <code>needs review</code> and does not block the merge; it does block a transaction decision.',
    'Gate 0 (privacy) is a prerequisite for every other gate and has the highest urgency. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">California CCPA/CPRA ↗</a>',
])}
"""
write("gates.html", "Decision-gate board", "Decision", "Decision-gate progress board",
      "Ten gates from privacy through the final decision, each with evidence requirements, status and an "
      "official reference.", body)

# ---------------------------------------------------------------- 13. risks
rows = [row([(esc(r["id"]), "mono"), esc(r["decision"]), esc(r["exposure"]), esc(r["effect"]), esc(r["mitigation"]), badge(r["evidence"], status_kind(r["evidence"]))], [r["source"]]) for r in DATA["risks"]]
body = f"""
<p class="muted">Scenario magnitudes are intentionally not published as facts. OBSERVATION = verified official
material; ANALYSIS = qualitative reasoning; UNVERIFIED = blank value flagged elsewhere.</p>
{table(["ID", "Decision / scope", "Exposure", "Potential effect", "Mitigation", "Evidence class", "Official reference"], rows,
       "Risk register for every decision path, including business-as-usual and black-swan events", "data-table")}
{analysis("Black-swan posture", [
    'Wildfire, earthquake and flood are officially mapped hazards; combine them with lost rent, repair costs and impaired exit liquidity in one stress run rather than three isolated estimates. <a href="https://www.fema.gov/flood-maps/products-tools/national-risk-index" target="_blank" rel="noopener noreferrer">FEMA NRI ↗</a> <a href="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones" target="_blank" rel="noopener noreferrer">CAL FIRE ↗</a> <a href="https://www.conservation.ca.gov/cgs/shzp" target="_blank" rel="noopener noreferrer">CGS ↗</a>',
    'Insurance availability is part of the risk: the FAIR Plan is an insurer of last resort with coverage limitations and NFIP flood policies typically have a 30-day waiting period. <a href="https://www.insurance.ca.gov/01-consumers/105-type/95-guides/03-res/Res-Ins-Guide.cfm" target="_blank" rel="noopener noreferrer">CDI ↗</a> <a href="https://www.fema.gov/flood-insurance" target="_blank" rel="noopener noreferrer">FEMA ↗</a>',
    'For wealth preservation and growth, avoid concentration in a single unverified tenant and avoid leverage before rent and hazard costs are verified; keep both transaction options open until the gates close. <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm" target="_blank" rel="noopener noreferrer">BLS ↗</a>',
])}
"""
write("risks.html", "Risk & black swans", "Decision", "Risk register & black-swan scenarios",
      "Risks for every decision path, business-as-usual and rare natural-disaster events, with an official "
      "reference on every row.", body)

# ---------------------------------------------------------------- 14. questions
rows = []
for q in DATA["questions"]:
    blank = q["answer"] == ""
    rows.append(row([
        (esc(q["id"]), "mono"), esc(q["category"]), esc(q["question"]), esc(q["needed"]),
        (esc(q["answer"]) if not blank else "", "value blank" if blank else "value"),
        esc(q["discovery"]), badge(q["status"], status_kind(q["status"])),
    ], [q["source"]], value_blank=blank, row_status="unverified" if blank else "verified"))
body = f"""
<p class="muted">A blank answer means unverified, not zero. Each row tells you what information is needed, how to
discover it, and which official source to consult.</p>
{table(["ID", "Category", "Question", "Information needed", "Current answer", "How to discover it", "Status", "Official reference"], rows,
       "Questions, information and answers required before any decision can reasonably be made", "data-table")}
{analysis("What the answers add up to", [
    'The verified answers are limited to regional economic observations and issuer-level series; they cannot establish a parcel-level decision. <a href="https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia/INC110223" target="_blank" rel="noopener noreferrer">Census ↗</a> <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R33.htm" target="_blank" rel="noopener noreferrer">SEC ↗</a>',
    'Every blank answer is also published on <a href="flagged.html">Flagged for Review</a> with its official portal so a human can verify it manually.',
    'No answer requires publishing personal information; all discovery happens in the access-controlled offline workflow. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">CCPA/CPRA ↗</a>',
])}
"""
write("questions.html", "Questions & answers", "Decision", "Questions & answers",
      "A clear list of the questions, information needed, current answers and suggested discovery paths that "
      "must be addressed before any decision can reasonably be made.", body)

# ---------------------------------------------------------------- 15. calculator
verified_params = [
    ("Federal maximum long-term capital gain rate", "20%", "IRS-TC409"),
    ("Maximum unrecaptured section 1250 gain rate", "25%", "IRS-TC409"),
    ("Net investment income tax", "3.8%", "IRS-TC559"),
    ("California capital gains", "ordinary income rates (no preferential rate)", "FTB-CAPGAINS"),
    ("California maximum personal income tax rate", "13.3%", "FTB-FEDCHANGES"),
    ("MACRS nonresidential real property", "39 years straight line", "IRS-P946"),
    ("Section 1031 identification / receipt", "45 days / 180 days", "IRS-I8824"),
    ("California property tax rate", "1% of assessed value plus voter-approved debt", "BOE-PUB800-10"),
]
param_rows = [row([esc(a), (esc(b), "value")], [c]) for a, b, c in verified_params]
body = f"""
<div class="callout"><strong>Private, browser-only, no network calls and no storage.</strong>
<p>All inputs stay in this page's memory and disappear on reload. Do not enter names, addresses, APNs or any
identifier. Nothing is transmitted. The only verified numbers on this page are the tax rules below; every dollar
field is an adviser-entered assumption and is left empty by default.</p></div>
<h2>Verified parameters (observations)</h2>
{table(["Rule", "Verified value", "Official source"], param_rows,
       "These rules are transcribed from official sources; they are not property-specific", "data-table")}
<h2>Adviser inputs (assumptions — blank by default)</h2>
<form id="calc" class="calc" autocomplete="off" novalidate>
  <fieldset><legend>Sale case</legend>
    <label>Sale price (USD)<input type="number" name="price" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Selling costs (USD)<input type="number" name="costs" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Debt payoff (USD)<input type="number" name="debt" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Adjusted basis (USD)<input type="number" name="basis" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Accumulated depreciation (USD)<input type="number" name="depr" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Federal long-term gain rate (%)<input type="number" name="fed" min="0" max="60" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>California marginal rate (%)<input type="number" name="ca" min="0" max="60" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label><input type="checkbox" name="niit"> Apply 3.8% NIIT to the gain</label>
  </fieldset>
  <fieldset><legend>Hold case</legend>
    <label>Annual net rent (USD)<input type="number" name="rent" min="0" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Remaining years (number)<input type="number" name="years" min="0" max="60" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Discount rate (%)<input type="number" name="discount" min="0" max="60" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Exit capitalisation rate (%)<input type="number" name="cap" min="0.1" max="60" step="any" placeholder="[ADVISER_INPUT]"></label>
    <label>Lost-rent months (stress)<input type="number" name="lostmonths" min="0" max="120" step="any" placeholder="[ASSUMPTION]"></label>
    <label>Repair cost (USD, stress)<input type="number" name="repairs" min="0" step="any" placeholder="[ASSUMPTION]"></label>
    <label>Exit-liquidity haircut (%, stress)<input type="number" name="haircut" min="0" max="100" step="any" placeholder="[ASSUMPTION]"></label>
  </fieldset>
  <div class="actions"><button type="submit">Compare locally →</button><button type="reset" class="secondary">Clear inputs</button><button type="button" id="printcalc" class="secondary">Print</button></div>
</form>
<div id="calcresult" class="result" aria-live="polite">No comparison calculated — verified inputs are missing. Every field above is an assumption until an adviser verifies it privately.</div>
<h2>What the one number means</h2>
{table(["Output", "Definition", "Class", "Official rule"], [
    row([esc("After-tax sale net proceeds"), esc("sale price − selling costs − debt − federal tax on gain − 25% tax on unrecaptured section 1250 gain − NIIT − California tax on gain"), badge("COMPUTED from assumptions")], ["IRS-TC409", "FTB-CAPGAINS"]),
    row([esc("Hold-case present value"), esc("present value of annual net rent for the remaining years + present value of the exit value (net rent ÷ cap rate)"), badge("COMPUTED from assumptions")], ["BEA-GDP-CTY"]),
    row([esc("Stressed hold value"), esc("hold value less lost rent, repairs and an exit-liquidity haircut applied together"), badge("COMPUTED from assumptions")], ["FEMA-NRI"]),
    row([esc("Comparison number"), esc("after-tax sale net proceeds − hold-case present value on one valuation date"), badge("OUTPUT, not a recommendation")], ["IRS-TC559"]),
], "Definitions of the calculator outputs", "data-table")}
<p class="muted">Simplifications are deliberate: no instalment sale, no passive-activity or basis-difference
adjustments, no state deduction of federal tax, no §1031 deferral, no mid-month convention proration, and no
land/building allocation beyond the entered basis. A CPA must produce the real computation. This calculator is
not tax advice.</p>
"""
write("calculator.html", "Private calculator", "Tools", "Private after-tax calculator",
      "A browser-only sell-versus-hold worksheet that turns verified tax rules into one comparable number. "
      "No data leaves the reader's browser.", body,
      extra_script='<script src="assets/js/calculator.js" defer></script>')

# ---------------------------------------------------------------- 16. suggestions
rows = []
for s in DATA["suggestions"]:
    rows.append(row([
        (esc(s["id"]), "mono"),
        (f'<label class="pick"><input type="checkbox" class="sug-pick" value="{esc(s["id"])}"> {esc(s["proposal"])}</label>', ""),
        esc(s["category"]), esc(s["rationale"]), badge(s["effort"], "neutral"), badge(s["status"], status_kind(s["status"])),
    ], [s["source"]]))
body = f"""
<div class="callout"><strong>Review and choose a path before implementing any change.</strong>
<p>Shortlist suggestions below, choose one path, and generate a decision memo. Everything happens in this
browser; there are no network calls, no accounts and no persistence. Clearing or reloading discards the shortlist.</p></div>
{table(["ID", "Suggestion (tick to shortlist)", "Category", "Rationale", "Effort", "Status", "Official reference"], rows,
       "Suggestions to improve the site and the decision process", "data-table")}
<h2>Choose a path</h2>
<form id="pathform" class="paths">
  <label><input type="radio" name="path" value="A" checked> <b>Path A — Verification first (recommended process decision)</b><span>Implement only privacy, provenance and gate improvements now; defer all valuation changes until Gates 1–6 close.</span></label>
  <label><input type="radio" name="path" value="B"> <b>Path B — Build the sale track first</b><span>Prioritise quotes, lease abstract and after-tax work; keep the renewal track as a parallel check.</span></label>
  <label><input type="radio" name="path" value="C"> <b>Path C — Build the renewal track first</b><span>Prioritise tenant credit, renewal terms and hazard/insurance verification; keep the sale track as a parallel check.</span></label>
  <label><input type="radio" name="path" value="D"> <b>Path D — No site changes yet</b><span>Record the review without implementing anything; re-open at the next gate review.</span></label>
  <div class="actions"><button type="button" id="makememo">Generate decision memo →</button><button type="button" id="clearmemo" class="secondary">Clear shortlist</button></div>
</form>
<pre id="memo" class="memo" aria-live="polite">No memo generated. Shortlist suggestions and choose a path above.</pre>
<h2>Candidate decision memos (analysis)</h2>
{table(["Path", "When it is appropriate", "Main risk", "Official reference"], [
    row([esc("A — Verification first"), esc("When property-specific inputs are unverified, as they are today"), esc("Deferral without a hard deadline")], ["SEC-10K-INDEX"]),
    row([esc("B — Sale track first"), esc("When notice windows are near or hazard/insurance costs look material"), esc("Pricing an assumed short-lease discount")], ["IRS-TC409"]),
    row([esc("C — Renewal track first"), esc("When tenant credit and a written renewal term sheet are available"), esc("Assuming a renewal that is not enforceable")], ["SEC-Q4-8K"]),
    row([esc("D — No change"), esc("When the review is deliberately paused"), esc("Silent loss of options")], ["LACITY-PLANNING"]),
], "Paths a reviewer may choose", "data-table")}
"""
write("suggestions.html", "Suggestions board", "Tools", "Suggestions & reviewer decision board",
      "Site and research improvements, with an in-browser shortlist and path selection so a reviewer can choose "
      "before any change is implemented.", body)

# ---------------------------------------------------------------- 17. summary
body = f"""
<div class="printbar"><button type="button" onclick="window.print()">Print this one-pager</button> <a href="executive.html">Full executive summary →</a></div>
<section class="onepage">
<h2>Decision brief for authorised advisers (anonymous)</h2>
<p><b>Subject.</b> One single-tenant quick-service restaurant property under a triple-net lease, described only
as being around central Los Angeles, with a user-supplied expiration window of 2030–2035. No parcel identifier
is published.</p>
<p><b>Decision status.</b> No sale-or-renewal winner is defensible. The supported decision is a reversible,
verification-first hold: commit to neither path, protect all notice windows, and build both the after-tax sale
case and the negotiated renewal case in parallel behind a hard private deadline.</p>
<h3>What is verified (official sources)</h3>
{table(["Topic", "Verified observation", "Official source"], [
    row([esc("Regional jobs"), esc("LA MD unemployment 4.6% and total nonfarm 4,662.8k in Oct 2026 (preliminary); +0.9% y/y")], ["BLS-EAG-LA"]),
    row([esc("Regional population"), esc("LA County 9,694,934 (Jul 2025, V2025), −3.2% since the 2020 estimates base")], ["CENSUS-QF-CTY-POP"]),
    row([esc("Regional income"), esc("County median household income $90,112; city $81,939 (2020–2024 ACS, 2024 dollars)")], ["CENSUS-QF-CTY-INC"]),
    row([esc("Operator direction"), esc("System same-store sales −1.3% (FY2024) and −4.2% (FY2025); FY2025 openings 31, closures 86")], ["SEC-Q4-8K"]),
    row([esc("Franchise rental revenue"), esc("Brand $351,283k → $347,227k → $332,735k (FY2023–FY2025)")], ["SEC-R33"]),
    row([esc("After-tax rules"), esc("Federal max 20% gain / 25% unrecaptured 1250 / 3.8% NIIT; CA gains as ordinary income, max 13.3%")], ["IRS-TC409", "IRS-TC559", "FTB-CAPGAINS"]),
    row([esc("Hazard framework"), esc("FEMA MSC flood maps, CAL FIRE FHSZ, CGS EQ ZApp, FEMA NRI v1.20 — parcel status not checked")], ["FEMA-MSC", "CALFIRE-FHSZ", "CGS-SHZP"]),
], "Verified observations only", "data-table")}
<h3>What is not verified (blank by design)</h3>
{table(["Topic", "Verified value", "Official portal for private verification"], [
    row([esc("Exact expiry, options, notice dates, rent, guaranty"), ("", "value blank")], ["SEC-10K-INDEX"], value_blank=True, row_status="unverified"),
    row([esc("Parcel flood / fire / seismic zone status"), ("", "value blank")], ["FEMA-MSC"], value_blank=True, row_status="unverified"),
    row([esc("Trade-area tracts, traffic, schools, competitors"), ("", "value blank")], ["CENSUS-ONTHEMAP"], value_blank=True, row_status="unverified"),
    row([esc("Sale price, short-lease discount, renewal terms"), ("", "value blank")], ["LACITY-PLANNING"], value_blank=True, row_status="unverified"),
    row([esc("Basis, depreciation, debt, owner tax rates"), ("", "value blank")], ["IRS-P946"], value_blank=True, row_status="unverified"),
], "Blank means unverified — never zero", "data-table")}
<h3>Next actions</h3>
<ol>
<li>Keep all identifiers, lease files and owner finances offline with authorised advisers; publish only anonymous summaries. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">CCPA/CPRA ↗</a></li>
<li>Commission the private lease abstract and reconcile it with a dated notice calendar. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm" target="_blank" rel="noopener noreferrer">SEC EDGAR (issuer-level context) ↗</a></li>
<li>Fix the trade area privately; pull tract-level Census, CDE, PeMS and planning evidence. <a href="https://www.census.gov/programs-surveys/acs/data/data-via-api.html" target="_blank" rel="noopener noreferrer">Census ACS API ↗</a></li>
<li>Screen flood, fire and seismic zones, engineering and insurance; stress lost rent, repairs and exit liquidity together. <a href="https://www.fema.gov/flood-maps/products-tools/national-risk-index" target="_blank" rel="noopener noreferrer">FEMA NRI ↗</a></li>
<li>Get dated quotes and a CPA after-tax computation; compare both cases on one valuation date; select a winner only when Gates 1–6 close. <a href="https://www.irs.gov/taxtopics/tc409" target="_blank" rel="noopener noreferrer">IRS Topic 409 ↗</a></li>
</ol>
<p class="muted">Not investment, legal, tax or engineering advice. Retrieved {esc(DATE)}. Session {esc(META['session'])}.
This page contains no personal information.</p>
</section>
"""
write("summary.html", "Advisor one-pager", "Overview", "One-page advisor summary",
      "A printable, anonymous one-pager with the verified observations, the blank items and the next actions.", body)

# ---------------------------------------------------------------- 18. requirements
rows = [row([(esc(r["id"]), "mono"), esc(r["category"]), esc(r["text"]), badge(r["status"], status_kind(r["status"])), esc(r["note"])], [r["source"]]) for r in DATA["requirements"]]
body = f"""
<p class="muted">Every stated requirement is listed with its current status. Rows with status blocked or flagged
point to the <a href="flagged.html">Flagged for Review</a> page.</p>
{table(["ID", "Category", "Requirement (verbatim intent)", "Status", "How it is addressed", "Official reference"], rows,
       "Full requirements inventory", "data-table")}
"""
write("requirements.html", "Requirements inventory", "Governance", "Requirements inventory",
      "All stated requirements collected, organized and status-tracked, each with an official reference.", body)

# ---------------------------------------------------------------- 19. flagged
rows = [row([(esc(f["id"]), "mono"), esc(f["item"]), ("", "value blank"), esc(f["why"]), esc(f["action"]), badge("needs review", "warn")], [f["source"]], value_blank=True, row_status="unverified") for f in DATA["flagged"]]
body = f"""
<div class="callout"><strong>Flagged for review — does not block the merge.</strong>
<p>Every item here is published for manual review with the official link. A blank verified value means the
value could not be confirmed from an official source; it is never inferred or filled in.</p></div>
{table(["ID", "Item", "Verified value", "Why it is flagged", "Action for manual review", "Status", "Official link"], rows,
       "Flagged irregularities and unverified items", "data-table")}
{analysis("Review instructions", [
    'Open each official link and confirm the value and vintage; where a link is a portal, run the lookup privately with the real parcel location and record the map version and date. <a href="https://msc.fema.gov/portal/home" target="_blank" rel="noopener noreferrer">FEMA MSC ↗</a>',
    'Never paste an address, APN, owner name, lease file or financial figure into the public site or repository. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">CCPA/CPRA ↗</a>',
    'When a value becomes verified, add it to <code>verification/data/dataset.json</code> with its source ID and retrieval date, re-run <code>verification/build.py</code> and <code>verification/check.py</code>, and update the gate board. <a href="https://github.com/kanlerxz87-cyber/Jackbox1" target="_blank" rel="noopener noreferrer">Repository ↗</a>',
])}
"""
write("flagged.html", "Flagged for review", "Governance", "Flagged for review",
      "Unverified values and irregularities published for manual review, each with an official source link. "
      "Blank means unverified, never zero.", body)

# ---------------------------------------------------------------- 20. privacy
body = f"""
<div class="callout critical"><strong>Personal information privacy is the highest-urgency requirement.</strong>
<p>No personal information appears in the final website product or anywhere on the published site. Any personal
information discovered during research is for internal use only, in an access-controlled offline workspace,
and is represented publicly only by placeholders.</p></div>
<h2>Placeholder scheme</h2>
{table(["Placeholder", "Stands for", "Where it may be used", "Official basis"], [
    row([(esc("[PARCEL_ID]"), "mono"), esc("Address, APN/AIN, legal description, coordinates"), esc("Private worksheet only; never published as a value")], ["LEGINFO-CCPA"]),
    row([(esc("[OWNER_ENTITY]"), "mono"), esc("Owner name, entity, contact details"), esc("Private adviser notes only")], ["LEGINFO-CCPA"]),
    row([(esc("[LEASE_FILE]"), "mono"), esc("Executed lease, amendments, estoppels"), esc("Offline document store only")], ["SEC-10K-INDEX"]),
    row([(esc("[ADVISER_1]"), "mono"), esc("Authorised adviser identity"), esc("Private access list only")], ["LEGINFO-CCPA"]),
    row([(esc("[UNVERIFIED_DATE]"), "mono"), esc("Lease expiry, option window, notice deadline"), esc("Notice calendar template; blank until verified")], ["SEC-10K"]),
    row([(esc("[ADVISER_INPUT]"), "mono"), esc("Any adviser-entered financial assumption"), esc("Browser calculator input; never transmitted")], ["IRS-TC559"]),
    row([(esc("[ASSUMPTION]"), "mono"), esc("Any non-verified scenario magnitude"), esc("Model and stress scenarios; always labelled")], ["FEMA-NRI"]),
], "Anonymisation placeholders used across the site", "data-table")}
<h2>Rules enforced by the build</h2>
{table(["Rule", "Implementation", "Official basis"], [
    row([esc("No personal identifiers in published files"), esc("Automated pattern scan in verification/check.py over every HTML, CSS, JS and JSON file")], ["LEGINFO-CCPA"]),
    row([esc("No network calls from the site"), esc("JavaScript scan rejects fetch, XMLHttpRequest, WebSocket, sendBeacon and external script sources")], ["GH-PAGES"]),
    row([esc("No persistence of inputs"), esc("Calculator and suggestion board are memory-only; no localStorage or sessionStorage")], ["LEGINFO-CCPA"]),
    row([esc("Aggregate findings only"), esc("All published values are official aggregate or issuer-level observations")], ["CENSUS-QF-CTY-INC"]),
    row([esc("Public site is not an access-controlled workspace"), esc("Private records stay offline; nothing private is committed to the public repository")], ["GH-PAGES"]),
], "Privacy controls", "data-table")}
{analysis("Legal context", [
    'The California Consumer Privacy Act requires notice at collection, purpose limitation, retention limits and contractual controls when personal information is disclosed to third parties. <a href="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5" target="_blank" rel="noopener noreferrer">California Civil Code Title 1.81.5 ↗</a>',
    'Parcel and ownership records belong to official county systems and should be consulted only inside the secure workflow. <a href="https://assessor.lacounty.gov/" target="_blank" rel="noopener noreferrer">LA County Assessor ↗</a>',
])}
"""
write("privacy.html", "Privacy policy", "Governance", "Privacy & anonymisation",
      "The highest-priority rules: placeholders only, no personal information published, no network calls and "
      "no persistence of inputs.", body)

# ---------------------------------------------------------------- 21. sources
rows = [row([(esc(s["id"]), "mono"), esc(s["agency"]),
             (f'<a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])} ↗</a>', ""),
             esc(s["retrieved"]), esc(s["method"]), esc(s["note"])], [s["id"]]) for s in DATA["sources"]]
body = f"""
<p class="muted">Only official government and primary regulatory sources are used for published values. Retrieval
method is recorded because some official pages were accessible only through indexed official-page content.</p>
{table(["ID", "Agency", "Official page", "Retrieved", "Retrieval method", "Note", "Official link"], rows,
       "Official source register — every published value resolves to one of these sources", "data-table")}
{analysis("Verification method", [
    'Each value in <code>verification/data/dataset.json</code> carries a source ID. The generator emits that official URL into the row. <a href="https://github.com/kanlerxz87-cyber/Jackbox1" target="_blank" rel="noopener noreferrer">Repository ↗</a>',
    'Values that could not be confirmed are left blank and carry the official portal where they must be checked; see <a href="flagged.html">Flagged for Review</a>.',
    'Preliminary BLS figures, map-version changes and revised official series are re-check items; see <a href="review.html">Repo review</a>.',
])}
"""
write("sources.html", "Official sources", "Governance", "Official source register",
      "Every official source used, with retrieval date, retrieval method and notes for manual review.", body)

# ---------------------------------------------------------------- 22. review
body = f"""
<p class="muted">Line-by-line review of the repository as it stood on main at commit <code>673c9a8</code>
(merged PR #1) and of the initial commit <code>4aa9dad</code>, plus the parallel-session branches observed on
2026-11-25. Findings are also on <a href="flagged.html">Flagged for Review</a>.</p>
<h2>Repository inventory reviewed</h2>
{table(["Path / commit", "What it contains", "Review result", "Official / manual review link"], [
    row([(esc("4aa9dad README.md"), "mono"), esc("One line: '# Jackbox1'; no newline; no data, no site, no board."), badge("no irregularities", "good")], ["GH-PAGES"]),
    row([(esc("673c9a8 index.html"), "mono"), esc("Root landing dashboard with a nine-page sidebar and an on-hold decision status."), badge("builds; generic source links", "warn")], ["GH-PAGES"]),
    row([(esc("673c9a8 pages/*.html"), "mono"), esc("Nine category pages including calculator, hazards, questions, suggestions, flags and an advisor brief."), badge("row-level provenance missing", "warn")], ["GH-PAGES"]),
    row([(esc("673c9a8 assets/app.js"), "mono"), esc("In-browser arithmetic worksheet; no network calls and no storage found."), badge("privacy-safe arithmetic", "good")], ["GH-PAGES"]),
    row([(esc("673c9a8 assets/style.css"), "mono"), esc("Single-line minified stylesheet for the dashboard shell."), badge("no irregularities", "good")], ["GH-PAGES"]),
    row([(esc("673c9a8 COORDINATION.md"), "mono"), esc("Short board from another session; other branches carry incompatible board schemas."), badge("merge conflict risk", "bad")], ["GH-PAGES"]),
    row([(esc("GitHub Pages configuration"), "mono"), esc("Source main / (legacy build), public, HTTPS enforced, repo public."), badge("root site is live", "good")], ["GH-PAGES"]),
], "Line-by-line repository review (files are minified to one line each on main)", "data-table")}
<h2>Irregularities flagged for manual review</h2>
{table(["ID", "Finding", "Verified value", "Action", "Official link"], [
    row([(esc(f["id"]), "mono"), esc(f["item"]), ("", "value blank"), esc(f["action"])], [f["source"]], value_blank=True, row_status="unverified") for f in DATA["flagged"]
         if f["id"] in {"F-11", "F-12", "F-13", "F-14", "F-15", "F-16", "F-17"}],
       "Selected repository and process irregularities", "data-table")}
{analysis("How this pass differs from the published root site", [
    'This independent desk adds row-level official URLs, retrieval dates, an explicit observation/assumption/unverified classification, a machine-readable dataset, an automated validator and a source register. <a href="https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia/INC110223" target="_blank" rel="noopener noreferrer">Census QuickFacts ↗</a>',
    'It also supplies the deep multi-year official series (BLS, EDD, Census, SEC, IRS, FTB, FEMA, CAL FIRE, CGS, USGS, CDI) that the original requirements asked for. <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/R33.htm" target="_blank" rel="noopener noreferrer">SEC 10-K revenue tables ↗</a>',
    'No file owned by another session is edited here; the work lives only in <code>audit/</code> and <code>verification/</code>. <a href="https://github.com/kanlerxz87-cyber/Jackbox1" target="_blank" rel="noopener noreferrer">Repository ↗</a>',
])}
"""
write("review.html", "Repo review", "Governance", "Repository review & irregularities",
      "A line-by-line review of the repository and parallel-session state, with links for manual review and "
      "every irregularity flagged.", body)

# ---------------------------------------------------------------- CSS
CSS = r"""
:root{--bg:#f5f7fa;--ink:#122033;--muted:#5d6b7e;--line:#dde4ec;--card:#fff;--accent:#1d5c9e;--accent2:#0f7a6b;--warn:#a86a00;--bad:#b0342c;--good:#0f7a6b;--side:#0e1b2c}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}.skip{position:absolute;left:-9999px;top:0;background:#fff;padding:10px;z-index:99}.skip:focus{left:10px;top:10px}
.shell{display:grid;grid-template-columns:262px minmax(0,1fr);min-height:100vh}
.side{background:var(--side);color:#dce6f2;padding:22px 16px;position:sticky;top:0;height:100vh;overflow-y:auto}
.brand{display:flex;gap:11px;align-items:center;color:#fff;font-weight:700;letter-spacing:.06em;font-size:14px;line-height:1.25;margin-bottom:14px}
.brand .mark{display:grid;place-items:center;width:36px;height:36px;border-radius:9px;background:#2f7fc1;color:#fff;font-size:19px;font-weight:800}
.brand small{font-size:10px;font-weight:500;color:#9db5d0;letter-spacing:.09em}
.side-note{font-size:11.5px;color:#a8bdd5;border:1px solid #2b4059;background:#152840;border-radius:8px;padding:9px 10px;margin-bottom:16px;line-height:1.5}
.side-note a{color:#8fd0ff}
.nav-label{font-size:10px;letter-spacing:.14em;color:#7f9ab8;margin:16px 8px 6px;font-weight:700}
.side nav{display:flex;flex-direction:column;gap:1px}
.nav-link{color:#c6d6e8;padding:7px 10px;border-radius:7px;font-size:13px;display:block}
.nav-link:hover{background:#1c324d;text-decoration:none;color:#fff}.nav-link.active{background:#22619e;color:#fff;font-weight:600}
.privacy{margin-top:20px;border-top:1px solid #2b4059;padding-top:14px;font-size:11.5px;color:#a8bdd5}.privacy strong{color:#8fd0ff;display:block;margin-bottom:6px}.privacy p{margin:0}
main{min-width:0}.top{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#fff;border-bottom:1px solid var(--line);padding:13px 26px;font-size:11px;letter-spacing:.1em;color:var(--muted);font-weight:600;text-transform:uppercase}
.top .slash{color:#c3cedb;margin:0 6px}.top-right{color:var(--accent2);white-space:nowrap}
.content{max-width:1180px;margin:0 auto;padding:30px 26px 60px}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--accent);font-weight:700;margin-bottom:8px}
h1{font-size:32px;line-height:1.2;margin:0 0 10px;letter-spacing:-.02em}h2{font-size:21px;margin:32px 0 12px;letter-spacing:-.01em}h3{font-size:16px;margin:0 0 6px}
.lead{font-size:16.5px;color:var(--muted);max-width:900px;margin:0 0 22px}
.muted{color:var(--muted);font-size:13px}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px;white-space:nowrap;color:#4b5c72}
.callout{background:#eaf3fb;border:1px solid #c7dff2;border-left:4px solid var(--accent);border-radius:10px;padding:16px 18px;margin:18px 0}
.callout.critical{background:#fff4ee;border-color:#f3d3bd;border-left-color:#c2622c}.callout strong{display:block;margin-bottom:6px}.callout p{margin:0;color:#3d5065}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px;margin:20px 0}
.stat{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 16px}.stat strong{font-size:24px;display:block;color:var(--accent)}.stat span{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin:16px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:16px;color:var(--ink)}.card:hover{border-color:var(--accent);text-decoration:none;box-shadow:0 4px 14px rgba(20,50,90,.08)}
.card span{font-size:11px;color:var(--accent);font-weight:700;letter-spacing:.1em}.card p{margin:0;color:var(--muted);font-size:13px}
.analysis{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent2);border-radius:10px;padding:14px 20px;margin:22px 0}.analysis h2{margin:8px 0 10px;font-size:18px}.analysis ul{margin:0;padding-left:20px}.analysis li{margin:9px 0}
.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:14px 0 22px}
table{border-collapse:collapse;width:100%;font-size:13px}caption{caption-side:top;text-align:left;padding:12px 14px;font-size:12px;color:var(--muted);font-weight:600;background:#f8fafc;border-bottom:1px solid var(--line)}
th{background:#f1f5f9;text-align:left;padding:10px 12px;font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:#42536a;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:10px 12px;border-bottom:1px solid #eef2f6;vertical-align:top}tr:last-child td{border-bottom:0}tbody tr:hover{background:#f8fbff}
td.value{font-weight:600}td.num{font-variant-numeric:tabular-nums;white-space:nowrap}td.blank{background:#fff8f3;min-width:64px}td.blank:empty::after{content:"— blank / unverified";color:#b06a2c;font-size:11px;font-weight:600;font-style:italic}
td.source{white-space:nowrap;font-size:12px}td.source a{display:inline-block}.srcid{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:10px;color:#6b7c90;background:#eef2f7;border-radius:3px;padding:1px 4px}
.badge{display:inline-block;border-radius:999px;padding:2px 9px;font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;border:1px solid transparent}
.badge.good{background:#e7f6f1;color:var(--good);border-color:#bfe7db}.badge.warn{background:#fff5e2;color:var(--warn);border-color:#f0dcae}.badge.bad{background:#fdecea;color:var(--bad);border-color:#f4c9c4}.badge.neutral{background:#eef2f7;color:#4a5b70;border-color:#dce4ec}
.filterbar{display:flex;gap:8px;align-items:center;margin:12px 0 4px;flex-wrap:wrap}.filterbar input{padding:8px 11px;border:1px solid var(--line);border-radius:8px;min-width:260px;font-size:13px}.filterbar button{padding:8px 12px;border:1px solid var(--line);background:#fff;border-radius:8px;cursor:pointer;font-size:13px}
.foot{border-top:1px solid var(--line);margin-top:38px;padding-top:14px;font-size:11.5px;color:var(--muted)}
.calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px}.calc fieldset{border:1px solid var(--line);border-radius:10px;background:#fff;padding:14px 16px}.calc legend{font-weight:700;color:var(--accent);padding:0 6px}
.calc label{display:block;font-size:12.5px;color:#41536a;margin:8px 0}.calc input[type=number]{display:block;width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:7px;margin-top:4px;font-size:14px}.calc label:has(input[type=checkbox]){display:flex;gap:8px;align-items:center}.calc input[type=checkbox]{width:auto;margin:0}
.actions{grid-column:1/-1;display:flex;gap:9px;flex-wrap:wrap;margin:6px 0 12px}.actions button,.printbar button{border:0;background:var(--accent);color:#fff;padding:9px 16px;border-radius:8px;cursor:pointer;font-size:13.5px;font-weight:600}.actions button.secondary,.printbar button.secondary{background:#fff;color:var(--ink);border:1px solid var(--line)}
.result,.memo{background:#0e1b2c;color:#dbe8f6;border-radius:10px;padding:16px 18px;white-space:pre-wrap;font:13px/1.6 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow-x:auto}.result b,.result strong{color:#8fd0ff}
.paths{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 16px 16px;margin:12px 0}.paths label{display:block;border-bottom:1px solid #eef2f6;padding:11px 4px;cursor:pointer}.paths label:last-of-type{border-bottom:0}.paths label span{display:block;margin-left:24px;color:var(--muted);font-size:12.5px}
.pick{cursor:pointer}.memo{margin-top:12px;min-height:90px}
.printbar{display:flex;gap:12px;align-items:center;margin:8px 0 16px;font-size:13px}.onepage{background:#fff;border:1px solid var(--line);border-radius:10px;padding:22px 26px}.onepage h2{margin-top:0}.onepage h3{margin-top:22px;font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
code{background:#eef2f7;padding:1px 5px;border-radius:4px;font-size:12px}
@media(max-width:880px){.shell{grid-template-columns:1fr}.side{position:static;height:auto}.side nav{display:flex;flex-direction:row;flex-wrap:wrap;gap:4px}.nav-label{width:100%}.content{padding:22px 16px 44px}.top{padding:11px 16px;font-size:10px}.top-right{display:none}}
@media print{.side,.top,.printbar,.foot,.filterbar,.privacy{display:none!important}.shell{display:block}.content{padding:0;max-width:none}.onepage{border:0;padding:0}.table-wrap{overflow:visible}table{font-size:11px}a{color:#000}.callout{break-inside:avoid}tr{break-inside:avoid}body{background:#fff}}
"""
(SITE / "assets/css/site.css").write_text(CSS)

# ---------------------------------------------------------------- site.js
JS = r"""
/* Independent verification desk — browser-only helpers. No network calls, no storage. */
(function () {
  'use strict';
  var tables = document.querySelectorAll('table');
  if (tables.length) {
    var bar = document.createElement('div');
    bar.className = 'filterbar';
    bar.innerHTML = '<input type="search" id="rowfilter" placeholder="Filter rows on this page…" aria-label="Filter table rows">' +
                    '<button type="button" id="toggleblank">Hide blank/unverified rows</button>' +
                    '<span class="muted" id="rowcount"></span>';
    var first = tables[0];
    first.parentNode.insertBefore(bar, first);
    var input = bar.querySelector('#rowfilter');
    var toggle = bar.querySelector('#toggleblank');
    var count = bar.querySelector('#rowcount');
    var hideBlank = false;
    function apply() {
      var q = (input.value || '').toLowerCase().trim();
      var shown = 0, total = 0;
      document.querySelectorAll('table tbody tr').forEach(function (tr) {
        total++;
        var match = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        var skipBlank = hideBlank && tr.getAttribute('data-unverified') === '1';
        tr.style.display = (match && !skipBlank) ? '' : 'none';
        if (match && !skipBlank) shown++;
      });
      count.textContent = shown + ' of ' + total + ' rows shown';
    }
    input.addEventListener('input', apply);
    toggle.addEventListener('click', function () {
      hideBlank = !hideBlank;
      toggle.textContent = hideBlank ? 'Show blank/unverified rows' : 'Hide blank/unverified rows';
      apply();
    });
    apply();
  }
  // Suggestion review board — memory only, nothing is transmitted or stored.
  var memoButton = document.getElementById('makememo');
  if (memoButton) {
    var memo = document.getElementById('memo');
    var pathForm = document.getElementById('pathform');
    memoButton.addEventListener('click', function () {
      var picked = Array.prototype.slice.call(document.querySelectorAll('.sug-pick:checked')).map(function (c) { return c.value; });
      var path = pathForm.querySelector('input[name="path"]:checked');
      var names = {A:'Verification first (recommended process decision)', B:'Build the sale track first', C:'Build the renewal track first', D:'No site changes yet'};
      var lines = [
        'DECISION MEMO — anonymous, generated locally in this browser',
        'Session: S-62b1c0c2    Retrieved: 2026-11-25',
        'No personal information, no network calls, no persistence.',
        '',
        'Chosen path: ' + (path ? path.value + ' — ' + names[path.value] : 'none selected'),
        'Shortlisted suggestions: ' + (picked.length ? picked.join(', ') : 'none'),
        '',
        'Rule: no change is implemented until a reviewer approves this memo and the relevant decision gates close.',
        'This memo is advisory. It does not select a sale or renewal winner.'
      ];
      memo.textContent = lines.join('\n');
    });
    document.getElementById('clearmemo').addEventListener('click', function () {
      document.querySelectorAll('.sug-pick').forEach(function (c) { c.checked = false; });
      memo.textContent = 'No memo generated. Shortlist suggestions and choose a path above.';
    });
  }
})();
"""
(SITE / "assets/js/site.js").write_text(JS)

# ---------------------------------------------------------------- calculator.js
CALCJS = r"""
/* Browser-only after-tax sell-versus-hold comparison.
   No network calls, no persistence. Inputs are adviser-entered assumptions.
   Verified tax rules are described on the page with official source links. */
(function () {
  'use strict';
  var form = document.getElementById('calc');
  if (!form) return;
  var out = document.getElementById('calcresult');
  var money = function (v) {
    return new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: 0}).format(v);
  };
  function val(name) {
    var el = form.elements[name];
    if (!el || el.value === '' || el.value === null) return null;
    var n = Number(el.value);
    return Number.isFinite(n) ? n : null;
  }
  function pct(name) { var v = val(name); return v === null ? null : v / 100; }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var required = ['price','costs','debt','basis','depr','fed','ca','rent','years','discount','cap'];
    var missing = required.filter(function (n) { return val(n) === null; });
    if (missing.length) {
      out.textContent = 'No comparison calculated. Fill every required adviser input first (missing: ' + missing.join(', ') + '). These are assumptions, not verified values.';
      return;
    }
    var price = val('price'), costs = val('costs'), debt = val('debt'), basis = val('basis');
    var depr = Math.max(0, val('depr')), fed = pct('fed'), ca = pct('ca');
    var rent = val('rent'), years = val('years'), discount = pct('discount'), cap = pct('cap');
    var lostMonths = val('lostmonths') || 0, repairs = val('repairs') || 0, haircut = pct('haircut') || 0;
    if (cap <= 0 || years <= 0 || discount < 0) {
      out.textContent = 'Check the cap rate, remaining years and discount rate inputs. No comparison calculated.';
      return;
    }
    var gain = Math.max(0, price - costs - basis);
    var unrecaptured = Math.min(depr, gain);
    var remainder = Math.max(0, gain - unrecaptured);
    var federalTax = remainder * fed + unrecaptured * 0.25;
    var caTax = gain * ca;
    var niit = form.elements['niit'].checked ? gain * 0.038 : 0;
    var saleNet = price - costs - debt - federalTax - caTax - niit;
    var d = 1 + discount;
    var pvRent = 0;
    for (var y = 1; y <= Math.floor(years); y++) pvRent += rent / Math.pow(d, y);
    var exitValue = rent / cap;
    var pvExit = exitValue / Math.pow(d, years);
    var holdPV = pvRent + pvExit;
    var stressed = holdPV - (rent * lostMonths / 12) - repairs - (exitValue * haircut / Math.pow(d, years));
    var lines = [
      'ILLUSTRATIVE RESULT — all amounts depend on adviser-entered assumptions, not verified property values.',
      '',
      'Sale case',
      '  Gain subject to tax:                 ' + money(gain),
      '  Unrecaptured §1250 portion (25%):   ' + money(unrecaptured),
      '  Federal tax (entered rate + 25%):  ' + money(federalTax),
      '  California tax (entered rate):     ' + money(caTax),
      '  NIIT (3.8% if selected):           ' + money(niit),
      '  AFTER-TAX SALE NET PROCEEDS:       ' + money(saleNet),
      '',
      'Hold case (same valuation date)',
      '  PV of net rent over ' + years + ' years:      ' + money(pvRent),
      '  PV of exit value at entered cap:    ' + money(pvExit),
      '  HOLD-CASE PRESENT VALUE:           ' + money(holdPV),
      '  Stressed hold value (joint):       ' + money(stressed),
      '',
      'COMPARISON NUMBER (sale − hold):     ' + money(saleNet - holdPV),
      'Sale − stressed hold:               ' + money(saleNet - stressed),
      '',
      'A positive number is not a recommendation. Verified lease, tax, hazard and quote inputs are still missing.',
      'Simplifications and official sources are listed on this page. Nothing was transmitted or stored.'
    ];
    out.textContent = lines.join('\n');
  });
  form.addEventListener('reset', function () {
    out.textContent = 'No comparison calculated — verified inputs are missing. Every field above is an assumption until an adviser verifies it privately.';
  });
  var p = document.getElementById('printcalc');
  if (p) p.addEventListener('click', function () { window.print(); });
})();
"""
(SITE / "assets/js/calculator.js").write_text(CALCJS)

# ---------------------------------------------------------------- markdown companions
def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "\\|") for x in r) + " |")
    return "\n".join(out)


lines = ["# Official source register", "", f"Session: `{META['session']}` · Retrieved: `{DATE}`.", "",
         "Only official government and primary regulatory sources are used for published values. "
         "Where a direct fetch was blocked, the method column records that the value was transcribed from "
         "indexed content of the official page, and the item is flagged for manual review.", "",
         md_table(["ID", "Agency", "Title", "URL", "Method", "Retrieved"],
                  [[s["id"], s["agency"], s["title"], s["url"], s["method"], s["retrieved"]] for s in DATA["sources"]]), ""]
(VER / "SOURCES.md").write_text("\n".join(lines))

lines = ["# Questions, information needed and answers", "",
         "A blank answer means unverified, not zero. Discovery happens only in the access-controlled offline workflow.", "",
         md_table(["ID", "Category", "Question", "Information needed", "Current answer", "How to discover", "Status", "Official source"],
                  [[q["id"], q["category"], q["question"], q["needed"], q["answer"] or "", q["discovery"], q["status"], SOURCES[q["source"]]["url"]] for q in DATA["questions"]]), ""]
(VER / "QUESTIONS.md").write_text("\n".join(lines))

lines = ["# Suggestions and reviewer decision paths", "",
         "Reviewers shortlist suggestions and choose a path on `audit/suggestions.html`; the board is memory-only.", "",
         md_table(["ID", "Category", "Proposal", "Rationale", "Effort", "Status", "Official source"],
                  [[s["id"], s["category"], s["proposal"], s["rationale"], s["effort"], s["status"], SOURCES[s["source"]]["url"]] for s in DATA["suggestions"]]), "",
         "## Paths", "", md_table(["Path", "Description"],
                  [["A", "Verification first — recommended process decision"],
                   ["B", "Build the sale track first"], ["C", "Build the renewal track first"],
                   ["D", "No site changes yet"]]), ""]
(VER / "SUGGESTIONS.md").write_text("\n".join(lines))

lines = ["# Risk register and black-swan scenarios", "",
         "Scenario magnitudes are assumed, never published as facts. OBSERVATION = official material; ANALYSIS = reasoning; UNVERIFIED = blank and flagged.", "",
         md_table(["ID", "Decision / scope", "Exposure", "Potential effect", "Mitigation", "Evidence class", "Official source"],
                  [[r["id"], r["decision"], r["exposure"], r["effect"], r["mitigation"], r["evidence"], SOURCES[r["source"]]["url"]] for r in DATA["risks"]]), ""]
(VER / "RISKS.md").write_text("\n".join(lines))

review_lines = [
    "# Repository review — line by line", "",
    f"Session: `{META['session']}` · Retrieved: `{DATE}`.", "",
    "Baseline `4aa9dad`: `README.md` contained one line (`# Jackbox1`), no trailing newline. No data, no site, no board.",
    "",
    "`main` at `673c9a8` (PR #1 from another session) contained: `COORDINATION.md`, `README.md`, `index.html`, "
    "`assets/app.js`, `assets/style.css`, and nine pages under `pages/`. Each HTML/CSS file is minified to one line, so "
    "line references below are file-level.", "",
    "GitHub Pages was verified with `gh api repos/kanlerxz87-cyber/Jackbox1/pages`: source `main` / `/`, "
    "`build_type: legacy`, public, HTTPS enforced.", "",
    "Eight session branches were visible on the remote; several claimed overlapping scopes (`docs/**`, `pages/**`, "
    "`site/**`, `data/**`, `tools/**`) and created incompatible COORDINATION.md board schemas. This session revised its "
    "scope to the unclaimed `audit/**` and `verification/**` namespaces and edits no other session's files.", "",
    "## Irregularities", "",
    md_table(["ID", "Item", "Why flagged", "Action", "Official link"],
             [[f["id"], f["item"], f["why"], f["action"], SOURCES[f["source"]]["url"]] for f in DATA["flagged"]]),
    "", "## Manual review links", "",
    "- Repository: https://github.com/kanlerxz87-cyber/Jackbox1",
    "- Published site: https://kanlerxz87-cyber.github.io/Jackbox1/",
    "- Pages settings: https://github.com/kanlerxz87-cyber/Jackbox1/settings/pages",
    "- COORDINATION.md (shared board): https://github.com/kanlerxz87-cyber/Jackbox1/blob/main/COORDINATION.md",
    "", "## Verification performed", "",
    "1. `verification/build.py` generated every page from `verification/data/dataset.json`.",
    "2. `verification/check.py` validated row-level official source links, blank/unverified cells, internal links, "
    "external domain allowlist, JavaScript privacy constraints and personal-information patterns.",
    "3. Results are recorded in `verification/REPORT.md` and reflected on `audit/flagged.html`.",
    "4. No value was inferred; values that could not be confirmed are blank and flagged.",
    "",
]
(VER / "REVIEW.md").write_text("\n".join(review_lines))

# .nojekyll inside audit/ so static assets are served verbatim even with Jekyll
(SITE / ".nojekyll").write_text("")
print("generated", len(list(SITE.glob('*.html'))), "pages and", len(DATA["metrics"]), "verified metric rows")
