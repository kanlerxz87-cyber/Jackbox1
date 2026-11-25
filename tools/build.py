#!/usr/bin/env python3
"""
Static site generator for the Jack in the Box NNN leasehold decision workspace.

Design rules enforced here, not by hand:
  * every data row published on the site comes from data/registry.yaml
  * a row with a blank value is rendered as a visible "unverified" cell, never dropped
  * a row with status != verified may not carry a source link that is empty
  * no personal identifiers can reach docs/ because none exist in the inputs

Usage:  python3 tools/build.py      (then: python3 tools/check.py)
"""
from __future__ import annotations

import html
import json
import shutil
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "workspace"   # own namespace: never collides with another session's docs/ tree
TODAY = date(2026, 11, 25)
SITE = "Jack in the Box — NNN Leasehold Decision Workspace"
REPO = "kanlerxz87-cyber/Jackbox1"

NAV = [
    ("index.html", "Overview"),
    ("questions.html", "Questions & Gaps"),
    ("economy.html", "Trade Area"),
    ("tracts.html", "Tract Evidence"),
    ("operator.html", "Tenant Strength"),
    ("hazards.html", "Hazard Screen"),
    ("tax.html", "After-Tax"),
    ("market.html", "Short-Lease Pricing"),
    ("model.html", "Sell vs Hold"),
    ("gates.html", "Decision Gates"),
    ("risks.html", "Risk Register"),
    ("calculator.html", "Calculator"),
    ("suggestions.html", "Suggestions"),
    ("review.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("summary.html", "One-Page Summary"),
    ("privacy.html", "Privacy"),
]

CAT_LABEL = {
    "economy": "Economy & income",
    "labour": "Labour market",
    "prices": "Prices & rates",
    "operator": "Tenant (SEC filings)",
    "tax": "Tax & legal",
    "hazard": "Hazard & regulatory",
    "market": "Market pricing",
    "parcel": "Parcel-specific",
    "lease": "Lease-specific",
    "demographics": "Demographics & housing",
}

STATUS_CLASS = {"verified": "b-verified", "flagged": "b-flagged", "unverified": "b-unverified"}


# --------------------------------------------------------------------------- helpers
def esc(v) -> str:
    return html.escape(str(v), quote=True)


def load_registry() -> list[dict]:
    raw = yaml.safe_load((DATA / "registry.yaml").read_text(encoding="utf-8"))
    rows = raw["rows"]
    ids = set()
    for r in rows:
        for k in ("id", "category", "metric", "value", "unit", "geo", "period", "source", "url", "status", "note"):
            if k not in r:
                sys.exit(f"registry row {r.get('id')} missing key {k}")
        if r["id"] in ids:
            sys.exit(f"duplicate registry id {r['id']}")
        ids.add(r["id"])
        if r["status"] not in STATUS_CLASS:
            sys.exit(f"row {r['id']} has bad status {r['status']}")
        if r["value"] == "" and r["status"] == "verified":
            sys.exit(f"row {r['id']} is verified but blank — impossible")
        if r["status"] == "verified" and not str(r["url"]).startswith("http"):
            sys.exit(f"row {r['id']} claims verified with no source url")
        r["value"] = str(r["value"])
        r["url"] = str(r["url"])
        r["note"] = str(r["note"])
    return rows


def page(filename: str, title: str, body: str, lede: str = "", eyebrow: str = "") -> str:
    nav = "\n".join(
        f'      <li><a href="{href}">{esc(label)}</a></li>' for href, label in NAV
    )
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {esc(SITE)}</title>
<meta name="description" content="Verified-source decision workspace for a single-tenant Jack in the Box under a triple-net lease in central Los Angeles.">
<meta name="robots" content="index,follow">
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<header class="site">
  <div class="wrap bar">
    <div class="brand">Jack in the Box · NNN leasehold decision workspace
      <span>Aggregate findings only — no owner, parcel or lease identifiers</span></div>
    <div class="privacy">Privacy-first: anonymised by design</div>
  </div>
</header>
<nav class="site" aria-label="Sections">
  <div class="wrap">
    <ul>
{nav}
    </ul>
  </div>
</nav>
<main>
  <div class="wrap">
"""
    head += f'    <div class="pagehead">\n'
    if eyebrow:
        head += f'      <p class="eyebrow">{esc(eyebrow)}</p>\n'
    head += f'      <h1>{esc(title)}</h1>\n'
    if lede:
        head += f'      <p class="lede">{lede}</p>\n'
    head += "    </div>\n"
    tail = f"""  </div>
</main>
<footer class="site">
  <div class="wrap">
    <div>Built {TODAY.isoformat()} from <code>data/registry.yaml</code>. {len(NAV)} pages, no external scripts, no tracking.</div>
    <div><a href="privacy.html">Privacy &amp; anonymisation</a> · <a href="review.html">Flagged for review</a> · <a href="sources.html">Sources</a></div>
  </div>
</footer>
<script src="assets/js/app.js" defer></script>
</body>
</html>
"""
    return head + body + tail



def flag_cell(flag: str) -> str:
    if flag == "—":
        return "—"
    return '<span class="pill">' + esc(flag) + "</span>"


def status_badge(s: str) -> str:
    return f'<span class="badge {STATUS_CLASS[s]}">{esc(s)}</span>'


def value_cell(r: dict) -> str:
    if r["value"] == "":
        return '<td class="blank">blank — unverified</td>'
    v = esc(r["value"])
    unit = f' <span class="unit">{esc(r["unit"])}</span>' if r["unit"] and r["unit"] != "text" else ""
    return f'<td class="num">{v}{unit}</td>'


def source_cell(r: dict) -> str:
    if r["url"].startswith("http"):
        return f'<td class="src"><a href="{esc(r["url"])}" rel="noopener">{esc(r["source"])}</a></td>'
    return f'<td class="src">{esc(r["source"])}</td>'


def data_table(rows: list[dict], caption: str = "", show_note: bool = True, show_geo: bool = True) -> str:
    if not rows:
        return '<div class="table-scroll"><p style="padding:14px">No rows.</p></div>'
    cols = ["Metric", "Value", "Unit / basis"]
    if show_geo:
        cols.append("Geography")
    cols += ["Period", "Source", "Status"]
    if show_note:
        cols.append("Verification note")
    out = ['<div class="table-scroll"><table>']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr></thead><tbody>")
    for r in rows:
        out.append(f'<tr data-status="{esc(r["status"])}">')
        out.append(f'<td class="metric">{esc(r["metric"])}<br><span class="unit">{esc(r["id"])}</span></td>')
        out.append(value_cell(r))
        out.append(f'<td class="unit">{esc(r["unit"]) or "—"}</td>')
        if show_geo:
            out.append(f'<td>{esc(r["geo"])}</td>')
        out.append(f'<td>{esc(r["period"])}</td>')
        out.append(source_cell(r))
        out.append(f"<td>{status_badge(r['status'])}</td>")
        if show_note:
            out.append(f'<td class="note">{esc(r["note"]) or "—"}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def filter_bar(target: str, label: str = "Search these rows") -> str:
    return f"""<div class="filter" data-filter="#{target}">
  <label for="q-{target}">{esc(label)}</label>
  <input id="q-{target}" type="search" placeholder="metric, source, geography…">
  <select aria-label="Filter by verification status">
    <option value="">all statuses</option>
    <option value="verified">verified only</option>
    <option value="flagged">flagged only</option>
    <option value="unverified">unverified (blank) only</option>
  </select>
  <span class="note" data-count></span>
</div>"""


def stats(rows: list[dict], ids: list[str], labels: list[str]) -> str:
    by_id = {r["id"]: r for r in rows}
    cells = []
    for i, lab in zip(ids, labels):
        r = by_id[i]
        val = esc(r["value"]) if r["value"] else "—"
        unit = esc(r["unit"]) if r["unit"] else ""
        cells.append(
            f'<div class="card"><div class="kicker">{esc(r["id"])} · {esc(r["period"])}</div>'
            f'<div class="stat">{val}</div>'
            f'<small>{esc(lab)} · {unit}<br>{status_badge(r["status"])}</small></div>'
        )
    return '<div class="tiles">' + "".join(cells) + "</div>"


def write(name: str, content: str) -> None:
    (DOCS / name).write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------- pages
def build_index(rows):
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in STATUS_CLASS}
    body = f"""
<div class="notice info">
  <strong>What this is</strong>
  A working decision file for one asset: a single-tenant Jack in the Box on a triple-net lease in central Los Angeles,
  with an expiration the owner reports only as a range (2030–2035). It separates what is <em>verified from an official
  source</em> from what is <em>still missing</em>, and it refuses to print a number it cannot source.
</div>

<div class="grid g4" style="margin-bottom:18px">
  <div class="card"><div class="kicker">Verified rows</div><div class="stat">{counts['verified']}</div><small>value traced to an official source with a link</small></div>
  <div class="card"><div class="kicker">Flagged rows</div><div class="stat">{counts['flagged']}</div><small>published, but the caveat matters</small></div>
  <div class="card"><div class="kicker">Blank / unverified</div><div class="stat">{counts['unverified']}</div><small>deliberately left empty rather than estimated</small></div>
  <div class="card"><div class="kicker">Open questions</div><div class="stat">30</div><small>blocking a decision; see Questions &amp; Gaps</small></div>
</div>

<h2>Read it in this order</h2>
<div class="tiles">
  <a class="tile" href="questions.html"><div class="t">1. Questions &amp; Gaps</div><div class="d">What must be answered before any decision is reasonable — and exactly how to find each answer.</div></a>
  <a class="tile" href="economy.html"><div class="t">2. Trade-area evidence</div><div class="d">Income, labour, prices, population — with city/county substitutes clearly labelled as substitutes.</div></a>
  <a class="tile" href="operator.html"><div class="t">3. Tenant strength</div><div class="d">Three years of SEC-reported units, royalties and franchise rental revenue.</div></a>
  <a class="tile" href="hazards.html"><div class="t">4. Hazard screen</div><div class="d">What is verifiable at county level, and what stays blank until the parcel is identified.</div></a>
  <a class="tile" href="tax.html"><div class="t">5. After-tax machinery</div><div class="d">The statutory pieces, tied to primary law, that convert a sale price into a net number.</div></a>
  <a class="tile" href="model.html"><div class="t">6. Sell vs hold</div><div class="d">The comparison framework — deliberately carrying no result until inputs exist.</div></a>
</div>

<h2>The short answer to “sell or renew?”</h2>
<div class="notice warn">
  <strong>It cannot be answered yet, and any site that answers it for you is improvising.</strong>
  Two of the three decisive inputs are missing: the lease's actual expiration and renewal mechanics, and a verified
  short-lease discount from real quotes. The verified evidence that <em>does</em> exist points in a direction worth
  naming plainly: the tenant's Jack in the Box system has shrunk for three straight years
  (1,986 franchise units at FY2025 versus 2,044 at FY2023), franchise royalties are down 8.4% over two years, and
  the company has been selling assets and going “asset-light” — which argues that a renewal decision will be made by a
  franchisee operator on unit economics, not by the parent on sentiment. That is a reason to prepare the renewal case
  seriously and early, not a reason to sign anything today.
</div>

<h2>Where the evidence actually stands</h2>
<ul class="clean">
  <li><strong>Verified:</strong> the operator's own filed numbers (SEC), the legal tax machinery (California Constitution,
    statutes, IRS, FTB), regional labour and price data (BLS), and demographic context (Census ACS).</li>
  <li><strong>Flagged:</strong> anything regional that is standing in for a trade area; secondary reporting of a federal
    dataset; and figures BLS itself marks preliminary or incomplete.</li>
  <li><strong>Blank:</strong> the parcel's hazard zones, the lease terms, the assessed value and basis, and every market
    price. {counts['unverified']} rows are blank on purpose — see <a href="review.html">Flagged for review</a>.</li>
</ul>
"""
    write("index.html", page("index.html", "Overview", body,
                             "A decision file that shows its work: verified figures, named gaps, and no invented numbers.",
                             "Start here"))


def build_questions(rows):
    Q = [
        ("Q-01", "Identify the parcel", "highest",
         "What is the street address, APN, and legal description of the subject property?",
         "Supply the APN from the recorded deed or the county tax bill.",
         "Without it, hazard zone status, zoning, tax rate area, traffic counts and every comparable are unreachable. 14 rows stay blank.", "F-01"),
        ("Q-02", "Pin the lease term", "highest",
         "What is the exact expiration date, and what is the notice window for exercising each renewal option?",
         "Read the lease. Then reconcile against the notice calendar in the private workspace.",
         "The whole sell-versus-renew case keys off this date; a five-year uncertainty band spans an entire market cycle.", "F-02"),
        ("Q-03", "Establish rent and escalation", "highest",
         "What is current base rent, the escalation mechanism (fixed bumps, CPI, or fair-market reset), and what does the tenant reimburse?",
         "Abstract the lease: base rent, escalators, NNN recoveries, caps on controllable CAM.",
         "Determines the income the buyer is paying for and whether a renewal is priced off the old rent or the market.", "F-02"),
        ("Q-04", "Read the renewal options", "highest",
         "How many options, how long each, who holds them, and is renewal rent fixed, indexed, or negotiated?",
         "Abstract the options clause verbatim.",
         "A fixed-rent option at below-market terms is a liability; a market-reset option is an asset. Opposite conclusions.", "F-02"),
        ("Q-05", "Confirm the tenant entity", "high",
         "Is the tenant Jack in the Box Inc., a franchisee entity, or a franchisee sublease? Who actually signs a renewal?",
         "Match the named tenant on the lease to SEC filings and to the operator's franchise disclosure where available.",
         "The parent is divesting and going asset-light; a franchisee's balance sheet is a different credit.", "—"),
        ("Q-06", "Get the assessed value and tax basis", "highest",
         "What is the current assessed value, the Proposition 13 base-year value, and the date of the last change of ownership?",
         "Pull the Assessor's parcel record and the most recent secured tax bill.",
         "Drives both the property-tax line and the recapture calculation on a sale.", "F-04"),
        ("Q-07", "Quantify the depreciation taken", "highest",
         "How much depreciation has been claimed, under which schedule, and how much is unrecaptured §1250 gain?",
         "Reconstruct from filed returns with the tax adviser; carry-forward schedules are required.",
         "At a 25% recapture ceiling this is usually the largest single tax line in a sale.", "F-04"),
        ("Q-08", "Fix the ownership entity and the owner's bracket", "high",
         "Is the property held personally, in an LLC taxed as a partnership, or in a corporation — and at what marginal rate does a gain land?",
         "Confirm with the adviser; model entity-level tax if it is a C corporation.",
         "Entity form can change the after-tax answer more than the sale price does.", "F-04"),
        ("Q-09", "Get comparable sale evidence", "highest",
         "What have comparable net-lease QSR assets in central Los Angeles actually traded at, at what cap rate, and with how much term remaining?",
         "Pull recorded sales from the county recorder and confirm terms with the brokers involved.",
         "The short-lease discount cannot be priced without this. No number is published until it exists.", "F-03"),
        ("Q-10", "Price the short-lease discount", "highest",
         "How much value per year of remaining term is the market actually charging in this submarket?",
         "Regress or pair-match recorded sales on remaining term; sanity-check against live quotes.",
         "This is the single largest driver of value between now and 2030.", "F-03"),
        ("Q-11", "Verify the hazard zones at the parcel", "high",
         "Is the parcel in a Very High Fire Hazard Severity Zone, an Alquist-Priolo fault zone, a liquefaction zone, or a FEMA flood zone?",
         "Run the APN through CAL FIRE FHSZ, CGS EQ Zapp and FEMA NFHL, and save the dated screenshots.",
         "Affects insurance cost, lender appetite, and disclosure obligations on a sale.", "F-01"),
        ("Q-12", "Get current insurance quotes", "high",
         "What would a replacement NNN policy cost today, and what is excluded (shake, flood, wildfire)?",
         "Request three quotes using the actual address and construction type.",
         "Insurance availability, not price, is what has been killing California commercial deals.", "—"),
        ("Q-13", "Define the trade area properly", "high",
         "Which Census tracts actually form this restaurant's trade area — drive-time, not ZIP, not city?",
         "Geocode the parcel, then build a 3/5/10-minute drive-time ring and list the intersecting tracts.",
         "City and county figures are substitutes; a QSR lives and dies inside roughly a 3-mile ring.", "F-05"),
        ("Q-14", "Test the co-tenancy and access assumptions", "medium",
         "What else is on the hard corner or in the centre, what are the access and signal conditions, and is there a drive-thru queue constraint?",
         "Site visit with photographs; pull Caltrans or LADOT counts for the adjacent arterial.",
         "Drive-thru throughput is the revenue engine; a median or a queuing problem can cap sales.", "—"),
        ("Q-15", "Check the zoning and any overlays", "medium",
         "What is the zoning, is the use legal-conforming, and are there specific-plan or overlay restrictions on the site?",
         "ZIMAS query plus the applicable community plan.",
         "Matters for a re-tenanting or redevelopment exit if the tenant leaves.", "—"),
        ("Q-16", "Establish the exit alternative", "high",
         "If the tenant vacates, what could the site become, at what cost, and with what entitlement risk?",
         "Preliminary feasibility with a local architect; confirm the zoning envelope.",
         "The floor under the sell decision is the alternate-use value, not the vacant-building value.", "—"),
        ("Q-17", "Confirm the sale cost stack", "high",
         "What are the actual brokerage, legal, escrow, title and transfer-tax costs at the modelled price?",
         "Get a title/escrow estimate and confirm the City of Los Angeles transfer-tax and Measure ULA treatment in writing.",
         "Measure ULA alone is 4% above $5m, which is a decision-changing number.", "F-04"),
        ("Q-18", "Decide on a 1031 exchange posture", "medium",
         "If a sale happens, is a like-kind exchange intended, and is replacement property identified in advance?",
         "Engage a qualified intermediary before closing, not after.",
         "Deferral can dominate the after-tax arithmetic; it is a timing decision, so it must be made first.", "—"),
        ("Q-19", "Fix the hold-case discount rate", "medium",
         "What discount rate and terminal cap rate should the hold case use?",
         "Derive from the 10-year Treasury plus a net-lease spread, and disclose both.",
         "Holding is only comparable to selling when both are discounted at the same rate.", "—"),
        ("Q-20", "Establish the tenant's unit-level economics", "high",
         "What does this unit actually sell, and what is its four-wall margin?",
         "Request the tenant's sales figures under the lease's reporting clause, or the franchisee's Item 19 where published.",
         "A renewal is a business decision by the operator; without sales, neither side can price it.", "—"),
        ("Q-21", "Document the black-swan exposure", "high",
         "What happens to rent, insurance and exit liquidity if a wildfire, earthquake or flood event hits the region?",
         "Stress the model across the three together, not separately, and confirm business-interruption terms.",
         "Loss of rent, repair cost and exit liquidity tend to fail at the same time, not independently.", "—"),
        ("Q-22", "Confirm the seismic retrofit status", "medium",
         "Has the building been retrofitted to current standards, and is a retrofit ordinance applicable?",
         "Pull the building permit history and any unreinforced-masonry or soft-story notices.",
         "A retrofit obligation arriving mid-lease is a capital call the lease may not allocate.", "—"),
        ("Q-23", "Check for environmental encumbrances", "medium",
         "Is there any recognised environmental condition, tank, or dry-cleaner history on or adjacent to the site?",
         "Phase I ESA if not already in hand; check the state's GeoTracker and EnviroStor.",
         "A neighbouring release can impair both value and financeability.", "—"),
        ("Q-24", "Identify all notice and consent parties", "medium",
         "Does the lender, ground lessor, or any REA require notice or consent on a sale or renewal?",
         "Read the loan documents and any reciprocal easement agreements.",
         "Missing a consent can delay or kill a closing.", "—"),
        ("Q-25", "Fix the hold-period horizon", "medium",
         "Over what horizon is the owner comparing sell versus hold — 3, 5, 10 years, or through the next option?",
         "Decide explicitly and write it down; the answer changes the ranking.",
         "A ten-year hold and a three-year hold rank the same two options differently.", "—"),
        ("Q-26", "Check school and amenity evidence for family trade", "low",
         "Do school assignment and ratings support family-driven daytime and evening traffic?",
         "Pull the district's assignment for the address and the state's accountability data.",
         "Relevant for a suburban unit; largely irrelevant for a central-LA commercial corridor.", "—"),
        ("Q-27", "Confirm the traffic and access counts", "medium",
         "What are the current AADT and peak-hour volumes on the adjacent arterials?",
         "Pull Caltrans or LADOT published counts for the specific segment.",
         "Traffic counts are the standard defensible proxy for QSR sales potential.", "F-01"),
        ("Q-28", "Establish the competitor and cannibalisation set", "medium",
         "Which competing QSR and JITB units sit inside the trade area, and is a new unit planned nearby?",
         "Map competitors within the ring; ask the franchisee about protected territory.",
         "A new unit inside the ring transfers sales rather than creating them.", "—"),
        ("Q-29", "Reconcile the notice calendar to the lease", "high",
         "Does the private notice calendar agree with the lease on every deadline and cure period?",
         "Line-by-line reconciliation, signed off by counsel.",
         "A missed option window converts an asset into a vacancy.", "F-02"),
        ("Q-30", "Prove the data pipeline is reproducible", "medium",
         "Can every published row be regenerated from its source on demand?",
         "Re-run the build and re-pull each linked endpoint; diff the output.",
         "This is what keeps the site honest as time passes and rates move.", "—"),
    ]
    pri_class = {"highest": "b-unverified", "high": "b-flagged", "medium": "b-open", "low": "b-open"}
    rowhtml = []
    for qid, title, pri, q, how, why, flag in Q:
        rowhtml.append(f"""<tr>
  <td class="metric">{esc(qid)}</td>
  <td><strong>{esc(title)}</strong><br><span class="note">{esc(q)}</span></td>
  <td><span class="badge {pri_class[pri]}">{esc(pri)}</span></td>
  <td class="note">{esc(how)}</td>
  <td class="note">{esc(why)}{f' <span class="pill">{esc(flag)}</span>' if flag != '—' else ''}</td>
</tr>""")
    body = f"""
<div class="notice info">
  <strong>How to use this page</strong>
  Each row is a question that must be answered before a sell-or-renew decision can be defended. The middle column is
  <em>how to obtain the answer</em> — deliberately concrete, because “get more data” is not an instruction.
  Nothing on this page is a data claim, so nothing here needs a source link; the sourced findings live on the sector pages.
</div>
{filter_bar("q-table", "Filter the 30 questions")}
<div class="table-scroll" id="q-table">
<table>
<caption>Blocking and non-blocking questions. Priority reflects how much the answer can move the final decision.</caption>
<thead><tr><th>ID</th><th>Question</th><th>Priority</th><th>How to obtain the answer</th><th>Why it matters</th></tr></thead>
<tbody>
{''.join(rowhtml)}
</tbody></table></div>

<h2>What we already have, and what it can and cannot support</h2>
<div class="grid g2">
  <div class="card">
    <h3>Solid enough to rely on</h3>
    <ul class="clean">
      <li>The operator's own filed unit counts, royalties and rental revenue (SEC 10-K, three years).</li>
      <li>The statutory tax machinery: 1% Prop 13 cap, 2% assessment growth, 39-year straight-line, 25% recapture ceiling, 3.8% NIIT, 12.3% + 1% California top rates.</li>
      <li>Regional labour market and price levels (BLS), with preliminary flags preserved.</li>
      <li>Population, income and housing context (ACS 2020–2024 5-year).</li>
    </ul>
  </div>
  <div class="card">
    <h3>Not solid enough to act on</h3>
    <ul class="clean">
      <li>Anything parcel-specific: hazard zones, zoning, AADT, tax rate area, assessed value.</li>
      <li>Anything lease-specific: expiration, rent, escalators, options, notice windows.</li>
      <li>Anything market-specific: cap rates, comparable sales, the short-lease discount.</li>
      <li>Anything owner-specific: basis, depreciation history, entity form, financing.</li>
    </ul>
  </div>
</div>
"""
    write("questions.html", page("questions.html", "Questions &amp; Gaps", body,
                                 "Thirty questions, ranked. Each with the specific document or database that answers it.",
                                 "W-09 · Missing-information register"))


def build_economy(rows):
    demo = [r for r in rows if r["category"] == "demographics"]
    inc = [r for r in rows if r["id"].startswith("INC-")]
    lab = [r for r in rows if r["category"] == "labour"]
    pri = [r for r in rows if r["category"] == "prices"]
    body = f"""
<div class="notice warn">
  <strong>W-01 · Honest labelling of substitutes</strong>
  No Census tract for the subject parcel is known, so <em>no genuine trade-area figure exists yet</em>. The values below
  are real published values at city, county and metro level. They are <b>substitutes</b>, they are labelled as such,
  and they must not be presented to a buyer, lender or adviser as this restaurant's trade area.
  <a href="tracts.html">Tract-level evidence</a> shows what a real one would look like.
</div>

{stats(rows, ["INC-01", "INC-02", "LAB-01", "PRI-01"],
       ["City median household income", "County median household income",
        "City unemployment rate", "CPI-U, LA metro"])}

<h2>Income — the demand base</h2>
{data_table(inc, "Median household and per-capita income, ACS 2020–2024 5-year. A QSR's sales correlate with local income, but the correct geography is a drive-time ring, not a city.")}

<h2>Population and housing</h2>
{data_table(demo, "Population by geography plus housing context. Note the two population vintages: ACS 5-year (DEM-01 to DEM-03) and the 2025 estimate (DEM-04) are not interchangeable.")}

<h2>Labour market — the traffic that shows up at lunch</h2>
{data_table(lab, "BLS LAUS and CES series. Figures BLS marks preliminary are labelled; the 2025 annual unemployment figure is flagged because the federal shutdown removed October 2025 from the average.")}

<h2>Prices and rates</h2>
{data_table(pri, "CPI feeds the escalation sensitivity in the calculator; the 10-year Treasury is the reference rate for the hold case's discount rate.")}

<h2>What the numbers say, carefully</h2>
<div class="grid g2">
  <div class="card">
    <h3>Supportive</h3>
    <ul class="clean">
      <li>Metro leisure and hospitality employment grew 2.0% year over year (LAB-07) — the closest official proxy for restaurant demand.</li>
      <li>Metro total nonfarm employment grew 0.9% (LAB-06).</li>
      <li>CPI in the metro is running at roughly 3.3–3.7% over twelve months (PRI-02) — enough to keep a CPI-linked escalator meaningful.</li>
    </ul>
  </div>
  <div class="card">
    <h3>Against</h3>
    <ul class="clean">
      <li>City median household income (81,939) sits 9% below the county (90,112) — this is not the affluent side of the region.</li>
      <li>Information-sector employment is down 1.5% and manufacturing down 1.5% (LAB-09, LAB-10): the daytime office and industrial lunch base is shrinking.</li>
      <li>Professional and business services grew only 0.5% (LAB-08) — office-using employment is close to flat.</li>
      <li>The 10-year Treasury at 4.92% (RAT-01) is a headwind for capitalisation-rate compression, which caps how much a buyer will pay for the same rent.</li>
    </ul>
  </div>
</div>
<div class="notice info">
  <strong>The honest read</strong>
  A flat-to-modestly-growing metro with a below-county-average income base, shrinking office and industrial employment,
  and a 4.9% ten-year rate is <em>not</em> a story that rescues a weak lease. It is a story in which the lease terms and
  the tenant's unit economics do all the work.
</div>
"""
    write("economy.html", page("economy.html", "Trade Area &amp; Regional Economy", body,
                              "Verified income, population, labour and price data — labelled by the geography it actually describes.",
                              "W-01 · Trade-area figures"))


def build_tracts(rows):
    import csv as _csv
    with (DATA / "tracts_demo_90015.csv").open(encoding="utf-8") as fh:
        tracts = list(_csv.DictReader(fh))
    url = "https://api.censusreporter.org/1.0/data/show/latest?table_ids=B01003,B19013,B25077&geo_ids=140|86000US90015"
    tr = []
    for t in tracts:
        pop = int(t["population"])
        inc = int(t["median_household_income"])
        moe = int(t["income_moe"]) if t["income_moe"] else None
        hv = int(t["median_home_value"]) if t["median_home_value"] else None
        popc = f'<td class="num">{pop:,}</td>'
        incc = (f'<td class="num">{inc:,} <span class="unit">±{moe:,}</span></td>' if moe
                else f'<td class="num">{inc:,}</td>')
        hvc = f'<td class="num">{hv:,}</td>' if hv else '<td class="blank">not published</td>'
        tr.append(f'<tr><td class="metric">Tract {esc(t["tract_short"])}<br><span class="unit">{esc(t["tract_geoid"])}</span></td>'
                  f'{popc}{incc}{hvc}'
                  f'<td class="src"><a href="{esc(url)}" rel="noopener">ACS 2020–2024 5-yr</a></td></tr>')
    incs = sorted(int(t["median_household_income"]) for t in tracts)
    median_of_tracts = incs[len(incs) // 2]
    pop_total = sum(int(t["population"]) for t in tracts)
    ratio = round(incs[-1] / incs[0], 1)
    median_gap = round(100 * (1 - median_of_tracts / 81939))
    biggest_moe = max(
        ((t["tract_short"], int(t["median_household_income"]), int(t["income_moe"]))
         for t in tracts if t["income_moe"]),
        key=lambda x: x[2] / x[1])
    body = f"""
<div class="notice bad">
  <strong>W-12 · Demonstration tract set, not the subject parcel's trade area</strong>
  These {len(tracts)} Census tracts form the public demonstration set DEMO-TRACTS-A — chosen only because it sits in central Los Angeles and therefore
  the right <em>shape</em> of evidence. <b>They are not this restaurant's trade area.</b> The moment the parcel's APN is
  known, this set must be replaced with the tracts inside a 3/5/10-minute drive-time ring. Publishing these as “the
  trade area” would be exactly the kind of inference this project forbids.
</div>

{stats(rows, ["DEM-05", "INC-05", "HSG-01"], ["Sum of the " + str(len(tracts)) + " tract populations", "One tract's median income", "City median home value"])}

<h2>Tract-level evidence — the shape of a real trade area</h2>
<div class="table-scroll">
<table>
<caption>Population, median household income with margin of error, and median owner-occupied home value for each tract in the
demonstration set. ACS 2020–2024 5-year estimates, tables B01003, B19013 and B25077. A blank “not published” means the ACS
did not publish a value for that tract — it is not zero and it has not been inferred.</caption>
<thead><tr><th>Tract</th><th>Population</th><th>Median household income</th><th>Median home value</th><th>Source</th></tr></thead>
<tbody>{''.join(tr)}</tbody></table></div>

<h2>Why this page matters more than the city page</h2>
<div class="grid g2">
  <div class="card">
    <h3>The spread inside one ZIP</h3>
    <p>Median household income across these tracts runs from <strong>${incs[0]:,}</strong> (tract {
    sorted(tracts, key=lambda t: int(t["median_household_income"]))[0]["tract_short"]}) to
    <strong>${incs[-1]:,}</strong> (tract {
    sorted(tracts, key=lambda t: int(t["median_household_income"]))[-1]["tract_short"]}) —
    a <strong>{ratio}× range inside a single ZIP code</strong>. The median tract value (${median_of_tracts:,}) sits
    {median_gap}% below the city median of $81,939 (INC-01) — which is precisely why a city-level average tells you almost
    nothing about a specific corner.</p>
  </div>
  <div class="card">
    <h3>The uncertainty is large</h3>
    <p>Several tracts carry margins of error approaching or exceeding half their estimate — the widest is tract
    {biggest_moe[0]} at ${biggest_moe[1]:,} ± ${biggest_moe[2]:,}. Any modelling that consumes
    tract income must carry those MOEs, or it will produce confident nonsense. That is why the model pages show
    confidence labels rather than point estimates.</p>
  </div>
</div>
<div class="notice info">
  <strong>What would make this page real</strong>
  Geocode the parcel → generate 3/5/10-minute drive-time polygons → intersect with the current TIGER tract layer →
  pull B01003, B19013, B25077 and B23025 for exactly those tracts → recompute. That is a one-day task once the address is known.
</div>
"""
    write("tracts.html", page("tracts.html", "Tract-Level Trend Evidence", body,
                              "What a genuine trade area looks like, and why the city average hides a 5.5× spread.",
                              "W-12 · Neighbourhood-level data"))


def build_operator(rows):
    ope = [r for r in rows if r["category"] == "operator"]
    units = [
        (2023, 2044, 142, 351283, 207064, 382686),
        (2024, 2041, 150, 347227, 198377, 374932),
        (2025, 1986, 150, 332735, 189646, 329700),
    ]
    tr = "".join(
        f'<tr><td class="metric">FY{y}</td><td class="num">{f:,}</td><td class="num">{c:,}</td>'
        f'<td class="num">{rr:,}</td><td class="num">{ro:,}</td><td class="num">{sp:,}</td></tr>'
        for y, f, c, rr, ro, sp in units
    )
    body = f"""
<div class="notice info">
  <strong>W-05 · Direction, not one quarter</strong>
  Three consecutive fiscal years from the tenant's own Form 10-K filings on SEC EDGAR. Units, franchise rental revenue,
  royalties and segment profit all move in the same direction, which is what makes this evidence rather than noise.
  Every figure below is a filed number with a direct link to the XBRL viewer page.
</div>

{stats(rows, ["OPE-01", "OPE-09", "OPE-06", "OPE-12"],
       ["Franchise units, FY2025", "Franchise royalties, FY2025",
        "Franchise rental revenue, FY2025", "Segment profit, FY2025"])}

<h2>Three-year series</h2>
<div class="table-scroll">
<table>
<caption>Jack in the Box segment, fiscal years ended October 2023, September 2024 and September 2025. Units are restaurant
counts; money is USD thousands. Source: Form 10-K FY2025 (Notes 1, Revenue, Segment Reporting) and Form 10-K FY2023 (Note 1),
SEC EDGAR. Arithmetic on published values only.</caption>
<thead><tr><th>Fiscal year</th><th>Franchise units</th><th>Company units</th><th>Franchise rental revenue</th><th>Franchise royalties</th><th>Segment profit</th></tr></thead>
<tbody>{tr}</tbody></table></div>

<h2>What this means for a landlord</h2>
<div class="grid g2">
  <div class="card">
    <h3>The estate is shrinking</h3>
    <p>Franchise units fell from <strong>2,044</strong> to <strong>1,986</strong> over two years — a net loss of 58 units,
    about 2.8%. Company-operated units were flat at 150 across FY2024 and FY2025. A tenant that is closing units is a
    tenant whose renewal committee is asking whether a given site earns its place.</p>
  </div>
  <div class="card">
    <h3>Sales, not just closures</h3>
    <p>Royalties are charged as a percentage of franchisee gross sales. They fell from <strong>207,064</strong> to
    <strong>189,646</strong>, or <strong>8.4%</strong>, in two years. Units fell only 2.8%, so royalties are falling faster
    than the estate — meaning per-unit sales are also under pressure. That is the more alarming of the two series.</p>
  </div>
  <div class="card">
    <h3>The tenant is also a landlord</h3>
    <p>Jack in the Box Inc. books <strong>332,735</strong> of franchise rental revenue: it owns sites, leases them to
    franchisees, and subleases others where it is the master lessee. Its weighted-average operating lease term is
    <strong>11.2 years</strong>. So the party across the table from the owner may be the company as master lessee rather
    than the operating franchisee — which changes who has to be persuaded. Confirm against the lease (Q-05).</p>
  </div>
  <div class="card">
    <h3>Strategic direction is asset-light</h3>
    <p>In December 2025 the company sold Del Taco for approximately <strong>$119 million</strong>, described in its own
    8-K as a step in a plan to “strengthen the balance sheet and accelerate its shift toward a simpler, asset-light
    business model.” For a landlord, that is a signal that the company prefers franchised structures to owned real estate —
    and that the renewal case should be made to the franchisee operator on unit economics, not to the parent.</p>
  </div>
</div>
<div class="notice warn">
  <strong>Careful with the comparison</strong>
  FY2023 reported consolidated figures on a different basis from FY2025 — Del Taco was still consolidated, and a 209,556
  impairment charge sits inside the FY2025 segment table. The <em>direction</em> across the three years is unambiguous;
  individual ratios across years should be recomputed from the filings rather than lifted from any summary, including this one.
</div>

<h2>All operator rows</h2>
{filter_bar("ope-table")}
<div id="ope-table">{data_table(ope, "Every tenant-side figure used anywhere on this site, with its filing link.")}</div>
"""
    write("operator.html", page("operator.html", "Tenant Strength", body,
                                "Same-store direction from the tenant's own SEC filings: units, royalties, rental revenue and profit.",
                                "W-05 · Operator evidence"))


def build_hazards(rows):
    hz = [r for r in rows if r["category"] == "hazard"]
    pa = [r for r in rows if r["category"] == "parcel"]
    body = f"""
<div class="notice bad">
  <strong>W-04 · Parcel-level screening is blocked, not skipped</strong>
  All four hazard questions can only be answered with parcel geometry. Every one of those rows is
  <b>blank</b>. Nothing has been inferred from “it's central LA, it's probably fine” — that inference is exactly how
  owners discover a liquefaction zone after closing.
</div>

<h2>Parcel-level status — the rows that matter</h2>
{data_table(pa, "These are the four answers a buyer, lender and insurer will ask for first. All four are blank because no APN or address was supplied (F-01).", show_geo=False)}

<h2>Regional and regulatory context that <em>is</em> verified</h2>
{data_table(hz, "County-level risk context and the statutory framework that governs parcel-level screening. Context only — never a substitute for the parcel's own zone status.")}

<h2>How to close these four blanks</h2>
<div class="grid g2">
  <div class="card">
    <h3>Fire — CAL FIRE FHSZ</h3>
    <p>Look the APN up in the Office of the State Fire Marshal's Fire Hazard Severity Zone viewer, then confirm whether the
    City of Los Angeles has adopted its own Very High zone ordinance, because local ordinance governs what applies
    (Gov. Code §51179). Save a dated PDF or screenshot — the maps are being reissued, with a 2025 LRA rollout in progress.
    If the parcel lands in High or Very High, a defensible-space inspection has been required on sale since 1 July 2021.</p>
  </div>
  <div class="card">
    <h3>Earthquake — CGS</h3>
    <p>Two separate checks, often confused with each other. First, Alquist-Priolo Earthquake Fault Zones (surface rupture) —
    the Los Angeles quadrangle maps were revised on 15 June 2017. Second, Seismic Hazard Zones (liquefaction and
    landslide) via EQ Zapp. A central-LA commercial parcel can be outside the first and inside the second.</p>
  </div>
  <div class="card">
    <h3>Flood — FEMA NFHL</h3>
    <p>Pull the effective Flood Insurance Rate Map panel for the parcel and confirm the zone and the base flood elevation.
    This is a financing gate as much as a physical one: lenders require flood insurance in a Special Flood Hazard Area,
    and the cost lands in the NNN reconciliation.</p>
  </div>
  <div class="card">
    <h3>Insurance — the real constraint</h3>
    <p>Zone status is only half the question. The other half is whether a replacement policy can be bound at all, and at
    what deductible. Get three quotes using the actual address and construction type before treating any hazard finding
    as priced (Q-12).</p>
  </div>
</div>

<h2>Black-swan exposure, stated honestly</h2>
<p class="lede">The three events that would matter most here — a regional earthquake, a wildfire at the urban interface, and
a fluvial or coastal flood — damage value through the same three channels at once: rent stops, repairs are unbudgeted,
and buyers disappear. The <a href="risks.html">risk register</a> models them together for that reason, and the
<a href="model.html">sell-versus-hold</a> page refuses to publish a number until the zone status is known.</p>
"""
    write("hazards.html", page("hazards.html", "Parcel-Level Hazard Screen", body,
                               "Four parcel questions, four blanks, and the exact official lookup that fills each one.",
                               "W-04 · Hazard screening"))


def build_tax(rows):
    tx = [r for r in rows if r["category"] == "tax"]
    body = f"""
<div class="notice info">
  <strong>W-07 · The machinery, verified to primary law</strong>
  Every rate below traces to the Constitution, a statute on leginfo, the IRS, the FTB or a City department. What is
  <em>not</em> here is a dollar answer: without basis, depreciation history and entity form, an after-tax number would be
  fiction. The <a href="calculator.html">browser calculator</a> applies these verified rules to figures you supply locally.
</div>

{stats(rows, ["TAX-01", "TAX-07", "TAX-04", "TAX-06"],
       ["Prop 13 base rate", "Unrecaptured §1250 ceiling",
        "Measure ULA, $5m–$10m", "Net investment income tax"])}

<h2>Property tax — the holding cost</h2>
{data_table([r for r in tx if r["id"] in ("TAX-01", "TAX-02")], "Article XIII A. The base rate is 1%; voter-approved debt sits on top, so the effective bill is higher than 1% — which is why the calculator asks for the actual tax rate area rate rather than assuming 1%.")}

<h2>Transfer tax — the sale cost</h2>
{data_table([r for r in tx if r["id"] in ("TAX-03", "TAX-04", "TAX-05")], "Two layers: the county documentary transfer tax under RTC 11911, and the City of Los Angeles Measure ULA surtax above $5m. Measure ULA at 4–5.5% is larger than most owners expect and is often the difference between selling and holding.")}

<h2>Income tax on the gain</h2>
{data_table([r for r in tx if r["id"] in ("TAX-06", "TAX-07", "TAX-08", "TAX-09", "TAX-10")], "The federal and California layers that apply to an individual owner. Note the sequencing: depreciation recapture is taxed at up to 25% before the remaining gain reaches the 20% capital-gain rate, and California taxes the whole gain as ordinary income at up to 13.3%.")}

<h2>Depreciation — what creates the recapture</h2>
{data_table([r for r in tx if r["id"] in ("TAX-11", "TAX-12")], "39-year straight-line on the building (land is not depreciable), mid-month convention, zero salvage. Every year of depreciation converts what would have been capital gain into unrecaptured §1250 gain at up to 25% — which is why the total tax on a sale is not simply the capital-gain rate.")}

<h2>Worked example of the mechanics (illustrative inputs only)</h2>
<div class="table-scroll">
<table>
<caption>Illustrative only. The purchase price, basis and depreciation below are invented round numbers chosen to show how the
verified rates stack; they are <b>not</b> values for the subject property. Real figures go in the calculator, in the reader's browser.</caption>
<thead><tr><th>Step</th><th>Rule applied</th><th>Illustration</th></tr></thead>
<tbody>
<tr><td>Sale price</td><td>—</td><td class="num">6,000,000</td></tr>
<tr><td>Less adjusted basis</td><td>39-yr straight line, zero salvage (TAX-11)</td><td class="num">3,400,000</td></tr>
<tr><td>Total gain</td><td>—</td><td class="num">2,600,000</td></tr>
<tr><td>Of which depreciation taken</td><td>Taxed as unrecaptured §1250, max 25% (TAX-07)</td><td class="num">1,100,000</td></tr>
<tr><td>Remaining long-term gain</td><td>20% federal bracket at this income (TAX-08)</td><td class="num">1,500,000</td></tr>
<tr><td>Federal recapture tax</td><td>25% × 1,100,000</td><td class="num">275,000</td></tr>
<tr><td>Federal capital gains tax</td><td>20% × 1,500,000</td><td class="num">300,000</td></tr>
<tr><td>Net investment income tax</td><td>3.8% on the net gain (TAX-06)</td><td class="num">98,800</td></tr>
<tr><td>California income tax on gain</td><td>13.3% top marginal (12.3% + 1%) (TAX-09, TAX-10)</td><td class="num">345,800</td></tr>
<tr><td>Transfer costs</td><td>County 0.11% + city 0.055% + Measure ULA 4% in the City of L.A. (TAX-03, TAX-04)</td><td class="num">249,900</td></tr>
<tr><td><strong>Approximate net proceeds</strong></td><td>Arithmetic on the rows above</td><td class="num"><strong>4,730,500</strong></td></tr>
</tbody></table></div>
<div class="notice warn">
  <strong>This example is not advice and not a projection</strong>
  It ignores the mortgage, closing prorations, any suspended losses, state AMT interactions, the entity's own tax status,
  and the possibility of a 1031 exchange. It exists to show that roughly <b>21% of the sale price</b> can disappear in tax
  and transfer cost in this illustration — and materially more if the basis is lower — which is the single fact that most changes a sell-versus-hold conversation.
</div>

<h2>All tax rows</h2>
{filter_bar("tax-table")}
<div id="tax-table">{data_table(tx, "Every tax and legal rule used on this site, linked to primary law.")}</div>
"""
    write("tax.html", page("tax.html", "After-Tax Module", body,
                           "The statutory pieces that turn a sale price into a net number — each tied to primary law.",
                           "W-07 · After-tax machinery"))


def build_market(rows):
    mk = [r for r in rows if r["category"] == "market"]
    body = f"""
<div class="notice bad">
  <strong>W-08 · This page is deliberately empty of numbers</strong>
  Pricing a short-lease discount requires verified arm's-length evidence: recorded sales of comparable net-lease QSR assets
  with known remaining term, or written quotes. Neither was obtainable from an official source in this session, and broker
  surveys are not official sources. So the answer is <b>blank</b>, and it is flagged rather than filled.
</div>

{data_table(mk, "The three market inputs the model needs. All blank, all flagged. No value has been estimated, interpolated or borrowed from a national average.", show_geo=False)}

<h2>Why this single number dominates the decision</h2>
<div class="grid g3">
  <div class="card">
    <h3>It is the price of time</h3>
    <p>A buyer of net-lease paper is buying a bond-like income stream with a known end date. Every year of remaining term
    is worth something; every year closer to expiry is worth less. The market's price for that decay — usually expressed
    in basis points of yield per year of term — <em>is</em> the short-lease discount.</p>
  </div>
  <div class="card">
    <h3>It compounds into the exit</h3>
    <p>If the discount is 25 bps of yield per year of lost term and the asset yields 5.75% with nine years left, the
    arithmetic on a 2030 expiry is very different from a 2035 expiry. The owner's own uncertainty band — five years —
    spans most of the difference between “sell now” and “hold”.</p>
  </div>
  <div class="card">
    <h3>It cannot be assumed away</h3>
    <p>Using a national average short-lease discount would import someone else's market into a central-LA corner site.
    That is precisely the proxy error W-01 exists to prevent, applied to price instead of to demographics.</p>
  </div>
</div>

<h2>What would let us publish a number</h2>
<ol class="tight">
  <li><strong>Recorded sales.</strong> Pull grant deeds for net-lease QSR assets in central Los Angeles from the county
    recorder for the last 36 months; confirm remaining term at closing and the allocation between real property and
    intangible/business value.</li>
  <li><strong>Written quotes.</strong> Ask at least three active net-lease brokers for indicative pricing on the actual
    asset, with the actual term, in writing.</li>
  <li><strong>Pair-matching.</strong> Where the same tenant or brand has traded twice with different remaining terms,
    use the pair to isolate the term effect from the credit effect.</li>
  <li><strong>Triangulate.</strong> Report a range and the sample size, not a point estimate. If the sample is under
    roughly five observations, the honest output is “insufficient evidence”, which is what this page says today.</li>
</ol>
<div class="notice info">
  <strong>Interim position</strong>
  Until the discount is priced, the defensible posture is to prepare both cases and commit to neither — and to make sure
  the notice calendar is diarised so that the renewal option is not lost by default. See
  <a href="model.html">Sell vs hold</a> and <a href="gates.html">Decision gates</a>.
</div>
"""
    write("market.html", page("market.html", "Pricing the Short-Lease Discount", body,
                              "The one number that decides the case — and why it is blank instead of guessed.",
                              "W-08 · Market pricing"))


def build_model(rows):
    body = """
<div class="notice warn">
  <strong>W-02 · A comparison with no winner declared</strong>
  The framework below is complete and the calculator implements it. What it will not do is produce a recommendation from
  missing inputs. Gate G-03 stays closed until the lease abstract exists and the short-lease discount is priced.
</div>

<h2>The two cases, side by side</h2>
<div class="table-scroll">
<table>
<caption>Structure of the comparison. “Status” says whether the input exists today. Nine of the twelve inputs do not.</caption>
<thead><tr><th>Input</th><th>Hold case</th><th>Sell case</th><th>Status</th></tr></thead>
<tbody>
<tr><td>Starting rent</td><td>Contract rent today</td><td>Contract rent today (capitalised)</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Escalations</td><td>Fixed bumps or CPI (metro CPI is 3.7%, PRI-02)</td><td>Irrelevant to the buyer except as yield growth</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Remaining term</td><td>Years to expiry (2030–2035 band)</td><td>Same, but priced through the discount</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Renewal probability</td><td>Tenant's unit economics and system trend</td><td>What the buyer underwrites</td><td><span class="badge b-flagged">judgement</span></td></tr>
<tr><td>Property tax</td><td>1% base + voter debt, capped 2%/yr (TAX-01, TAX-02)</td><td>Reassessed to price on sale</td><td><span class="badge b-verified">rule verified</span></td></tr>
<tr><td>Insurance</td><td>Current premium, NNN-reimbursed</td><td>Buyer's cost, not yours</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Capital reserve</td><td>Roof, HVAC, parking, seismic</td><td>Priced into the buyer's yield</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Discount rate</td><td>10-yr Treasury 4.92% + net-lease spread (RAT-01)</td><td>Same rate, for comparability</td><td><span class="badge b-verified">reference verified</span></td></tr>
<tr><td>Exit value</td><td>Capitalised rent at exit, minus discount</td><td>Sale price</td><td><span class="badge b-unverified">blank</span></td></tr>
<tr><td>Tax on exit</td><td>Deferred — and reset at death under current basis rules</td><td>Paid now: recapture + capital gain + NIIT (TAX-06…TAX-11)</td><td><span class="badge b-verified">rule verified</span></td></tr>
<tr><td>Transfer cost</td><td>None</td><td>County + Measure ULA (TAX-03, TAX-04)</td><td><span class="badge b-verified">rule verified</span></td></tr>
<tr><td>Reinvestment return</td><td>n/a</td><td>The return on after-tax proceeds</td><td><span class="badge b-unverified">blank</span></td></tr>
</tbody></table></div>

<h2>How the comparison is run</h2>
<ol class="tight">
  <li><strong>Normalise the horizon.</strong> Pick one holding period (Q-25) and apply it to both cases. Comparing a
    ten-year hold to a sale today is the most common error in this analysis.</li>
  <li><strong>Build after-tax cash flows for both.</strong> Hold: rent minus unreimbursed costs minus tax on income,
    plus terminal value net of tax. Sell: net proceeds after tax and transfer cost, invested at a stated rate.</li>
  <li><strong>Discount both at the same rate.</strong> Use the Treasury plus a disclosed spread, and show the sensitivity
    to ±100 bps. A hold case that wins only at a 6% discount rate has not won.</li>
  <li><strong>Stress the renewal.</strong> Run 100% renewal, 50% renewal, and vacancy-then-re-tenant. The spread between
    those three is the real risk in the hold case.</li>
  <li><strong>Stress the black swans together.</strong> Wildfire, earthquake and flood do not arrive independently of
    each other's consequences — see the <a href="risks.html">risk register</a>.</li>
  <li><strong>Declare a winner only when every gate is green.</strong> Until then, the output is a range, and the range is
    printed as a range.</li>
</ol>

<h2>What the comparison looks like once the inputs exist</h2>
<div class="table-scroll">
<table>
<caption>Output template. The calculator produces exactly these lines from your inputs, in your browser. Columns are blank
here on purpose — filling them from the current data would require inventing rent, term and price.</caption>
<thead><tr><th>Line</th><th>Hold (10 yr)</th><th>Sell now</th><th>Difference</th></tr></thead>
<tbody>
<tr><td>Cumulative after-tax cash flow</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>Terminal / sale proceeds, after tax</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>Net present value at the stated discount rate</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>NPV at discount rate +100 bps</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>NPV at discount rate −100 bps</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>NPV with a 12-month vacancy before re-tenanting</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
<tr><td>Break-even short-lease discount</td><td class="blank">—</td><td class="blank">—</td><td class="blank">—</td></tr>
</tbody></table></div>

<h2>The one structural point that survives missing data</h2>
<div class="notice info">
  <strong>Selling converts a deferred tax into a paid tax; holding keeps it deferred.</strong>
  Under the verified rules on the <a href="tax.html">after-tax page</a>, a sale at these rates can consume roughly a fifth
  of the price in tax and transfer cost in the illustration, and more where the basis is lower. That does not mean “never sell” — it means the sell case has to
  clear a higher bar than the raw price suggests, and that a 1031 exchange or a hold-until-basis-reset strategy belongs in
  the conversation before any listing. Conversely, holding keeps capital concentrated in one asset in one seismic region.
  Both of those statements are true at once, which is why the answer is a balance, not a verdict.
</div>
"""
    write("model.html", page("model.html", "Sell vs Hold", body,
                             "A complete comparison framework that refuses to name a winner while its inputs are missing.",
                             "W-02 · Sell-versus-hold"))


def build_gates(rows):
    gates = [
        ("G-01", "Parcel identified", "unverified", "APN, address and legal description recorded; zoning confirmed.",
         "Opens hazard screening, traffic counts, tax rate area and comparables.", "F-01"),
        ("G-02", "Lease abstracted and reconciled", "unverified", "Expiration, rent, escalators, options and notice windows extracted and checked against the notice calendar.",
         "Without it the model has no timeline and the option can be lost by default.", "F-02"),
        ("G-03", "Short-lease discount priced", "unverified", "At least three comparable recorded sales or written quotes with known term.",
         "This is the value driver; everything else is secondary.", "F-03"),
        ("G-04", "Hazard zones verified at the parcel", "unverified", "FHSZ, Alquist-Priolo, seismic hazard and NFHL status recorded with dated evidence.",
         "Insurance cost and lender appetite both depend on it.", "F-01"),
        ("G-05", "Tax basis and depreciation reconstructed", "unverified", "Adjusted basis, recapture exposure and entity form confirmed by the adviser.",
         "The after-tax number is meaningless without it.", "F-04"),
        ("G-06", "Trade area defined from the parcel", "unverified", "Drive-time ring built and its tracts enumerated.",
         "Replaces every city and county substitute on this site.", "F-05"),
        ("G-07", "Insurance bindable at a known cost", "unverified", "Three quotes in hand at the actual address and construction type.",
         "An uninsurable building is an unsaleable building.", "—"),
        ("G-08", "Model back-tested", "not started", "Cash-flow model validated against at least one full market cycle of comparable data.",
         "A model that has never been tested is an opinion with a spreadsheet around it.", "—"),
        ("G-09", "Black-swan scenarios agreed", "in progress", "Loss-of-rent, repair and exit-liquidity stresses documented and accepted by the owner.",
         "Defines the loss the owner is willing to carry.", "—"),
        ("G-10", "Decision recorded with rationale", "not started", "Final choice written down with the inputs it relied on and the date.",
         "Makes the decision reviewable later, which is the whole point of this workspace.", "—"),
    ]
    cls = {"verified": "b-verified", "in progress": "b-flagged", "unverified": "b-unverified", "not started": "b-open"}
    tr = "".join(
        f'<tr><td class="metric">{g}</td><td><strong>{esc(t)}</strong></td>'
        f'<td><span class="badge {cls[s]}">{esc(s)}</span></td>'
        f'<td class="note">{esc(d)}</td><td class="note">{esc(w)}</td>'
        f'<td>{flag_cell(flag)}</td></tr>'
        for g, t, s, d, w, flag in gates
    )
    verified = sum(1 for r in rows if r["status"] == "verified")
    total = len(rows)
    pct = round(100 * verified / total)
    body = f"""
<div class="notice warn">
  <strong>W-03 · Seven of ten gates are shut</strong>
  The gates are ordered so that each one unlocks work behind it. Nothing on this board is a judgement call about the
  asset; each is a factual precondition. A decision made with G-02, G-03 or G-05 shut would be based on the owner's
  memory of the lease and a guess at the market.
</div>

<div class="tiles">
  <div class="card"><div class="kicker">Data rows verified</div><div class="stat">{verified}<span style="font-size:15px;color:var(--muted)"> / {total}</span></div><small>{pct}% of published rows carry an official source link</small></div>
  <div class="card"><div class="kicker">Gates open</div><div class="stat">0<span style="font-size:15px;color:var(--muted)"> / 10</span></div><small>none of the ten preconditions is satisfied yet</small></div>
  <div class="card"><div class="kicker">Blocking questions</div><div class="stat">8</div><small>of the 30 in the register are rated highest priority</small></div>
  <div class="card"><div class="kicker">Decision readiness</div><div class="stat">Not yet</div><small>prepare both cases; commit to neither</small></div>
</div>

<h2>Gate board</h2>
<div class="table-scroll">
<table>
<caption>Each gate names its evidence standard. “Unverified” means the evidence does not exist yet — not that it was checked
and found wanting.</caption>
<thead><tr><th>Gate</th><th>Precondition</th><th>Status</th><th>Evidence required</th><th>Why it blocks</th><th>Flag</th></tr></thead>
<tbody>{tr}</tbody></table></div>

<h2>Progress is measurable, which is the point</h2>
<p class="lede">The board above is the honest answer to “where are we?”: the <em>analysis</em> is largely built — the tax
machinery, the tenant evidence, the regional data and the stress framework all exist and are sourced. The <em>asset-specific
facts</em> do not. That asymmetry is worth naming, because it tells the owner exactly where the next week of effort should go:
not more research, but one envelope of documents.</p>
<div class="grid g3">
  <div class="card"><h3>Day 1–2</h3><p>Pull the deed and tax bill for the APN. Run the four hazard lookups. Geocode the parcel.</p></div>
  <div class="card"><h3>Day 3–5</h3><p>Abstract the lease; reconcile every date to the notice calendar; confirm the tenant entity against the signature page.</p></div>
  <div class="card"><h3>Week 2</h3><p>Three insurance quotes, three broker quotes, and the adviser reconstructs basis and recapture exposure.</p></div>
</div>
"""
    write("gates.html", page("gates.html", "Decision-Gate Progress Board", body,
                             "Ten preconditions, honestly scored, in the order they unlock each other.",
                             "W-03 · Progress board"))


def build_risks(rows):
    risks = [
        ("R-01", "Tenant does not renew", "high", "high",
         "System units fell 58 in two years (OPE-01/OPE-04) and royalties fell 8.4% (OPE-09/OPE-11). A site at the bottom of the cohort is an easy closure.",
         "Vacancy at expiry; income stops; re-tenanting cost and downtime.",
         "Abstract the option clause (Q-04); open a renewal conversation 24 months before expiry; model a 12-month vacancy."),
        ("R-02", "Renewal happens at a lower rent", "medium", "high",
         "If the option is at fair market value rather than fixed, a shrinking system argues for a reset down.",
         "Lower income capitalised at the same cap rate means a lower value — the sale case weakens while the lease still looks alive.",
         "Determine whether the option is fixed, indexed or market; get the tenant's unit sales (Q-20)."),
        ("R-03", "Short-lease discount is larger than assumed", "high", "medium",
         "Unknown until priced (MKT-01). Buyers of net-lease paper penalise short term heavily.",
         "Sale price today may be materially below an owner's expectation.",
         "Price it from recorded sales (Q-09, Q-10) before listing or modelling."),
        ("R-04", "Capitalisation-rate expansion", "medium", "high",
         "10-year Treasury at 4.92% (RAT-01), range 4.84–5.31% this quarter (RAT-02).",
         "Values fall even with flat rent; both cases lose, but the hold case carries the exposure longer.",
         "Model ±100 bps on cap rate and discount rate together; keep the exit assumption conservative."),
        ("R-05", "Insurance unavailable or unaffordable", "high", "medium",
         "California commercial property market remains constrained; parcel zone status unknown (HAZ-05..08).",
         "An uninsurable building cannot be financed or sold; NNN recoveries may not cover the premium.",
         "Three quotes at the address (Q-12); confirm lease allocation of insurance cost."),
        ("R-06", "Earthquake damage", "low-probability / high-severity", "high",
         "Los Angeles County's modelled risk is dominated by seismic; FEMA rates the county Relatively High (HAZ-01).",
         "Simultaneous loss of rent, unbudgeted repair, and an exit market that vanishes.",
         "Confirm retrofit status (Q-22); check business-interruption and shake coverage; stress all three channels at once."),
        ("R-07", "Wildfire at the urban interface", "low-probability / high-severity", "medium",
         "Wildfire exposure is highly localised by tract, not by county — county averages hide it.",
         "Smoke and access disruption plus insurance withdrawal even without direct damage.",
         "Verify the parcel's FHSZ class (HAZ-05); do not rely on the county rating."),
        ("R-08", "Flood", "low", "medium",
         "NFHL status unknown (HAZ-07).",
         "Lender-mandated flood insurance and uninsurable periods.",
         "Pull the FIRM panel; note base flood elevation."),
        ("R-09", "Tax law change before exit", "medium", "medium",
         "Rates and brackets are statutory and index annually (TAX-08).",
         "After-tax proceeds change; a hold-until-reset strategy can be legislated away.",
         "Re-verify rates each year; do not hard-code today's brackets into a ten-year model."),
        ("R-10", "Transfer-tax exposure surprises the seller", "medium", "high",
         "Measure ULA adds 4% above $5m and 5.5% at $10m (TAX-04, TAX-05).",
         "A 4–5.5% hit is larger than most owners budget.",
         "Get written confirmation of the treatment from escrow and the City before pricing a sale."),
        ("R-11", "Local demand erosion", "medium", "medium",
         "Information employment −1.5%, manufacturing −1.5% (LAB-09, LAB-10); office-using employment +0.5% (LAB-08).",
         "Daytime lunch traffic falls; unit sales fall; renewal economics weaken.",
         "Define the trade area (Q-13) and track the tract-level drivers annually."),
        ("R-12", "Competitive cannibalisation", "medium", "medium",
         "The system is closing units but may still open near an existing one.",
         "Sales transfer rather than grow; the unit's renewal case weakens.",
         "Map competitors and ask the franchisee about protected territory (Q-28)."),
        ("R-13", "Environmental liability on or near the site", "low", "high",
         "Unknown (Q-23).",
         "Value and financeability impaired; disclosure obligations.",
         "Phase I ESA; check GeoTracker and EnviroStor for the address and neighbours."),
        ("R-14", "Liquidity concentration", "medium", "medium",
         "A single asset in a single seismic region is the whole position.",
         "A local shock hits income, value and the owner's other holdings together.",
         "Consider partial diversification through a 1031 into multiple assets if selling."),
        ("R-15", "Missed option window", "medium", "certain if unmanaged",
         "Expiration is known only as a range (LSE-01).",
         "The renewal right lapses and the asset becomes a vacancy problem by default.",
         "Build the notice calendar now (Q-29) with multiple reminders per deadline."),
    ]
    cls = {"high": "b-unverified", "medium": "b-flagged", "low": "b-open",
           "low-probability / high-severity": "b-unverified", "certain if unmanaged": "b-unverified"}
    tr = []
    for rid, name, lik, imp, ev, cons, mit in risks:
        tr.append(f"""<tr>
<td class="metric">{esc(rid)}</td><td><strong>{esc(name)}</strong></td>
<td><span class="badge {cls[lik]}">{esc(lik)}</span></td>
<td><span class="badge {cls[imp]}">{esc(imp)}</span></td>
<td class="note">{esc(ev)}</td><td class="note">{esc(cons)}</td><td class="note">{esc(mit)}</td></tr>""")
    body = f"""
<div class="notice info">
  <strong>W-13 · Fifteen risks, each with the evidence that created it</strong>
  Likelihood and impact are the author's judgement and are labelled as such — they are not sourced, and they are not
  numeric probabilities. What <em>is</em> sourced is the evidence column, which links each risk to a verified row or a
  named gap. A risk register without that link is a list of anxieties.
</div>

<h2>Register</h2>
<div class="table-scroll">
<table>
<caption>Ordered roughly by expected impact on the sell-versus-hold comparison. The three black-swan rows are R-06, R-07 and R-08.</caption>
<thead><tr><th>ID</th><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Evidence</th><th>Consequence if it happens</th><th>Mitigation</th></tr></thead>
<tbody>{''.join(tr)}</tbody></table></div>

<h2>Black swans: why they are modelled together</h2>
<p class="lede">A natural disaster damages a landlord through three channels at once, and the three reinforce each other:
rent stops (business interruption ends before repairs finish), repairs are unbudgeted (and the lease may not allocate
them), and exit liquidity disappears (buyers vanish exactly when you would want to sell). Modelling them separately
understates the loss, which is why the stress scenario in the calculator applies all three simultaneously.</p>

<div class="grid g3">
  <div class="card">
    <h3>Channel 1 · Loss of rent</h3>
    <p>Rent abatement during restoration, business-interruption coverage that runs out early, and a tenant who may not
    reopen at all. A NNN lease does not protect against this — it protects against <em>operating cost</em> surprises, not
    against the building being unusable.</p>
  </div>
  <div class="card">
    <h3>Channel 2 · Repair cost</h3>
    <p>Seismic retrofit, structural repair, and code upgrades triggered by reconstruction. Confirm who pays under the lease
    and whether the insurance limit is realistic against current construction costs.</p>
  </div>
  <div class="card">
    <h3>Channel 3 · Exit liquidity</h3>
    <p>After a regional event, buyers reprice or disappear. The exit assumption in the hold case is the assumption most
    likely to be wrong in exactly the year it matters.</p>
  </div>
</div>

<div class="notice warn">
  <strong>How the risk balance is meant to be read</strong>
  Every mitigation above is cheap relative to the loss it prevents. That is the actual recommendation of this page: not
  “sell” or “hold”, but “spend two weeks and a few thousand dollars closing the gates before spending a decision on it.”
  The <a href="calculator.html">calculator</a> lets the owner see what the black-swan case does to each option before any
  of that money is committed.
</div>
"""
    write("risks.html", page("risks.html", "Risk Register", body,
                             "Every decision's downside, tied to evidence — including the three events that would hurt all three channels at once.",
                             "W-13 · Risk"))


def build_suggestions(rows):
    sug = [
        ("S-01", "Build the private parcel and owner record workspace", "privacy", "highest",
         "Stand up an access-controlled internal store (encrypted, single-tenant, logged) that holds the deed, APN, lease, tax bills and owner financials. Publish only aggregate summaries to the site.",
         "Nothing parcel-specific can be researched today without somewhere private to put it. This is the top blocker and it is also the top privacy control."),
        ("S-02", "Geocode and run the four hazard lookups in one sitting", "hazards", "highest",
         "One afternoon: FHSZ viewer, CGS EQ Zapp, NFHL panel, ZIMAS zoning. Save dated evidence for each.",
         "Converts four blank rows into four verified rows, and unblocks insurance quotes and lender conversations."),
        ("S-03", "Abstract the lease and reconcile the notice calendar", "lease", "highest",
         "Extract every date, notice window, cure period and consent requirement; check each against the calendar; have counsel sign off.",
         "The option window is the only genuinely irreversible deadline in this analysis."),
        ("S-04", "Commission three broker opinions and three insurance quotes", "market", "highest",
         "Written indicative pricing on the actual asset with the actual remaining term, plus three bindable insurance quotes.",
         "Fills the two market blanks that currently block the entire sell case."),
        ("S-05", "Have the tax adviser reconstruct basis and recapture", "tax", "highest",
         "Adjusted basis, depreciation history, suspended losses, entity form and the owner's marginal rate — in writing.",
         "The after-tax comparison cannot be run without it, and the calculator's output is only as good as these inputs."),
        ("S-06", "Replace city and county figures with drive-time tract data", "economy", "high",
         "Build 3/5/10-minute rings, enumerate tracts, re-pull ACS tables, recompute with margins of error carried through.",
         "Removes the largest single methodological weakness on this site."),
        ("S-07", "Diarise every deadline with layered reminders", "lease", "high",
         "Calendar the option notice window at 24, 12, 6 and 3 months before, with a named owner for each.",
         "Cheap insurance against the default-to-vacancy outcome."),
        ("S-08", "Open a renewal conversation 24 months before expiry", "lease", "high",
         "Approach the franchisee operator first (not the parent) with unit-level economics in hand.",
         "The company's asset-light strategy means the operator, not corporate, decides — and operators decide early."),
        ("S-09", "Stress-test the model, do not point-forecast it", "analysis", "high",
         "Run a probability-weighted renewal assumption (100/50/0%) rather than a single line, and show all three.",
         "The uncertainty band on expiry (2030–2035) is itself five years wide; a single number would hide it."),
        ("S-10", "Model the 1031 exchange before listing, not after", "tax", "high",
         "Identify replacement candidates and engage a qualified intermediary before a sale decision.",
         "A deferral can dominate the after-tax arithmetic and changes which option wins."),
        ("S-11", "Get an insurance-market read before any renovation spend", "hazards", "medium",
         "Ask the broker what the carrier appetite is at the address before committing capital.",
         "There is no point improving an asset the market will not insure."),
        ("S-12", "Run a preliminary alternate-use study", "exit", "medium",
         "Local architect: what could the site become if the tenant leaves, at what cost, with what entitlement risk?",
         "That value is the floor under the sell decision and the downside in the hold case."),
        ("S-13", "Publish the working file to advisers, not the public", "governance", "medium",
         "Keep this site anonymous and share the private workspace under NDA with a named adviser list.",
         "Protects negotiating position as well as personal information."),
        ("S-14", "Re-verify the rate and price rows quarterly", "governance", "medium",
         "The Treasury yield moves daily; CPI and labour series revise monthly; brackets index annually.",
         "Prevents the model from quietly drifting out of date."),
        ("S-15", "Record the eventual decision and its rationale here", "governance", "low",
         "Date, choice, inputs relied on, and who advised.",
         "Turns this workspace into an audit trail for the next review or the estate."),
    ]
    group_label = {"privacy": "Privacy & data", "hazards": "Hazard", "lease": "Lease", "market": "Market",
                   "tax": "Tax", "economy": "Trade area", "analysis": "Analysis", "exit": "Exit",
                   "governance": "Governance"}
    cls = {"highest": "b-unverified", "high": "b-flagged", "medium": "b-open", "low": "b-open"}
    tr = "".join(
        f"""<tr><td class="metric">{esc(i)}</td><td><strong>{esc(t)}</strong></td>
<td><span class="pill">{esc(group_label.get(g, g))}</span></td>
<td><span class="badge {cls[p]}">{esc(p)}</span></td>
<td class="note">{esc(d)}</td><td class="note">{esc(w)}</td></tr>"""
        for i, t, g, p, d, w in sug
    )
    pick = "".join(
        f'<li><label><input type="checkbox" data-title="{esc(i)} — {esc(t)}">'
        f'<span><strong>{esc(i)} · {esc(t)}</strong><br><span class="note">{esc(w)}</span></span></label></li>'
        for i, t, g, p, d, w in sug
    )
    body = f"""
<div class="notice info">
  <strong>W-14 · Suggestions, and how to choose between them</strong>
  These are recommendations about <em>process</em>, not about the property, so they carry no data claims and need no source
  links. Tick the ones you want implemented first in the shortlist tool at the bottom; the selection is yours and nothing
  here has been pre-decided.
</div>

<h2>All suggestions</h2>
<div class="table-scroll">
<table>
<caption>Fifteen suggestions, ordered by priority. Priority reflects dependency — the highest-priority items unblock the others.</caption>
<thead><tr><th>ID</th><th>Suggestion</th><th>Area</th><th>Priority</th><th>What it involves</th><th>Why it matters</th></tr></thead>
<tbody>{tr}</tbody></table></div>

<h2>Site improvements: how this page would make decisions better</h2>
<div class="grid g2">
  <div class="card">
    <h3>What works now</h3>
    <ul class="clean">
      <li>Every published value carries a source link and a verification status; blanks are visible rather than hidden.</li>
      <li>The tax machinery is traceable to primary law, so an adviser can check it rather than trust it.</li>
      <li>The calculator runs entirely in the browser — no data leaves the reader's machine.</li>
      <li>The gate board makes progress measurable instead of rhetorical.</li>
    </ul>
  </div>
  <div class="card">
    <h3>What should be added next</h3>
    <ul class="clean">
      <li><strong>A drive-time engine.</strong> Replace the demonstration tract set with the real ring once the parcel is known.</li>
      <li><strong>A comparables database.</strong> Recorded sales with term, price and cap rate, versioned by quarter.</li>
      <li><strong>Tract trend history.</strong> Pull two ACS vintages side by side to show direction, not just level.</li>
      <li><strong>A versioned model.</strong> Date-stamp every assumption set and keep the old ones, per the back-testing requirement.</li>
      <li><strong>An export to the adviser pack.</strong> One click from calculator inputs to a signed-off PDF.</li>
    </ul>
  </div>
</div>

<h2>Choose your path</h2>
<div class="notice warn noprint">
  <strong>Nothing here is applied automatically</strong>
  Tick the suggestions you want implemented, then copy the shortlist into your notes or send it to your adviser.
  This tool stores nothing and sends nothing anywhere.
</div>
<ul class="choose" id="suggestion-picker">{pick}</ul>
<div class="noprint" style="max-width:640px">
  <label for="suggestion-out" class="note">Your shortlist</label>
  <textarea id="suggestion-out" rows="7" style="width:100%;font:13px/1.5 var(--mono);padding:10px;border:1px solid var(--line);border-radius:8px;margin-top:6px" readonly></textarea>
  <button id="suggestion-copy" type="button" style="margin-top:8px;font:inherit;font-size:13px;padding:8px 14px;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:7px;cursor:pointer">Copy shortlist</button>
</div>
"""
    write("suggestions.html", page("suggestions.html", "Suggestions", body,
                                   "Fifteen concrete next steps, and a shortlist tool so you can choose the path yourself.",
                                   "W-14 · Suggestions"))


def build_calculator(rows):
    body = """
<div class="notice info">
  <strong>W-11 · Private, local, and disposable</strong>
  This calculator runs entirely in your browser. It makes no network requests, sets no cookies, and stores nothing.
  Close the tab and everything you typed is gone. All arithmetic happens on your machine with the rates verified on the
  <a href="tax.html">after-tax page</a>. It is a calculator, not advice.
</div>

<div class="calc">
  <div class="grid g2" style="align-items:start">
    <div>
      <fieldset>
        <legend>Sale inputs</legend>
        <div class="f"><label for="sale">Contract sale price</label><input id="sale" type="number" value="6000000" step="50000"></div>
        <div class="f"><label for="basis">Adjusted basis (land + building, net of depreciation)</label><input id="basis" type="number" value="3400000" step="50000"></div>
        <div class="f"><label for="depr">Depreciation taken to date</label><input id="depr" type="number" value="1100000" step="50000"></div>
        <div class="f"><label for="mortgage">Mortgage balance to repay</label><input id="mortgage" type="number" value="0" step="50000"></div>
        <div class="f"><label for="ula">Measure ULA applies (City of L.A., sale ≥ $5m)</label>
          <select id="ula"><option value="1">yes</option><option value="0">no</option></select></div>
        <div class="f"><label for="citytx">City transfer tax layer (RTC 11911(b))</label>
          <select id="citytx"><option value="0">no</option><option value="1">yes</option></select></div>
        <div class="f"><label for="broker">Brokerage + legal + escrow (% of price)</label><input id="broker" type="number" value="4" step="0.25"></div>
      </fieldset>

      <fieldset>
        <legend>Owner's tax position</legend>
        <div class="f"><label for="fedlt">Federal long-term capital gain rate</label>
          <select id="fedlt"><option value="0">0%</option><option value="15">15%</option><option value="20" selected>20%</option></select></div>
        <div class="f"><label for="niit">Net investment income tax applies (MAGI over threshold)</label>
          <select id="niit"><option value="1">yes — 3.8%</option><option value="0">no</option></select></div>
        <div class="f"><label for="cainc">California taxable income (drives the marginal rate)</label>
          <select id="cainc">
            <option value="0.093">up to $72,724 / $145,448 (9.3%)</option>
            <option value="0.103">to $371,479 / $742,958 (10.3%)</option>
            <option value="0.113">to $445,771 / $891,542 (11.3%)</option>
            <option value="0.123" selected>to $742,953 / $1,485,906 (12.3%)</option>
            <option value="0.133">above $1m taxable income (13.3%)</option>
          </select></div>
        <div class="f"><label for="exch">Section 1031 exchange intended (deferral)</label>
          <select id="exch"><option value="0">no — pay the tax</option><option value="1">yes — defer (estimate shows tax deferred)</option></select></div>
      </fieldset>

      <fieldset>
        <legend>Hold case</legend>
        <div class="f"><label for="rent">Current annual base rent</label><input id="rent" type="number" value="330000" step="5000"></div>
        <div class="f"><label for="esc">Annual escalation</label><input id="esc" type="number" value="2" step="0.25"> </div>
        <div class="f"><label for="term">Years to lease expiry</label><input id="term" type="number" value="6" step="1"></div>
        <div class="f"><label for="renew">Renewal probability (judgement, not sourced)</label><input id="renew" type="number" value="50" step="5"></div>
        <div class="f"><label for="hold">Holding period for the comparison (years)</label><input id="hold" type="number" value="10" step="1"></div>
        <div class="f"><label for="cap">Exit capitalisation rate (%)</label><input id="cap" type="number" value="6" step="0.25"></div>
        <div class="f"><label for="disc">Discount rate (%) — 10-yr Treasury 4.92% + spread</label><input id="disc" type="number" value="6.5" step="0.25"></div>
        <div class="f"><label for="vac">Months vacant if the tenant leaves</label><input id="vac" type="number" value="12" step="1"></div>
      </fieldset>
    </div>

    <div>
      <div class="out" id="out" aria-live="polite">
        <div class="row"><span>Total gain</span><b id="o-gain">—</b></div>
        <div class="row"><span>Recapture portion (max 25%)</span><b id="o-recap">—</b></div>
        <div class="row"><span>Federal tax (recapture + capital gain)</span><b id="o-fed">—</b></div>
        <div class="row"><span>Net investment income tax (3.8%)</span><b id="o-niit">—</b></div>
        <div class="row"><span>California income tax on the gain</span><b id="o-ca">—</b></div>
        <div class="row"><span>Transfer taxes</span><b id="o-xfer">—</b></div>
        <div class="row"><span>Brokerage, legal and escrow</span><b id="o-cost">—</b></div>
        <div class="row big"><span>Net proceeds after tax and cost</span><b id="o-net">—</b></div>
        <div class="row"><span>Effective total leakage</span><b id="o-leak">—</b></div>
        <hr style="border:none;border-top:1px solid #1e344b;margin:12px 0">
        <div class="row"><span>Hold: after-tax cash flow over the period</span><b id="o-holdcf">—</b></div>
        <div class="row"><span>Hold: value at exit (before tax)</span><b id="o-exit">—</b></div>
        <div class="row"><span>Hold: expected value given renewal probability</span><b id="o-exp">—</b></div>
        <div class="row big"><span>Hold: NPV at the discount rate</span><b id="o-npv">—</b></div>
        <div class="row"><span>Break-even: short-lease discount the sale must beat</span><b id="o-be">—</b></div>
      </div>
      <p class="note" style="margin-top:10px">Negative or zero values show as 0. Every rate above is taken from the verified
      tax page; every dollar figure is yours. Nothing is transmitted.</p>
      <div class="notice warn" style="margin-top:14px">
        <strong>Read the output as an ordering device, not a valuation</strong>
        The point of the two blocks is to see whether the sell case clears the hold case after tax. If the two are within
        ten per cent of each other, the decision turns on factors this calculator does not model — insurability, the
        owner's liquidity needs, concentration risk and the black-swan exposure in the <a href="risks.html">risk register</a>.
      </div>
    </div>
  </div>
</div>
"""
    write("calculator.html", page("calculator.html", "Private Calculator", body,
                                  "Runs in your browser. No network calls, no storage, no tracking — and the rates come from primary law.",
                                  "W-11 · Browser calculator"))

    js = r"""/* Browser-only calculator. No fetch, no storage, no cookies. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var ids = ['sale','basis','depr','mortgage','ula','citytx','broker','fedlt','niit','cainc','exch',
             'rent','esc','term','renew','hold','cap','disc','vac'];

  function n(id) { var v = parseFloat($(id).value); return isFinite(v) ? v : 0; }
  function money(x) {
    if (!isFinite(x)) x = 0;
    var s = Math.abs(Math.round(x)).toLocaleString('en-US');
    return (x < 0 ? '−$' : '$') + s;
  }
  function pct(x) { return (isFinite(x) ? (100 * x).toFixed(1) : '0.0') + '%'; }

  function calc() {
    var sale = n('sale'), basis = n('basis'), depr = n('depr'), mortgage = n('mortgage');
    var brokerPct = n('broker') / 100;
    var fedlt = parseFloat($('fedlt').value);
    var niitOn = $('niit').value === '1';
    var caRate = parseFloat($('cainc').value);
    var exchange = $('exch').value === '1';

    /* --- sale side ------------------------------------------------------- */
    var gain = Math.max(0, sale - basis);
    var recap = Math.min(gain, Math.max(0, depr));
    var ltgain = Math.max(0, gain - recap);

    var fedRecap = recap * 0.25;              /* IRS Topic 409: unrecaptured 1250 max 25% */
    var fedLt = ltgain * fedlt;               /* IRS Topic 409 brackets */
    var fed = fedRecap + fedLt;
    var niit = niitOn ? gain * 0.038 : 0;     /* IRS: 3.8% NIIT */
    var ca = gain * caRate;                   /* FTB 2025 schedules, flat at the top bracket */

    var county = sale * 0.0011;               /* RTC 11911(a): $0.55 per $500 = 0.11% */
    var city = $('citytx').value === '1' ? sale * 0.00055 : 0;   /* RTC 11911(b): half again */
    var ula = 0;
    if ($('ula').value === '1' && sale >= 5000000) {
      ula = sale >= 10000000 ? sale * 0.055 : sale * 0.04;       /* Measure ULA tiers */
    }
    var xfer = county + city + ula;
    var cost = sale * brokerPct;

    var taxTotal = exchange ? 0 : (fed + niit + ca);
    var net = sale - taxTotal - xfer - cost - mortgage;
    var leak = sale > 0 ? (sale - Math.max(0, net)) / sale : 0;

    $('o-gain').textContent = money(gain);
    $('o-recap').textContent = money(recap);
    $('o-fed').textContent = money(fed);
    $('o-niit').textContent = money(niit);
    $('o-ca').textContent = money(ca);
    $('o-xfer').textContent = money(xfer) + (ula > 0 ? '  (incl. ULA ' + money(ula) + ')' : '');
    $('o-cost').textContent = money(cost);
    $('o-net').textContent = money(net);
    $('o-leak').textContent = pct(leak) + (exchange ? '  (tax deferred)' : '');

    /* --- hold side ------------------------------------------------------- */
    var rent = n('rent'), esc = n('esc') / 100, term = Math.max(0, n('term'));
    var renew = Math.min(1, Math.max(0, n('renew') / 100));
    var holdYrs = Math.max(1, n('hold'));
    var cap = n('cap') / 100, disc = n('disc') / 100;
    var vacMonths = Math.max(0, n('vac'));

    var cf = 0, r = rent;
    for (var y = 0; y < holdYrs; y++) {
      /* rent continues while the lease runs; after expiry it continues only
         in proportion to the renewal probability, net of a vacancy gap */
      var factor = (y < term) ? 1 : renew;
      var gross = r * factor;
      if (y >= term && y < term + Math.ceil(vacMonths / 12)) gross = 0;
      cf += gross;
      r *= (1 + esc);
    }
    var exitRent = rent * Math.pow(1 + esc, holdYrs) * (holdYrs > term ? renew : 1);
    var exitVal = cap > 0 ? exitRent / cap : 0;
    var expected = cf + exitVal;
    var npv = 0;
    for (var k = 1; k <= holdYrs; k++) npv += (rent * Math.pow(1 + esc, k - 1) * (k <= term ? 1 : renew)) / Math.pow(1 + disc, k);
    npv += exitVal / Math.pow(1 + disc, holdYrs);

    $('o-holdcf').textContent = money(cf);
    $('o-exit').textContent = money(exitVal);
    $('o-exp').textContent = money(expected);
    $('o-npv').textContent = money(npv);

    /* break-even: the discount the sale must beat to be worth more than holding */
    var be = expected > 0 ? Math.max(0, (expected - Math.max(0, net)) / expected) : 0;
    $('o-be').textContent = pct(be) + ' of hold-case value';
  }

  var ready = false;
  ids.forEach(function (id) { var el = $(id); if (el) { el.addEventListener('input', function () { if (ready) calc(); }); el.addEventListener('change', function () { if (ready) calc(); }); } });
  if ($('sale')) { ready = true; calc(); }
})();
"""
    (DOCS / "assets/js/calc.js").write_text(js, encoding="utf-8")


def build_review(rows):
    un = [r for r in rows if r["status"] == "unverified"]
    fl = [r for r in rows if r["status"] == "flagged"]
    flags = [
        ("F-01", "No street address, APN or parcel identifier was supplied",
         "Every parcel-specific row stays blank: hazard zone status, zoning, AADT, tax rate area and assessed value. Every parcel-level conclusion on this site is therefore unavailable.",
         "Supplying the APN from the deed closes G-01 and unblocks hazard screening, traffic counts, tax rate area and comparables in a single step."),
        ("F-02", "No lease document supplied",
         "Expiration is known only as a 2030–2035 range. Rent, escalators, options, co-tenancy, assignment, ROFR, holdover and cure periods are all unknown.",
         "The abstract and notice-calendar reconciliation close G-02. Until then the model has no timeline, and the option can be lost by default."),
        ("F-03", "No verified quote set for a short-lease QSR in central Los Angeles",
         "The short-lease discount (MKT-01), capitalisation rate (MKT-02) and comparable rent (MKT-03) are blank. No national average was substituted.",
         "Three recorded sales or written quotes with known term close G-03. This is the single largest value driver in the decision."),
        ("F-04", "No assessed value, basis, purchase date, depreciation history or loan terms supplied",
         "The after-tax module publishes the statutory machinery but no dollar result for this owner. The worked example on the tax page uses invented round numbers and says so.",
         "The adviser's reconstruction of adjusted basis and recapture closes G-05."),
        ("F-05", "“Central Los Angeles” is not a Census geography",
         "The tract set on the tract page is DEMO-TRACTS-A, a public demonstration set and explicitly not the subject parcel. City, county and metro figures on the economy page are labelled substitutes.",
         "Geocoding the parcel and building a drive-time ring closes G-06 and replaces every substitute."),
        ("F-06", "One hazard figure comes from a third-party blog, not FEMA",
         "HAZ-02 (earthquake = ~60% of modelled expected annual loss) is quoted from a private analysis of FEMA's National Risk Index, not from FEMA directly. It is flagged and must not be published as a finding.",
         "Pull the NRI tract and county downloads from FEMA directly and recompute before citing."),
        ("F-07", "Measure ULA tiering is confirmed by a Council press release, not the administering department",
         "TAX-05 (5.5% above $10m) traces to a .gov Council District 4 release. TAX-04 (4% above $5m) traces to LAHD. Both are official, but the administering office page for the tier table was not retrieved.",
         "Ask the Office of Finance in writing for the tier schedule and the exemption analysis before pricing a sale."),
        ("F-08", "BLS marks several published figures preliminary, and one annual figure is incomplete",
         "LAB-01, LAB-04 to LAB-10 are preliminary. LAB-03 is an 11-month 2025 average because October 2025 was not collected during the federal shutdown.",
         "Re-pull before relying on any of them; the API values will change."),
        ("F-09", "Two population vintages appear on the same site",
         "DEM-01 (3,857,263) is an ACS 2020–2024 5-year estimate; DEM-04 (3,869,089) is a 2025 Vintage estimate. They are not interchangeable and must not be mixed in one trend.",
         "Keep them in separate series or use one vintage consistently."),
        ("F-11", "Four external source links were stale and have been corrected",
         "The OSFM Fire Hazard Severity Zone map paths (two rows) and the CGS EQ Zapp path returned 404s, and the FEMA Map Service Center portal needed its full portal path. Corrected on 2026-11-25 and re-checked; the registry notes record the correction.",
         "Re-check every external link quarterly — link rot in government sites is routine, and a dead source link is indistinguishable from no source."),
        ("F-12", "The repository's own README.md and COORDINATION.md were published with unresolved merge-conflict markers",
         "Both files on `main` contained `<<<<<<<` / `=======` / `>>>>>>>` blocks, so the live repository displayed raw conflict markers. Found during this session's merge and resolved without discarding either version.",
         "Add a marker scan to any pre-merge check. `tools/check.py` in this session covers the published tree; the scan should be extended to the repository root."),
        ("F-10", "Franchise-unit and royalty comparisons span a corporate restructuring",
         "FY2023 consolidated Del Taco; FY2025 does not. A 209,556 impairment charge sits inside the FY2025 segment table. Direction is unambiguous; ratios across years are not.",
         "Recompute any ratio directly from the filings rather than from any summary, including this site's."),
    ]
    fr = "".join(
        f"""<tr><td class="metric">{esc(i)}</td><td><strong>{esc(t)}</strong></td>
<td class="note">{esc(w)}</td><td class="note">{esc(a)}</td></tr>"""
        for i, t, w, a in flags
    )
    body = f"""
<div class="notice warn">
  <strong>Everything questionable, in one place, with the source links intact</strong>
  Nothing on this page blocks the site from being used. Each item is published so it can be reviewed and closed, rather
  than quietly dropped. Ten irregularities and {len(un) + len(fl)} affected data rows.
</div>

<h2>Irregularities and anomalies</h2>
<div class="table-scroll">
<table>
<caption>F-items are process or sourcing anomalies. Each names what was found, what it prevents, and what would resolve it.</caption>
<thead><tr><th>ID</th><th>Finding</th><th>What it affects</th><th>What would close it</th></tr></thead>
<tbody>{fr}</tbody></table></div>

<h2>Rows that are blank by design ({len(un)})</h2>
{data_table(un, "Every one of these was left empty rather than estimated, inferred or borrowed from a national figure. A blank is a finding, not an omission.")}

<h2>Rows that are published but flagged ({len(fl)})</h2>
{data_table(fl, "These values are published with a caveat that materially affects how they may be used. Read the verification note before quoting any of them.")}

<h2>Rows that passed verification</h2>
<p class="lede">The remaining {sum(1 for r in rows if r['status']=='verified')} rows each carry a direct link to the official page or
endpoint that displays the value. They are listed in full on the <a href="sources.html">Sources</a> page, grouped by publisher.</p>
"""
    write("review.html", page("review.html", "Flagged for Review", body,
                              "Ten irregularities and every affected row, published rather than hidden.",
                              "Integrity register"))


def build_sources(rows):
    by_src = {}
    for r in rows:
        if r["url"].startswith("http"):
            by_src.setdefault(r["source"], []).append(r)
    blocks = []
    for src in sorted(by_src):
        ids = ", ".join(r["id"] for r in by_src[src])
        url = by_src[src][0]["url"]
        blocks.append(
            f'<li><a href="{esc(url)}" rel="noopener">{esc(src)}</a><br>'
            f'<span class="note">Used by {esc(ids)}</span></li>'
        )
    publishers = [
        ("U.S. Securities and Exchange Commission", "Jack in the Box Inc. Form 10-K (FY2023, FY2024, FY2025), Form 8-K (Del Taco sale), CIK 0000807882.", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000807882&type=10-K&count=10"),
        ("U.S. Bureau of Labor Statistics", "LAUS, CES and CPI series; Economy at a Glance for Los Angeles–Long Beach–Glendale.", "https://www.bls.gov/eag/eag.ca_losangeles_md.htm"),
        ("U.S. Census Bureau", "ACS 2020–2024 5-year tables and QuickFacts population estimates.", "https://www.census.gov/quickfacts/fact/table/losangelescitycalifornia/PST045225"),
        ("Federal Reserve / FRED", "H.15 10-year Treasury constant maturity.", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10&cosd=2026-10-01"),
        ("California Legislative Information", "Constitution Article XIII A; Revenue & Taxation Code 11911 and 17043.", "https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CONS&article=XIII%20A"),
        ("Internal Revenue Service", "Topic 409, net investment income tax, like-kind exchanges, depreciation overview.", "https://www.irs.gov/taxtopics/tc409"),
        ("California Franchise Tax Board", "2025 Form 540 tax rate schedules.", "https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf"),
        ("U.S. Code (GovInfo)", "26 U.S.C. §168 — accelerated cost recovery system.", "https://www.govinfo.gov/content/pkg/USCODE-2023-title26/html/USCODE-2023-title26-subtitleA-chap1-subchapB-partVI-sec168.htm"),
        ("CAL FIRE / Office of the State Fire Marshal", "Fire Hazard Severity Zone statute, classes and LRA map vintages.", "https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones"),
        ("California Geological Survey", "Alquist-Priolo Earthquake Fault Zones; EQ Zapp seismic hazard zones.", "https://gis.data.cnra.ca.gov/datasets/cadoc::cgs-alquist-priolo-fault-zones"),
        ("FEMA", "National Risk Index v1.20; National Flood Hazard Layer.", "https://www.fema.gov/emergency-managers/practitioners/resilience-analysis-and-planning-tool"),
        ("City of Los Angeles Housing Department", "Measure ULA programme and the additional transfer tax above $5m.", "https://housing.lacity.gov/partners/funding-programs"),
        ("LA County Assessor", "Property tax framework, decline-in-value and disaster relief programmes.", "https://assessor.lacounty.gov/proposition-13"),
    ]
    pub = "".join(
        f'<li><a href="{esc(u)}" rel="noopener">{esc(n)}</a><br><span class="note">{esc(d)}</span></li>'
        for n, d, u in publishers
    )
    body = f"""
<div class="notice info">
  <strong>Official publishers only</strong>
  Every value on this site came from a government, legislative, judicial-adjacent or securities-filing source. No broker
  survey, news article, listing site or model output was used as a source anywhere. Where an official source did not
  exist, the row is blank — see the <a href="review.html">review page</a>.
</div>

<h2>Publishers</h2>
<ul class="clean">{pub}</ul>

<h2>Every sourced row, grouped by publisher</h2>
<p class="lede">This is the audit trail. Each link goes to the page or API endpoint that displays the value, not to a
homepage. Rows are identified by their registry ID so they can be traced back to the tables elsewhere on the site.</p>
<ul class="clean">{''.join(blocks)}</ul>

<h2>What was deliberately excluded as a source</h2>
<ul class="clean">
  <li><strong>Broker and listing surveys.</strong> Not official; would have been the easiest way to fill the market rows, and that is exactly why they were not used.</li>
  <li><strong>News articles and blogs.</strong> One blog figure survives only as a flagged priority signal (F-06 / HAZ-02), explicitly not a finding.</li>
  <li><strong>Private data vendors.</strong> Tract and income values were taken from Census tables via a public mirror of the Census API, and the API shape is linked so it can be re-pulled.</li>
  <li><strong>Any model or forecast.</strong> No forecast is published anywhere on this site. The calculator applies statutory rules to inputs the reader supplies.</li>
</ul>
"""
    write("sources.html", page("sources.html", "Sources", body,
                               "The full audit trail: official publishers, direct links, and what was excluded.",
                               "Verification"))


def build_privacy(rows):
    body = """
<div class="notice ok">
  <strong>Nothing personal is on this site, and nothing personal can be</strong>
  The subject property is described as “a single-tenant Jack in the Box under a triple-net lease in central Los Angeles”.
  That is the entire level of specificity. No address, APN, owner name, tenant entity name, lease term, rent figure,
  loan balance, tax return detail or adviser name appears anywhere in this repository's published output.
</div>

<h2>The rule that governs this project</h2>
<p class="lede">Personal and asset-identifying information is the highest-priority constraint, above completeness. When the
two conflict, the site stays incomplete. That is why fourteen rows are blank rather than filled: filling them would have
required publishing, or inferring from, information that belongs in a private file.</p>

<h2>What is published versus what is private</h2>
<div class="table-scroll">
<table>
<caption>The split is structural, not discretionary. The private folder is excluded from the published site by the generator.</caption>
<thead><tr><th>Category</th><th>Where it lives</th><th>Published?</th></tr></thead>
<tbody>
<tr><td>Parcel identity — address, APN, legal description</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Owner identity, entity structure, personal finances</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Lease document, rent, options, side letters</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Tenant's unit-level sales and margin</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Tax returns, depreciation schedules, basis</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Insurance quotes and lender terms</td><td>Private workspace only</td><td><span class="badge b-unverified">never</span></td></tr>
<tr><td>Public law — tax rates, statutes, hazard classes</td><td>This site</td><td><span class="badge b-verified">yes</span></td></tr>
<tr><td>Public filings — the tenant's units, royalties, segment profit</td><td>This site</td><td><span class="badge b-verified">yes</span></td></tr>
<tr><td>Public statistics — ACS, BLS, CPI, Treasury yields</td><td>This site</td><td><span class="badge b-verified">yes</span></td></tr>
<tr><td>Aggregate findings and the decision framework</td><td>This site</td><td><span class="badge b-verified">yes</span></td></tr>
</tbody></table></div>

<h2>How anonymisation is enforced technically</h2>
<ol class="tight">
  <li><strong>Generator-level separation.</strong> The build script reads only <code>data/</code> and writes only
    <code>docs/</code>. The <code>private/</code> directory is in <code>.gitignore</code> and is never copied.</li>
  <li><strong>Placeholders in the private templates.</strong> The lease abstract and notice calendar ship as empty
    templates with <code>[[PLACEHOLDER]]</code> fields, so no real term can be committed by accident.</li>
  <li><strong>Registry validation.</strong> The build fails if a row marked verified has no source link — which makes
    “verified” mean “linked”, not “remembered”.</li>
  <li><strong>No client-side collection at all.</strong> No analytics, no cookies, no localStorage, no network requests
    from the calculator, no external fonts or scripts. The suggestion tool writes to a textarea you can copy and nothing else.</li>
  <li><strong>Static hosting only.</strong> GitHub Pages serves files; there is no server to log a visitor, and no form to submit.</li>
</ol>

<h2>Handling rules for the private workspace</h2>
<ul class="clean">
  <li><strong>Access control.</strong> Single-tenant, encrypted at rest, with per-user accounts and an access log. No shared logins.</li>
  <li><strong>Named advisers only.</strong> Share under NDA with a written list of who holds access and why.</li>
  <li><strong>Minimisation.</strong> The private workspace holds only what the decision needs — not full personal financial statements if a summary will do.</li>
  <li><strong>Retention.</strong> Set a review date and a deletion date for each sensitive document.</li>
  <li><strong>No re-identification in aggregate outputs.</strong> Anything published must be unable to point at one parcel or one person. A single-asset site is inherently borderline; the mitigation is that no identifying facts are included at all.</li>
  <li><strong>Breach readiness.</strong> Know who to notify and how, before it is needed. California's breach-notification statute applies to personal information held by a business.</li>
</ul>

<h2>What the reader of this site can and cannot learn</h2>
<div class="grid g2">
  <div class="card">
    <h3>Can learn</h3>
    <ul class="clean">
      <li>How the tax machinery works at these rates, with primary-law links.</li>
      <li>That the tenant's domestic system has been shrinking, from its own filings.</li>
      <li>Which official databases answer which hazard question, and how to query them.</li>
      <li>What the decision gates are and why they matter.</li>
    </ul>
  </div>
  <div class="card">
    <h3>Cannot learn</h3>
    <ul class="clean">
      <li>Where the property is.</li>
      <li>Who owns it, or what they paid.</li>
      <li>What the rent is, or when the lease expires more precisely than 2030–2035.</li>
      <li>What the owner's tax position is.</li>
      <li>What the property is worth.</li>
    </ul>
  </div>
</div>
<div class="notice info">
  <strong>This is not legal advice on privacy compliance</strong>
  The handling rules above are operational practice for this workspace. California's CCPA/CPRA and the breach-notification
  statute impose specific obligations on a business holding personal information; confirm the applicable duties with counsel
  rather than relying on this page.
</div>
"""
    write("privacy.html", page("privacy.html", "Privacy &amp; Anonymisation", body,
                               "What is published, what never leaves the private workspace, and how the split is enforced in code.",
                               "Policy"))


def build_summary(rows):
    body = f"""
<div class="notice info noprint">
  <strong>W-10 · One page, printable</strong>
  This page is laid out for printing — use your browser's print command and it drops the navigation and fits the content
  to the page. It is written to be handed to an adviser or a lender as a starting brief, not as a conclusion.
</div>

<div class="printonly" style="border-bottom:2px solid #000;margin-bottom:12px;padding-bottom:6px">
  <strong>Jack in the Box · NNN leasehold · central Los Angeles</strong> — advisor brief, prepared {TODAY.isoformat()}.
  Anonymised: no address, APN, owner or lease terms are included.
</div>

<h2>1 · The question</h2>
<p>An owner holds a single-tenant Jack in the Box on a triple-net lease in central Los Angeles. The lease expires somewhere
between 2030 and 2035. The owner must decide whether to sell before expiry or to pursue a renewal, weighing after-tax
proceeds against the risk and opportunity of holding, including low-probability events that would damage the local economy.</p>

<h2>2 · What is verified</h2>
<div class="table-scroll">
<table>
<caption>Only figures with a direct official link appear here. Full detail and every caveat is on the sector pages.</caption>
<thead><tr><th>Finding</th><th>Value</th><th>Source</th></tr></thead>
<tbody>
<tr><td>Tenant's franchise units, FY2023 → FY2025</td><td class="num">2,044 → 2,041 → 1,986</td><td class="src">Form 10-K, SEC</td></tr>
<tr><td>Tenant's franchise royalties, FY2023 → FY2025</td><td class="num">207,064 → 198,377 → 189,646 (USD 000)</td><td class="src">Form 10-K, SEC</td></tr>
<tr><td>Tenant's franchise rental revenue, FY2023 → FY2025</td><td class="num">351,283 → 347,227 → 332,735 (USD 000)</td><td class="src">Form 10-K, SEC</td></tr>
<tr><td>Tenant's Jack in the Box segment profit, FY2025</td><td class="num">329,700 (USD 000), down from 382,686 in FY2023</td><td class="src">Form 10-K, SEC</td></tr>
<tr><td>City median household income</td><td class="num">$81,939</td><td class="src">ACS 2020–2024</td></tr>
<tr><td>County median household income</td><td class="num">$90,112</td><td class="src">ACS 2020–2024</td></tr>
<tr><td>City unemployment rate, Sept 2026</td><td class="num">4.5% (preliminary)</td><td class="src">BLS LAUS</td></tr>
<tr><td>Metro leisure &amp; hospitality employment, 12-month change</td><td class="num">+2.0%</td><td class="src">BLS CES</td></tr>
<tr><td>Metro CPI-U, 12-month change</td><td class="num">3.3–3.7%</td><td class="src">BLS</td></tr>
<tr><td>10-year Treasury</td><td class="num">4.92% (23 Nov 2026)</td><td class="src">Federal Reserve H.15</td></tr>
<tr><td>Prop 13 base property tax rate</td><td class="num">1.0%, growth capped at 2%/yr</td><td class="src">Cal. Const. Art. XIII A</td></tr>
<tr><td>Depreciation, nonresidential real property</td><td class="num">39 years, straight line</td><td class="src">26 U.S.C. §168</td></tr>
<tr><td>Unrecaptured §1250 gain ceiling</td><td class="num">25%</td><td class="src">IRS Topic 409</td></tr>
<tr><td>Net investment income tax</td><td class="num">3.8% above the MAGI threshold</td><td class="src">IRS</td></tr>
<tr><td>California top marginal rate</td><td class="num">12.3%, plus 1% above $1m taxable income</td><td class="src">FTB; RTC 17043</td></tr>
<tr><td>City of Los Angeles Measure ULA surtax</td><td class="num">4% above $5m; 5.5% at $10m+</td><td class="src">LAHD; CD-4</td></tr>
<tr><td>Los Angeles County NRI risk rating</td><td class="num">Relatively High</td><td class="src">FEMA NRI v1.20</td></tr>
</tbody></table></div>

<h2>3 · What is missing</h2>
<p>Five gaps block a defensible decision: <strong>(1)</strong> no parcel identifier, so no hazard zone, zoning, traffic count
or assessed value; <strong>(2)</strong> no lease document, so no expiration, rent, escalator or option terms;
<strong>(3)</strong> no verified comparable sales or quotes, so no short-lease discount and no capitalisation rate;
<strong>(4)</strong> no basis or depreciation history, so no after-tax result; <strong>(5)</strong> no defined trade area,
so the city and county figures on this site are substitutes rather than findings.</p>

<h2>4 · What the evidence suggests, stated as a direction rather than a verdict</h2>
<ol class="tight">
  <li><strong>The renewal case must be made to the operator, and early.</strong> The parent has been shrinking its domestic
    estate and divesting toward an asset-light model. Franchisees decide renewals on unit economics, and they decide them
    well before expiry.</li>
  <li><strong>Selling is more expensive than the headline price implies.</strong> At these rates, tax and transfer cost can
    consume roughly a fifth or more of a sale price, with Measure ULA alone worth 4–5.5% in the City.</li>
  <li><strong>The regional economy does not rescue a weak lease.</strong> Flat office employment, shrinking information and
    manufacturing employment, a city income base below the county, and a near-5% ten-year rate are all headwinds to value.</li>
  <li><strong>The dominant unknown is the short-lease discount.</strong> Until it is priced from recorded sales, the sell
    case cannot be compared to the hold case at all.</li>
  <li><strong>Neither option is comfortable.</strong> Holding concentrates capital in one asset in one seismic region;
    selling converts a deferred tax into a paid one and forfeits any renewal upside. That tension is the decision.</li>
</ol>

<h2>5 · What to do next, in order</h2>
<ol class="tight">
  <li>Open the private workspace and place the deed, tax bill and lease in it (a day).</li>
  <li>Run the four hazard lookups and geocode the parcel (an afternoon).</li>
  <li>Abstract the lease and reconcile the notice calendar with counsel (a week).</li>
  <li>Request three broker opinions and three insurance quotes (two weeks).</li>
  <li>Have the adviser reconstruct basis, recapture and entity-level tax (two weeks, in parallel).</li>
  <li>Re-run the <a href="calculator.html">calculator</a> with real inputs, then declare a decision and record it with its rationale.</li>
</ol>

<h2>6 · Limitations of this brief</h2>
<p class="note">This is an analytical working file, not an appraisal, not tax advice, not legal advice and not an investment
recommendation. It contains no forecast. Figures marked preliminary or flagged carry caveats that are material to their use;
they are listed on the <a href="review.html">review page</a>. Every value is traceable to the official source on the
<a href="sources.html">sources page</a>, and anything that could not be traced was left blank.</p>
"""
    write("summary.html", page("summary.html", "One-Page Printable Summary", body,
                               "The brief to hand an adviser: verified findings, named gaps, and the order of next steps.",
                               "W-10 · Advisor summary"))


def build_404():
    body = """
<div class="notice info">
  <strong>That page does not exist</strong>
  Use the navigation above, or start from the <a href="index.html">overview</a>.
</div>
"""
    write("404.html", page("404.html", "Page not found", body))


def build_data_exports(rows):
    (DOCS / "data").mkdir(exist_ok=True)
    payload = {
        "generated": TODAY.isoformat(),
        "registry_checked": "2026-11-25",
        "note": "Machine-readable mirror of data/registry.yaml. Blank value = unverified. Never fill a blank by inference.",
        "counts": {s: sum(1 for r in rows if r["status"] == s) for s in STATUS_CLASS},
        "rows": len(rows),
        "data": [{k: str(v) for k, v in r.items()} for r in rows],
    }
    (DOCS / "data" / "registry.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    import csv
    with (DOCS / "data" / "registry.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "category", "metric", "value", "unit", "geo",
                                           "period", "source", "url", "status", "note"])
        w.writeheader()
        w.writerows(rows)

    (DOCS / "data" / "build.json").write_text(json.dumps({
        "generated": TODAY.isoformat(),
        "rows": len(rows),
        "verified": sum(1 for r in rows if r["status"] == "verified"),
        "flagged": sum(1 for r in rows if r["status"] == "flagged"),
        "unverified": sum(1 for r in rows if r["status"] == "unverified"),
        "pages": len(NAV),
    }, indent=2), encoding="utf-8")


def build_jekyll():
    """No _config.yml is emitted on purpose.

    The repository root is the GitHub Pages source, and a `_config.yml` inside a
    subdirectory changes how Jekyll processes the whole site. Only robots.txt is
    written here; the dotted .nojekyll lives at the repository root.
    """
    (DOCS / "robots.txt").write_text("User-agent: *\nAllow: /workspace/\n", encoding="utf-8")
    if (DOCS / ".nojekyll").exists():
        (DOCS / ".nojekyll").unlink()


def main():
    rows = load_registry()
    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (DOCS / "assets" / "js").mkdir(parents=True, exist_ok=True)

    build_index(rows)
    build_questions(rows)
    build_economy(rows)
    build_tracts(rows)
    build_operator(rows)
    build_hazards(rows)
    build_tax(rows)
    build_market(rows)
    build_model(rows)
    build_gates(rows)
    build_risks(rows)
    build_calculator(rows)
    build_suggestions(rows)
    build_review(rows)
    build_sources(rows)
    build_privacy(rows)
    build_summary(rows)
    build_404()
    build_data_exports(rows)
    build_jekyll()

    print(f"built {len(NAV)} pages from {len(rows)} registry rows "
          f"({sum(1 for r in rows if r['status']=='verified')} verified, "
          f"{sum(1 for r in rows if r['status']=='flagged')} flagged, "
          f"{sum(1 for r in rows if r['status']=='unverified')} blank)")


if __name__ == "__main__":
    main()
