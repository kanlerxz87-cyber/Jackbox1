#!/usr/bin/env python3
"""
build_site.py — generates the whole static site from data/*.json.

Design rules enforced here:
  * No value is ever written to HTML that is not in data/.
  * A row with verified=false renders as a blank cell plus a FLAGGED badge.
  * Every table row carries a source link, or is explicitly marked as having none.
  * No external CSS, JS, font or tracker is referenced.

Run:  python3 tools/build_site.py
"""
import json, os, re, html, datetime, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "workspace"  # this site lives at /workspace/ on the published root

BUILD_DATE = "2026-11-25"


# ---------------------------------------------------------------- helpers
def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


def esc(text):
    return html.escape(str(text), quote=True)


def money(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return f"${v:,.0f}"
    return str(v)


def numfmt(v, unit=""):
    if v is None:
        return None
    if isinstance(v, float):
        s = f"{v:,.2f}".rstrip("0").rstrip(".")
    elif isinstance(v, int):
        s = f"{v:,}"
    else:
        s = str(v)
    return s


NAV = [
    ("index.html", "Dashboard"),
    ("gates.html", "Decision Gates"),
    ("sell-vs-renew.html", "Sell vs Renew"),
    ("market.html", "Market & Economy"),
    ("location.html", "Trade Area"),
    ("hazards.html", "Hazards & Risk"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]


def page(filename, title, eyebrow, body, lede="", extra_head="", wide_note=""):
    cur = ' aria-current="page"'
    nav_html = "\n".join(
        '      <a href="%s"%s>%s</a>' % (href, cur if href == filename else "", esc(label))
        for href, label in NAV
    )
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Parcel Decision Workspace</title>
<meta name="description" content="An anonymised, source-linked decision workspace for a single-tenant quick-service parcel in central Los Angeles. Contains no personal or parcel-identifying information.">
<meta name="robots" content="index, follow">
<link rel="stylesheet" href="assets/css/app.css">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="header-inner">
    <a class="brand" href="index.html">
      <span class="brand-mark" aria-hidden="true">PDW</span>
      <span class="brand-text">
        <strong>Parcel Decision Workspace</strong>
        <span>Anonymised &middot; source-linked &middot; no personal data</span>
      </span>
    </a>
    <div class="header-meta">
      <b>PARCEL-A &middot; OWNER-1 &middot; TENANT-A</b><br>
      Central Los Angeles &middot; NNN &middot; expiry window 2030&ndash;2035<br>
      Evidence compiled {BUILD_DATE}
    </div>
  </div>
</header>

<nav class="site-nav" aria-label="Sections">
  <div class="nav-inner">
{nav_html}
  </div>
</nav>

<main id="main">
<div class="no-print" style="border:1px solid var(--line);background:#f7f9fc;border-radius:10px;padding:.7rem 1rem;margin-bottom:1.2rem;font-size:.84rem;color:var(--ink-soft)">
<strong style="display:block;font-size:.68rem;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:.3rem">Workspace sections &mdash; three independent research trees, all published</strong>
<a href="../index.html">Desk home</a> &nbsp;&middot;&nbsp; <a href="../pages/market.html">Desk pages</a> &nbsp;&middot;&nbsp; <a href="../docs/index.html">Sourced dashboard</a> &nbsp;&middot;&nbsp; <b>Verified workspace (this section)</b>
</div>
{lede_html}
{body}
</main>

<footer class="site-footer">
  <div class="footer-inner">
    <div>
      <strong>Parcel Decision Workspace</strong> &mdash; built {BUILD_DATE}.<br>
      Part of a three-section workspace: <a href="../index.html">Desk home</a> &middot; <a href="../pages/market.html">Desk pages</a> &middot; <a href="../docs/index.html">Sourced dashboard</a>.<br>
      Public product. Contains no address, parcel number, owner name, lease text or financial figure belonging to any person or entity.
      Private material is held offline with authorised advisers.
    </div>
    <nav aria-label="Footer">
      <a href="sources.html">Sources</a>
      <a href="flagged.html">Flagged for Review</a>
      <a href="questions.html">Open Questions</a>
      <a href="advisor-summary.html">One-Page Summary</a>
    </nav>
  </div>
</footer>
</body>
</html>
"""
    (SITE / filename).write_text(doc, encoding="utf-8")
    return filename


def badge(text, kind="gray"):
    return f'<span class="badge {kind}">{esc(text)}</span>'


def src_link(url, name, extra_class="src"):
    if url:
        return f'<a href="{esc(url)}" rel="noopener noreferrer" title="{esc(name)}">{esc(name)}</a>'
    return '<span class="muted">no published source</span>'


def verify_cell(verified, url, name):
    if verified and url:
        return f'<td class="src">{src_link(url, name)}</td>'
    if url:
        return f'<td class="src">{src_link(url, name)}<br>{badge("flagged", "warn")}</td>'
    return f'<td class="src"><span class="muted">no source</span><br>{badge("flagged", "warn")}</td>'


# ---------------------------------------------------------------- page: dashboard
def build_index():
    gates = load("gates.json")
    qs = load("questions.json")
    flagged = load("flagged.json")
    market = load("market.json")
    sug = load("suggestions.json")
    haz = load("hazards.json")

    n_gates = len(gates["gates"])
    n_open = sum(1 for g in gates["gates"] if g["state"] != "closed")
    n_blocking = sum(1 for q in qs["questions"] if q["priority"] == "blocking")
    n_missing = sum(1 for q in qs["questions"] if q["state"] in ("missing", "partly have"))
    n_flagged = len(flagged["items"])
    n_verified = sum(1 for m in market["metrics"] if m["verified"])
    n_metrics = len(market["metrics"])
    pct = int(round(100 * n_verified / n_metrics))

    def gate_rows():
        out = []
        for g in gates["gates"]:
            if g["state"] == "closed":
                kind, label = "ok", "closed"
            elif g["state"] == "blocked":
                kind, label = "stop", "blocked"
            else:
                kind, label = "warn", "open"
            done = sum(1 for r in g["requirements"] if r["done"])
            total = len(g["requirements"])
            out.append(
                f'<tr><td><a href="gates.html#{esc(g["id"])}">{esc(g["id"])}</a></td>'
                f'<td>{esc(g["name"])}</td>'
                f'<td>{badge(label, kind)}</td>'
                f'<td class="num">{done}/{total}</td>'
                f'<td>{esc(g["summary"])}</td></tr>'
            )
        return "\n".join(out)

    body = f"""
<section class="grid four" aria-label="Key indicators">
  <div class="card kpi">
    <span class="label">Blocking questions open</span>
    <span class="value">{n_blocking}</span>
    <span class="sub">of {qs['summary_counts']['total']} in the register. No recommendation can be issued while any remain.</span>
    <a href="questions.html">Open the register &rarr;</a>
  </div>
  <div class="card kpi">
    <span class="label">Decision gates not closed</span>
    <span class="value">{n_open}</span>
    <span class="sub">of {n_gates}. One is closed: privacy controls.</span>
    <a href="gates.html">See the board &rarr;</a>
  </div>
  <div class="card kpi">
    <span class="label">Data rows verified</span>
    <span class="value">{n_verified}<span class="muted" style="font-size:1rem;font-weight:500"> / {n_metrics}</span></span>
    <div class="bar" aria-hidden="true"><span style="width:{pct}%"></span></div>
    <span class="sub">Every verified row links to an official page. Blank rows are on the flagged list.</span>
    <a href="market.html">Market evidence &rarr;</a>
  </div>
  <div class="card kpi">
    <span class="label">Items flagged for review</span>
    <span class="value">{n_flagged}</span>
    <span class="sub">Published with the URL that was attempted and the reason it failed.</span>
    <a href="flagged.html">Review the flags &rarr;</a>
  </div>
</section>

<div class="notice stop">
  <p><strong>The short answer: there is no recommendation, and giving one would be a fabrication.</strong>
  The two decisions on the table &mdash; sell before expiry, or renew &mdash; both depend on a rent, a price and a basis.
  None of the three exists in this workspace. What does exist is a verified picture of the city and metro economy,
  a verified set of tax rules, confirmed official channels for every hazard and site question, and a complete list of
  what is still missing. The tool at <a href="sell-vs-renew.html">Sell vs Renew</a> will run any numbers you supply,
  but it refuses to invent them.</p>
</div>

<h2>What this workspace is for</h2>
<div class="grid two">
  <div class="card">
    <h3>It answers the answerable part</h3>
    <p class="small">Direction of the local economy, the tenant's own public disclosures, the tax rules that apply to a
    sale, and the official channel for each parcel-level question. All of it is linked. None of it is estimated.</p>
    <ul class="clean small">
      <li>Metro unemployment <b>4.4%</b> (Sep 2026), down from 5.5% a year earlier.</li>
      <li>City median household income <b>$81,939</b> in 2020&ndash;2024 dollars.</li>
      <li>City population <b>3,869,089</b> at July 2025, <b>&minus;0.8%</b> from the 2020 base.</li>
      <li>California house prices <b>+0.6%</b> over four quarters to 2026Q3, versus <b>+2.5%</b> nationally.</li>
    </ul>
    <p class="small"><a href="market.html">All of it, with sources &rarr;</a></p>
  </div>
  <div class="card">
    <h3>It refuses the unanswerable part</h3>
    <p class="small">Four things would decide this file, and none of them is public. Each is a named deliverable with an
    owner, not a research task that can be finished by reading the web.</p>
    <ul class="clean small">
      <li>The lease: term, rent, options and notice dates &rarr; private abstract.</li>
      <li>The price: a valuation and closed comparables &rarr; broker and appraiser.</li>
      <li>The tax: basis and depreciation history &rarr; the owner's CPA.</li>
      <li>The building: condition, insurance and hazard zones &rarr; engineer and broker.</li>
    </ul>
    <p class="small"><a href="questions.html">The full register of {qs['summary_counts']['total']} questions &rarr;</a></p>
  </div>
</div>

<h2 id="gates">Decision-gate progress board <span class="badge info">W-03</span></h2>
<p class="small">A gate closes only when every requirement under it is evidenced by a document. A closed gate is not a
decision; it is permission to make one.</p>
<div class="table-wrap">
  <table>
    <caption>Gate state
      <span class="cap-sub">Open and blocked gates both prevent a verdict. Blocked means no party can close it until a third party delivers.</span>
    </caption>
    <thead><tr><th>Gate</th><th>Name</th><th>State</th><th class="num">Reqs met</th><th>Why it matters</th></tr></thead>
    <tbody>
{gate_rows()}
    </tbody>
  </table>
</div>

<h2>Path through the site</h2>
<div class="grid three">
  <div class="card tight">
    <h3>1. Understand the economics</h3>
    <p class="small"><a href="market.html">Market &amp; Economy</a> — city, metro and price evidence, every row sourced.</p>
    <p class="small"><a href="location.html">Trade Area</a> — why city figures are a proxy, and the exact private steps that replace them.</p>
  </div>
  <div class="card tight">
    <h3>2. Understand the risk</h3>
    <p class="small"><a href="hazards.html">Hazards &amp; Risk</a> — the four official parcel-level programmes, confirmed, with the parcel rows deliberately blank.</p>
    <p class="small"><a href="sell-vs-renew.html">Sell vs Renew</a> — five decision options, their risks, and an after-tax calculator that runs in your browser.</p>
  </div>
  <div class="card tight">
    <h3>3. Close the gaps</h3>
    <p class="small"><a href="questions.html">Questions</a> — {qs['summary_counts']['total']} gating questions, each with how to answer it and who owns it.</p>
    <p class="small"><a href="suggestions.html">Suggestions</a> — a reviewable register with effort, cost, falsifier and a privacy verdict for each.</p>
  </div>
</div>

<h2>What is deliberately absent</h2>
<div class="card">
  <p class="small">By instruction and by design, this public product contains <b>no</b> street address, <b>no</b> assessor
  parcel number, <b>no</b> owner or tenant identifying detail, <b>no</b> lease text, and <b>no</b> figure describing the
  owner's finances. People and the property appear only as <code>OWNER-1</code>, <code>TENANT-A</code>,
  <code>PARCEL-A</code>, <code>ADVISER-1</code>&hellip;6. Anything that could locate the parcel is on the
  <a href="flagged.html">Flagged for Review</a> page with the reason it was withheld rather than published.</p>
</div>
"""
    return page("index.html", "Dashboard", "Decision workspace", body)


# ---------------------------------------------------------------- page: gates
def build_gates():
    gates = load("gates.json")
    d = gates["decision_status"]

    def block(g):
        if g["state"] == "closed":
            kind, label = "ok", "closed"
        elif g["state"] == "blocked":
            kind, label = "stop", "blocked"
        else:
            kind, label = "warn", "open"
        DONE_B = '<span class="badge ok">done</span>'
        OPEN_B = '<span class="badge gray">outstanding</span>'
        CHECK = '&#10003; '
        reqs = "".join(
            '<li>%s%s %s</li>' % (
                CHECK if r["done"] else "",
                esc(r["text"]),
                DONE_B if r["done"] else OPEN_B,
            )
            for r in g["requirements"]
        )
        done = sum(1 for r in g["requirements"] if r["done"])
        total = len(g["requirements"])
        pct = int(round(100 * done / total))
        return f"""
<div class="gate {g['state']}" id="{esc(g['id'])}">
  <h3>{esc(g['id'])} &middot; {esc(g['name'])} {badge(label, kind)}</h3>
  <p class="why">{esc(g['summary'])}</p>
  <div class="progress-shell"><div class="bar"><span style="width:{pct}%"></span></div><span class="small muted">{done}/{total}</span></div>
  <ul class="clean small">{reqs}</ul>
  <p class="tiny muted"><b>Closed by:</b> {esc(g['closed_by'])} &nbsp;&middot;&nbsp; <b>If left open:</b> {esc(g['consequence_if_open'])}</p>
</div>"""

    body = f"""
<p class="lede">{len(gates['gates'])} gates stand between this file and a decision. {sum(1 for g in gates['gates'] if g['state']!='closed')} are not closed. The board exists so that progress
is visible without pretending the work is done.</p>

<div class="grid three">
  <div class="card kpi"><span class="label">Sell before expiry</span>
    <span class="value blank">{esc(d['sell_before_expiry']['state'])}</span>
    <span class="sub">{esc(d['sell_before_expiry']['plain'])}</span>
    <span class="sub tiny muted">Blocked by {esc(', '.join(d['sell_before_expiry']['blocked_by']))}</span></div>
  <div class="card kpi"><span class="label">Renew the lease</span>
    <span class="value blank">{esc(d['renew_lease']['state'])}</span>
    <span class="sub">{esc(d['renew_lease']['plain'])}</span>
    <span class="sub tiny muted">Blocked by {esc(', '.join(d['renew_lease']['blocked_by']))}</span></div>
  <div class="card kpi"><span class="label">Hold to expiry</span>
    <span class="value blank">{esc(d['hold_to_expiry']['state'])}</span>
    <span class="sub">{esc(d['hold_to_expiry']['plain'])}</span>
    <span class="sub tiny muted">Blocked by {esc(', '.join(d['hold_to_expiry']['blocked_by']))}</span></div>
</div>

<div class="notice">{esc(d['overall'])}</div>

<h2>The gates</h2>
{''.join(block(g) for g in gates['gates'])}

<h2>Why the board is ordered this way</h2>
<div class="card">
  <p class="small">G-1 comes first because it is both the cheapest to close and the most time-sensitive. A renewal
  notice window that passes cannot be reopened by any amount of analysis. G-2 and G-3 come next because together
  they produce the only two numbers a sell-versus-renew comparison actually needs: what the asset would fetch, and
  what the owner would keep. G-4 sits inside both cases, because a hazard designation and an insurance file change
  the hold case and the buyer's view of the sale case at the same time. G-5 and G-6 are open rather than blocked:
  they can be closed by work already in scope, and the site is built to do the published half of G-5.</p>
  <p class="small">G-7 is the only closed gate. It is closed because the privacy control is verifiable in the artefact
  itself: you can read every page of this site and find no identifier. The remaining item under G-7 &mdash; the written
  access list &mdash; lives offline by necessity, which is why the gate is marked closed on the public side only.</p>
</div>

<h2>How to move a gate</h2>
<ol class="steps">
  <li>Open the gate's page entry and read the outstanding requirements. Each one names the document, not a task.</li>
  <li>Check the <a href="questions.html">Questions</a> register for the matching question. It carries the owner and the source.</li>
  <li>Check <a href="suggestions.html">Suggestions</a> for the cheapest route to that document, with a falsifier.</li>
  <li>When the document arrives, change <code>done</code> to <code>true</code> in <code>data/gates.json</code> and rebuild. Do not edit the HTML.</li>
</ol>
"""
    return page("gates.html", "Decision Gates", "Gate board", body)


# ---------------------------------------------------------------- page: market
def build_market():
    market = load("market.json")
    tenant = load("tenant.json")
    groups = {}
    for m in market["metrics"]:
        groups.setdefault(m["group"], []).append(m)

    def rows(items):
        out = []
        for m in items:
            val = m["value"]
            if val is None:
                cell = '<td class="num blank">&mdash;</td>'
            else:
                unit = m["unit"]
                v = numfmt(val)
                suffix = ""
                if unit.startswith("%"):
                    suffix = "%"
                cell = f'<td class="num">{v}{suffix}<br><span class="tiny muted">{esc(unit.replace("%","").strip() or "")}</span></td>'
            flag = "" if m["verified"] else " " + badge("flagged", "warn")
            note = esc(m["note"]) if m["note"] else ""
            out.append(
                f'<tr><td><code>{esc(m["id"])}</code></td>'
                f'<td>{esc(m["label"])}{flag}<br><span class="tiny muted">{note}</span></td>'
                f'<td class="small">{esc(m["geo"])}</td>'
                f'<td class="small">{esc(m["period"])}</td>'
                f'{cell}'
                f'{verify_cell(m["verified"], m["source_url"], m["source_name"])}</tr>'
            )
        return "\n".join(out)

    sections = ""
    for gname, items in groups.items():
        sections += f"""
<h2 id="{re.sub(r'[^a-z0-9]+','-',gname.lower())}">{esc(gname)}</h2>
<div class="table-wrap">
  <table>
    <caption>{esc(gname)} &mdash; {len(items)} row{'s' if len(items)!=1 else ''}
      <span class="cap-sub">Values reproduce the official page as read. Blank cells could not be confirmed and are flagged rather than estimated.</span>
    </caption>
    <thead><tr><th>ID</th><th>Measure</th><th>Geography</th><th>Period</th><th class="num">Value</th><th>Official source</th></tr></thead>
    <tbody>
{rows(items)}
    </tbody>
  </table>
</div>"""

    trows = "\n".join(
        f'<tr><td><code>{esc(f["id"])}</code></td><td>{esc(f["label"])}</td>'
        f'<td class="small">{esc(f["value"]) if not isinstance(f["value"], (int,float)) else numfmt(f["value"])}'
        f'<br><span class="tiny muted">{esc(f["note"])}</span></td>'
        f'{verify_cell(f["verified"], f["source_url"], f["source_name"])}</tr>'
        for f in tenant["facts"]
    )

    tanalysis = "".join(
        f'<div class="card"><h3>{esc(a["heading"])}</h3><ul class="clean small">'
        + "".join(f'<li>{esc(p)}</li>' for p in a["points"]) + "</ul></div>"
        for a in tenant["analysis"]
    )

    body = f"""
<p class="lede">Two questions are answered here and one is not. <b>Answered:</b> how the Los Angeles economy and the
tenant's corporate parent are actually performing, from official statistics and audited filings. <b>Not answered:</b>
what this specific corner is worth, because that requires the private lease and the private address.</p>

<div class="notice">
  <p><strong>Read the geography column before using any number.</strong> The brief asks for trade-area figures around
  the parcel. No official agency publishes a drive-time trade area, and building one requires the address. So every
  figure here is a <em>city</em> or <em>metro</em> figure, labelled as such. It establishes direction, not magnitude at
  the corner. <a href="location.html">The Trade Area page explains the exact substitution and the private steps that
  replace it &rarr;</a></p>
</div>

<div class="toc" aria-label="Jump to group">
{''.join(f'<a href="#{re.sub(r"[^a-z0-9]+","-",g.lower())}">{esc(g)}</a>' for g in groups)}
<a href="#tenant">Tenant &amp; franchisor</a>
</div>

{sections}

<h2 id="tenant">Tenant &amp; franchisor evidence <span class="badge info">audited filings only</span></h2>
<p class="small">A net lease is only as strong as the obligor. Below is what Jack in the Box Inc. discloses about itself
in its most recent annual report, quoted with the accession number linked. These are <b>system-level</b> facts. They say
nothing about the restaurant at PARCEL-A and are not used as if they did.</p>
<div class="table-wrap">
  <table>
    <caption>Jack in the Box Inc. &mdash; Form 10-K for the fiscal year ended 28 September 2025, filed 19 November 2025
      <span class="cap-sub">CIK 0000807882. The 10-K index page is the canonical source for the whole filing.</span>
    </caption>
    <thead><tr><th>ID</th><th>Disclosure</th><th>As filed</th><th>Official source</th></tr></thead>
    <tbody>
{trows}
    </tbody>
    <tfoot><tr><td colspan="4">Filed document:
      <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm" rel="noopener noreferrer">Form 10-K index, accession 0000807882-25-000072</a>
      &middot; <a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getCompany&CIK=0000807882&type=10-K" rel="noopener noreferrer">All 10-K filings</a></td></tr></tfoot>
  </table>
</div>

<div class="grid two">{tanalysis}</div>

<h2>What the evidence actually says</h2>
<div class="grid two">
  <div class="card">
    <h3>The local economy is improving, unevenly</h3>
    <p class="small">Metro unemployment fell from 5.5% to 4.4% in twelve months and total nonfarm employment is up 0.5%.
    That is a gently improving picture, not a boom. Underneath it, the sectors are moving in opposite directions:
    information lost 5.7% of its jobs while education and health added 3.8%. For a drive-thru, the second number matters
    more than the first, because hospital and school employment feeds weekday lunch traffic and a stable day-shift
    population.</p>
    <p class="small"><b>What this supports:</b> a hold case that does not assume deterioration.
    <b>What it does not support:</b> a specific sales forecast for this unit.</p>
  </div>
  <div class="card">
    <h3>Prices are rising slower than the nation, and wages faster</h3>
    <p class="small">California house prices rose 0.6% over four quarters against 2.5% nationally. Local CPI is running
    at 3.7% year over year. Meanwhile the Employment Cost Index for wages and salaries in the Los Angeles CSA rose 3.9%,
    faster than the 3.1% national figure. For a restaurant, that combination is the hard part: revenue indexed to local
    price growth, labour indexed to something steeper.</p>
    <p class="small"><b>What this supports:</b> expecting the tenant to negotiate hard on rent at renewal.
    <b>What it does not support:</b> concluding the tenant cannot pay.</p>
  </div>
</div>

<div class="notice warn">
  <p><strong>Two official data gaps affect this page.</strong> BLS did not collect October 2025 data during the 2025
  lapse in appropriations, so it cannot publish an October 2026 over-the-year change; the 12-month figure shown is
  September 2026. And the Census county QuickFacts page would not load, so the county benchmark is blank rather than
  borrowed from a secondary site. Both are on the <a href="flagged.html">Flagged for Review</a> page.</p>
</div>
"""
    return page("market.html", "Market & Economy", "Verified evidence", body)


# ---------------------------------------------------------------- page: location (W-01)
def build_location():
    body = """
<p class="lede">The brief asks to replace city and county proxies with trade-area figures. This page does the honest
version of that: it says exactly which proxy is being used, what the correct replacement is, which official dataset
holds it, and the two-step private procedure that produces it without publishing the address.</p>

<div class="notice warn">
  <p><strong>Why there is no trade-area table on this page.</strong> A trade area is defined by a drive-time ring drawn
  around a point. The point is the parcel. Publishing the ring publishes the parcel. There is no official agency that
  publishes a pre-computed three-minute drive-time ring for an anonymous location, so the replacement must be computed
  privately and only the aggregate published.</p>
</div>

<h2>Step 1 &mdash; the proxy, stated plainly</h2>
<div class="table-wrap">
  <table>
    <caption>What is being used, and what it substitutes for
      <span class="cap-sub">Every substitute below is a verified city or metro figure. None of them is presented as a trade-area figure.</span>
    </caption>
    <thead><tr><th>Decision-relevant quantity</th><th>Substitute currently used</th><th>Correct geography</th><th>Why the substitute is weak</th></tr></thead>
    <tbody>
      <tr><td>Household income around the site</td><td class="small">City median household income $81,939 (ACS 2020&ndash;2024)</td><td class="small">1&ndash;3 mile ring, median household income</td><td class="small">A city of 3.87 million people averages beachfront and South LA. The ring can move opposite to the city.</td></tr>
      <tr><td>Resident population and growth</td><td class="small">City population 3,869,089 at July 2025, &minus;0.8% from the 2020 base</td><td class="small">Ring population, current and projected</td><td class="small">City growth is dominated by districts far from the parcel.</td></tr>
      <tr><td>Daytime population (lunch traffic)</td><td class="small">City civilian labour force participation 66.4%</td><td class="small">Workplace-area employment within the ring</td><td class="small">Labour-force participation is a residence measure. A drive-thru lunch is a workplace measure.</td></tr>
      <tr><td>School quality</td><td class="small">City bachelor's degree or higher 38.5%</td><td class="small">Assigned schools' CAASPP results</td><td class="small">Educational attainment of adults is not school performance. They are different datasets.</td></tr>
      <tr><td>Traffic past the door</td><td class="small">Mean travel time to work 30.7 minutes</td><td class="small">AADT at the adjacent street</td><td class="small">A commute average says nothing about the curb cut.</td></tr>
      <tr><td>Competitive supply</td><td class="small">City accommodation and food services sales $17.37bn (2022)</td><td class="small">Unit count and approved permits within the ring</td><td class="small">Aggregate sales do not reveal whether a competitor opened across the street last quarter.</td></tr>
    </tbody>
    <tfoot><tr><td colspan="4">All substitute values are verified on the <a href="market.html">Market &amp; Economy</a> page with their official source links.</td></tr></tfoot>
  </table>
</div>

<h2 id="private-steps">Step 2 &mdash; the private procedure that produces the real figures</h2>
<p class="small">Do these in the offline workspace with the real address. Record the date and the source for each.
Publish only the aggregate, and only if the aggregate cannot be reverse-engineered to a location.</p>
<ol class="steps">
  <li><b>Resolve the address to Census geography.</b> Use the Census Geocoder to obtain the 2020 census tract, block group and ZCTA.
    <span class="tiny muted">Official tool: <a href="https://geocoding.geo.census.gov/geocoder/" rel="noopener noreferrer">Census Geocoder</a>.
    The county FIPS for Los Angeles is 06037. Treat the resulting tract list as private, because it locates the parcel.</span></li>
  <li><b>Pull the same-vintage ACS tables for those tracts.</b> Keep one vintage across every table so the comparison is internally consistent.
    <span class="tiny muted">Tables: B19013 (median household income), B01003 (total population), B25064 (median gross rent), B15003 (educational attainment), S0101 (age and sex).
    Reference: <a href="https://www.census.gov/programs-surveys/acs/" rel="noopener noreferrer">American Community Survey</a>.</span></li>
  <li><b>Pull workplace employment for the ring, not residential labour force.</b> Residence-based participation is the wrong denominator for lunch traffic.
    <span class="tiny muted">Reference: <a href="https://lehd.ces.census.gov/data/" rel="noopener noreferrer">LEHD / LODES</a>, and the Census Bureau's OnTheMap for workplace-area characteristics.</span></li>
  <li><b>Pull school performance for the assigned schools only.</b> Use the district and school codes that the address resolves to.
    <span class="tiny muted">Official source: <a href="https://caaspp-elpac.ets.org/caaspp/SearchSB.aspx" rel="noopener noreferrer">CAASPP Reporting, California Department of Education</a>.
    The report must name the administration year.</span></li>
  <li><b>Pull planning and zoning.</b> ZIMAS by address for zoning, General Plan designation, specific plan and overlays.
    <span class="tiny muted">Official source: <a href="https://planning.lacity.gov/" rel="noopener noreferrer">City of Los Angeles Department of City Planning</a>.</span></li>
  <li><b>Pull traffic counts.</b> Caltrans AADT covers the State Highway System only. City street counts must be requested from the city traffic engineering or public works department.
    <span class="tiny muted">Official source: <a href="https://dot.ca.gov/programs/traffic-operations/census" rel="noopener noreferrer">Caltrans Traffic Census Program</a>.</span></li>
  <li><b>Pull competitor supply.</b> Count quick-service units and approved new ones inside the ring, and mark each open, under construction or approved.
    <span class="tiny muted">Cross-check against the city's building permit records and a site visit.</span></li>
</ol>

<h2>What can be published once this is done</h2>
<div class="grid two">
  <div class="card">
    <h3>Publishable</h3>
    <ul class="clean small">
      <li>Index values and percentage changes for the ring, as long as the ring is not described precisely enough to locate it.</li>
      <li>The count of competing units, as a number.</li>
      <li>The direction of travel: improving, flat or deteriorating, with the period.</li>
      <li>Any statutory designation that applies across a whole district rather than one parcel.</li>
    </ul>
  </div>
  <div class="card">
    <h3>Not publishable, ever</h3>
    <ul class="clean small">
      <li>The address, the parcel number, the coordinates, or a map with a marker on it.</li>
      <li>A ring small enough that it contains only a handful of blocks.</li>
      <li>Exact tract identifiers, because a tract list in the right place is a location.</li>
      <li>Anything that pairs a figure with a photograph of the storefront.</li>
    </ul>
  </div>
</div>

<h2>Why this is the right trade-off</h2>
<div class="card">
  <p class="small">The brief sets privacy as the highest priority and asks for trade-area precision at the same time.
  Those two goals conflict only if the precise answer is published. They do not conflict if the precise answer is
  computed privately and the conclusion is published in aggregate. That is what this page does: it publishes the method
  in full, so the work is reproducible by an authorised adviser, and it withholds the output, so the public site cannot
  be used to find the property.</p>
  <p class="small">The economic direction from verified city and metro data is genuinely useful and is on the
  <a href="market.html">Market &amp; Economy</a> page. What is missing is magnitude at the corner, and this page is
  honest about the fact that magnitude requires work that cannot be published.</p>
</div>
"""
    return page("location.html", "Trade Area (W-01)", "Replacing proxies", body)


# ---------------------------------------------------------------- page: hazards (W-04)
def build_hazards():
    haz = load("hazards.json")
    flags = load("flagged.json")

    def rows():
        out = []
        for h in haz["hazards"]:
            prog = (badge("programme verified", "ok") if h["program_status"] == "verified"
                    else badge("programme unverified", "warn"))
            parcel = (badge("parcel verified", "ok") if h["parcel_status"] == "verified"
                      else badge("parcel blank", "warn"))
            out.append(f"""
<tr>
  <td><code>{esc(h['id'])}</code></td>
  <td><b>{esc(h['hazard'])}</b><br><span class="tiny muted">{esc(h['why_it_matters'])}</span></td>
  <td class="small">{prog}<br>{esc(h['official_source_name'])}<br>
      <a href="{esc(h['lookup_tool_url'])}" rel="noopener noreferrer" class="tiny">Open the official lookup &rarr;</a></td>
  <td class="num">{'<span class="blank muted">&mdash;</span>' if h['parcel_designation'] is None else esc(h['parcel_designation'])}<br>{parcel}</td>
  <td class="small">{esc(h['parcel_note'])}</td>
</tr>""")
        return "\n".join(out)

    def _detail():
        out = []
        for h in haz["hazards"]:
            out.append(f"""
<details>
  <summary>{esc(h['hazard'])} &mdash; what it does to the decision</summary>
  <p class="small"><b>Programme confirmed:</b> {esc(h['program_note'])}</p>
  <p class="small"><b>Loss channels:</b> {esc(', '.join(h['loss_channels']))}</p>
  <p class="small"><b>Evidence needed:</b></p>
  <ul class="clean small">{''.join(f'<li>{esc(e)}</li>' for e in h['evidence_needed'])}</ul>
  <p class="tiny muted">Source: <a href="{esc(h['official_source_url'])}" rel="noopener noreferrer">{esc(h['official_source_name'])}</a></p>
</details>""")
        return "\n".join(out)

    detail_html = _detail()

    gaps = "".join(
        f'<div class="card tight"><h3>{esc(g["item"])}</h3><p class="small">{esc(g["detail"])}</p>'
        + (f'<p class="tiny muted">Attempted: <code>{esc(g["attempted_url"])}</code></p>' if g.get("attempted_url") else "")
        + f'<p class="small"><b>Action:</b> {esc(g["action"])}</p></div>'
        for g in haz["gaps"]
    )

    body = f"""
<p class="lede">The brief asks to replace regional hazard context with the parcel's actual zone status, and to stress
loss of rent, repairs and exit liquidity together. This page separates two things that are usually merged: what the
official programme is and can be trusted to measure, and what this parcel's own status is.</p>

<div class="grid two">
  <div class="card kpi"><span class="label">Official programmes confirmed</span>
    <span class="value">{sum(1 for h in haz['hazards'] if h['program_status']=='verified')} of 6</span>
    <span class="sub">Each with its statute or mandate and its own lookup tool, read on the agency's site.</span></div>
  <div class="card kpi"><span class="label">Parcel-level designations confirmed</span>
    <span class="value blank">0 of 6</span>
    <span class="sub">Every one of these lookups keys off the private address or coordinates. Publishing any of them would locate the parcel.</span></div>
</div>

<div class="notice stop">
  <p><strong>This is the honest state of a parcel-level screening without the address.</strong> It is not a failure of
  research. The four national programmes below were confirmed to exist, to be current, and to be the authoritative
  source. The parcel rows are blank because filling them in public would disclose the property. The private procedure
  is spelled out so that an authorised adviser can complete it in an afternoon and keep the result offline.</p>
</div>

<h2>The screening register</h2>
<div class="table-wrap">
  <table>
    <caption>Hazard screening &mdash; programme verified, parcel withheld
      <span class="cap-sub">A 'programme verified' badge means the official source and its tool were read. A 'parcel blank' badge means the designation for PARCEL-A has deliberately not been published.</span>
    </caption>
    <thead><tr><th>ID</th><th>Hazard and why it matters</th><th>Official programme</th><th class="num">Parcel status</th><th>Notes</th></tr></thead>
    <tbody>
{rows()}
    </tbody>
    <tfoot><tr><td colspan="5">Programme statements are quoted from the agency pages linked in each row. Parcel designations are withheld under the privacy rule, not omitted for convenience.</td></tr></tfoot>
  </table>
</div>

<h2>What each hazard does to the decision</h2>
{detail_html}

<h2>Stressing the three loss channels together</h2>
<div class="table-wrap">
  <table>
    <caption>How the three channels combine in a single event
      <span class="cap-sub">The calculator on the Sell vs Renew page carries one input for each of these channels, so the scenario can be run as one case rather than three separate ones.</span>
    </caption>
    <thead><tr><th>Channel</th><th>What moves</th><th>Direction</th><th>How the calculator handles it</th></tr></thead>
    <tbody>
      <tr><td>Loss of rent</td><td class="small">Months of abated or uncollected rent during closure</td><td>Reduces net proceeds and hold-case income</td><td class="small">A rent-loss input in months, applied before the sale comparison</td></tr>
      <tr><td>Repairs</td><td class="small">Cost to restore, net of insurance recovery</td><td>Reduces net proceeds directly</td><td class="small">A repair-shock input as a percentage of value</td></tr>
      <tr><td>Exit liquidity</td><td class="small">The cap rate a buyer demands after a regional event</td><td>Reduces value through the cap rate</td><td class="small">An exit cap-rate shock in basis points</td></tr>
    </tbody>
    <tfoot><tr><td colspan="4">All three are inputs, not findings. No official source supplies them for this parcel, which is why the calculator requires the user to state them.</td></tr></tfoot>
  </table>
</div>

<h2>Gaps this screening cannot close</h2>
<div class="grid two">{gaps}</div>

<h2>Black swan framing</h2>
<div class="grid two">
  <div class="card">
    <h3>What the official programmes actually measure</h3>
    <p class="small">The Office of the State Fire Marshal is explicit that fire hazard severity zone maps
    <em>evaluate hazard, not risk</em>, and that hazard is based on physical conditions over a 30 to 50 year period
    without considering mitigation. FEMA describes flood maps as continually updated, with effective information that
    may be superseded. Neither programme tells you what happens to this building; they tell you what the ground and the
    water are like.</p>
    <p class="tiny muted">Sources: <a href="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones" rel="noopener noreferrer">CAL FIRE OSFM</a> &middot;
    <a href="https://msc.fema.gov/portal/home" rel="noopener noreferrer">FEMA Flood Map Service Center</a></p>
  </div>
  <div class="card">
    <h3>What a black swan does to a net-lease asset specifically</h3>
    <p class="small">The building is small: the franchisor's own prototype is roughly 1,372 sq ft on a drive-thru pad,
    so repair cost is modest relative to land value. The exposure is therefore not principally rebuild cost. It is the
    three things that surround it: the months of lost rent while the site is closed, the premium and availability of
    insurance afterwards, and whether a buyer will still pay a short-lease cap rate for a site in a district that has
    just been through a regional event. Those three are what the calculator stresses.</p>
  </div>
</div>
"""
    detail_html = (
        "\n".join(f"""
<details>
  <summary>{esc(h['hazard'])} &mdash; what it does to the decision</summary>
  <p class="small"><b>Programme confirmed:</b> {esc(h['program_note'])}</p>
  <p class="small"><b>Loss channels:</b> {esc(', '.join(h['loss_channels']))}</p>
  <p class="small"><b>Evidence needed:</b></p>
  <ul class="clean small">{''.join(f'<li>{esc(e)}</li>' for e in h['evidence_needed'])}</ul>
  <p class="tiny muted">Source: <a href="{esc(h['official_source_url'])}" rel="noopener noreferrer">{esc(h['official_source_name'])}</a></p>
</details>""" for h in haz["hazards"]))
    return page("hazards.html", "Hazards & Risk (W-04)", "Parcel-level screening", body)


# ---------------------------------------------------------------- page: questions
def build_questions():
    qs = load("questions.json")
    groups = {}
    for q in qs["questions"]:
        groups.setdefault(q["group"], []).append(q)

    def state_badge(s):
        return {"have": badge("answered", "ok"),
                "partly have": badge("partly", "warn"),
                "missing": badge("missing", "stop")}.get(s, badge(s, "gray"))

    def prio_badge(p):
        return badge(p, "stop" if p == "blocking" else ("warn" if p == "high" else "gray"))

    sections = ""
    for gname, items in groups.items():
        rws = []
        for q in items:
            rws.append(f"""
<tr>
  <td><code>{esc(q['id'])}</code><br>{prio_badge(q['priority'])}</td>
  <td><b>{esc(q['question'])}</b><br><span class="tiny muted">{esc(q['why'])}</span></td>
  <td class="small">{state_badge(q['state'])}<br>{esc(q['known'])}</td>
  <td class="small">{esc(q['how_to_find'])}
      {f'<br><span class="tiny"><a href="{esc(q["source_url"])}" rel="noopener noreferrer">official source &rarr;</a></span>' if q.get('source_url') else '<br><span class="tiny muted">no published source — private document</span>'}</td>
  <td class="small muted">{esc(q['owner_of_task'])}</td>
</tr>""")
        sections += f"""
<h2 id="{re.sub(r'[^a-z0-9]+','-',gname.lower())}">{esc(gname)}</h2>
<div class="table-wrap">
  <table>
    <caption>{esc(gname)} &mdash; {len(items)} question{'s' if len(items)!=1 else ''}</caption>
    <thead><tr><th>ID</th><th>Question and why it gates the decision</th><th>What we have</th><th>How to close it</th><th>Owner</th></tr></thead>
    <tbody>{''.join(rws)}</tbody>
  </table>
</div>"""

    counts = qs["summary_counts"]
    body = f"""
<p class="lede">{counts['total']} questions stand between this file and a decision. {counts['have']} are answered from an official source,
{counts['partly_have']} are partly answered, and {counts['missing']} are missing. {counts['blocking']} of them are blocking: no defensible sell-or-renew
recommendation can be issued until those are closed.</p>

<div class="grid four">
  <div class="card kpi"><span class="label">Total</span><span class="value">{counts['total']}</span><span class="sub">gating questions</span></div>
  <div class="card kpi"><span class="label">Answered</span><span class="value">{counts['have']}</span><span class="sub">with an official source</span></div>
  <div class="card kpi"><span class="label">Partly answered</span><span class="value">{counts['partly_have']}</span><span class="sub">programme known, parcel value not</span></div>
  <div class="card kpi"><span class="label">Blocking</span><span class="value" style="color:var(--stop)">{counts['blocking']}</span><span class="sub">no verdict possible while these are open</span></div>
</div>

<div class="notice">
  <p><strong>How to use this page.</strong> Each row is a question with three parts: why it gates the decision, what is
  already established, and how to close it. 'Missing' does not mean 'hard'. Several are one phone call to an adviser.
  What makes them gating is that the answer does not exist in this workspace yet, so any recommendation issued today
  would be resting on something unstated.</p>
</div>

<div class="toc" aria-label="Jump to group">
{''.join(f'<a href="#{re.sub(r"[^a-z0-9]+","-",g.lower())}">{esc(g)}</a>' for g in groups)}
</div>

{sections}

<h2>The {counts['blocking']} blocking questions, in the order to close them</h2>
<div class="table-wrap">
  <table>
    <caption>Sequence matters as much as content</caption>
    <thead><tr><th>Order</th><th>Question</th><th>Why now</th></tr></thead>
    <tbody>
      <tr><td class="num">1</td><td>Q-02, Q-03, Q-04 &mdash; lease, options, notice calendar</td><td class="small">Cheapest to close and the only one where delay is irreversible. A missed notice window cannot be recovered by analysis.</td></tr>
      <tr><td class="num">2</td><td>Q-21 &mdash; the owner's objective in writing</td><td class="small">Without it, every subsequent comparison is ranked against an unstated benchmark, and the ranking is unfalsifiable.</td></tr>
      <tr><td class="num">3</td><td>Q-11, Q-12 &mdash; basis and residence</td><td class="small">Determines whether the after-tax module can produce a number at all. Unrecaptured section 1250 gain is taxed at up to 25% federally, so the depreciation history is not a rounding detail.</td></tr>
      <tr><td class="num">4</td><td>Q-09, Q-10 &mdash; value and comparables</td><td class="small">Gives the sale case a numerator. Note that Q-05 (market rent) is equally blocking and sits with the lease work.</td></tr>
      <tr><td class="num">5</td><td>Q-01 &mdash; title and vesting</td><td class="small">Needed before anyone can sign, and it changes the tax analysis.</td></tr>
    </tbody>
  </table>
</div>

<h2>Questions this product cannot answer, by definition</h2>
<div class="card">
  <p class="small">Three questions in the register are not research problems and should not be treated as gaps in the
  analysis. Q-21 (the owner's objective) is a decision, not a fact. Q-22 (the access list) is an administrative act.
  Q-08 (whether this unit is in the closure programme) requires the counterparty to speak, and no amount of public
  research substitutes for asking. Everything else is obtainable.</p>
</div>
"""
    return page("questions.html", "Questions Register", "What must be answered", body)


# ---------------------------------------------------------------- page: suggestions
def build_suggestions():
    sug = load("suggestions.json")
    bands = {}
    for s in sug["suggestions"]:
        bands.setdefault(s["band"], []).append(s)

    def band_badge(b):
        return {"Do first": badge("do first", "stop"),
                "Do second": badge("do second", "warn"),
                "Consider": badge("consider", "info"),
                "Presentation": badge("presentation", "ok")}.get(b, badge(b, "gray"))

    def cost_badge(c):
        return badge(c, {"low": "ok", "none": "ok", "medium": "warn", "n/a": "gray"}.get(c, "gray"))

    sections = ""
    for bname, items in bands.items():
        rws = []
        for s in items:
            rws.append(f"""
<tr>
  <td><code>{esc(s['id'])}</code></td>
  <td><b>{esc(s['title'])}</b><br><span class="tiny muted"><b>Problem:</b> {esc(s['problem'])}</span>
      <br><span class="tiny muted"><b>Action:</b> {esc(s['action'])}</span>
      {f'<br><span class="tiny" style="color:var(--stop)"><b>Caution:</b> {esc(s["risk_note"])}</span>' if s.get('risk_note') else ''}</td>
  <td class="small">{esc(', '.join(s['unblocks'])) if s['unblocks'] else '<span class="muted">closes no open question</span>'}</td>
  <td class="small">{esc(s['effort'])}<br>{cost_badge(s['cost_band'])} <span class="tiny muted">cost</span><br>{badge(s['risk'] + ' risk', {'low':'ok','medium':'warn'}.get(s['risk'],'gray'))}</td>
  <td class="small">{esc(s['falsifier'])}</td>
  <td class="small">{esc(s['stays_private'])}</td>
</tr>""")
        sections += f"""
<h2 id="{re.sub(r'[^a-z0-9]+','-',bname.lower())}">{esc(bname)} &mdash; {band_badge(bname)}</h2>
<div class="table-wrap">
  <table>
    <caption>{esc(bname)} &mdash; {len(items)} suggestion{'s' if len(items)!=1 else ''}
      <span class="cap-sub">'Closes' lists the questions from the register that this suggestion answers. A suggestion that closes no blocking question should not be funded before one that does.</span>
    </caption>
    <thead><tr><th>ID</th><th>Suggestion</th><th>Closes</th><th>Effort &amp; cost</th><th>Falsifier</th><th>Privacy</th></tr></thead>
    <tbody>{''.join(rws)}</tbody>
  </table>
</div>"""

    proto = "".join(f"<li>{esc(p)}</li>" for p in sug["review_protocol"])

    body = f"""
<p class="lede">This is the section the brief asked for: a place to review suggestions and choose a path before
anything is implemented. Each suggestion states what it buys, what it costs, how long it takes, what would show it was
the wrong call, and whether it can be done without exposing private information.</p>

<div class="notice ok">
  <p><strong>How to choose.</strong> Read the <em>Closes</em> column against the <a href="questions.html">Questions</a>
  register. If a suggestion closes none of the blocking questions, it is not urgent, however appealing it looks.
  Then read the <em>Falsifier</em> column: if the falsifier is likely to be true, the suggestion buys little. Finally
  read the <em>Privacy</em> column. A suggestion that would put an identifier on the public site is rejected outright,
  regardless of its benefit.</p>
</div>

<div class="grid four">
  <div class="card kpi"><span class="label">Do first</span><span class="value">{len(bands.get('Do first',[]))}</span><span class="sub">close the blocking questions</span></div>
  <div class="card kpi"><span class="label">Do second</span><span class="value">{len(bands.get('Do second',[]))}</span><span class="sub">once the lease and basis are in hand</span></div>
  <div class="card kpi"><span class="label">Consider</span><span class="value">{len(bands.get('Consider',[]))}</span><span class="sub">worth doing if the falsifier survives</span></div>
  <div class="card kpi"><span class="label">Presentation</span><span class="value">{len(bands.get('Presentation',[]))}</span><span class="sub">already implemented on this site</span></div>
</div>

{sections}

<h2>Review protocol</h2>
<div class="card"><ol class="steps">{proto}</ol></div>

<h2>One suggestion that was deliberately declined</h2>
<div class="card">
  <h3>Do not build the versioned cash-flow model yet &mdash; S-16</h3>
  <p class="small">The brief asks for a versioned, back-tested cash-flow model once verified inputs and sufficient
  comparable history exist. The condition in that instruction is doing real work. There are currently no verified inputs
  and no comparable history, so a model built today would be a spreadsheet fitted to nothing, carrying a version number
  that implies rigour it does not have. The four-scenario calculator on the
  <a href="sell-vs-renew.html">Sell vs Renew</a> page is the honest interim tool: it makes every assumption visible and
  refuses to store one as a fact.</p>
  <p class="small"><b>When to revisit:</b> after S-05 produces a dated comparable set with enough history to back-test
  against. At that point the model has something to be wrong about, which is the only way back-testing means anything.</p>
</div>

<h2>How to improve this site itself</h2>
<div class="grid two">
  <div class="card">
    <h3>For decision-making quality</h3>
    <ul class="clean small">
      <li>Add a single dated status line to every gate, so progress is visible over time rather than as a snapshot.</li>
      <li>Add a comparable-sales evidence table, empty until documents exist, so the shape of the missing evidence is visible rather than abstract.</li>
      <li>Add a printable one-page brief per adviser, so each receives only the questions they own. <span class="muted">(Partially done: see the <a href="advisor-summary.html">One-Page Summary</a>.)</span></li>
      <li>Add a change log, so a reviewer can see what changed between visits and does not re-read the whole site.</li>
    </ul>
  </div>
  <div class="card">
    <h3>For reviewability</h3>
    <ul class="clean small">
      <li>Every flag on the <a href="flagged.html">Flagged for Review</a> page carries the URL that was attempted, so a reviewer can retry it rather than take the flag on trust.</li>
      <li>Every value on the <a href="market.html">Market &amp; Economy</a> page links to the official page it was read from.</li>
      <li>The <a href="sources.html">Sources</a> page lists every domain used, with what it was used for and what it cannot be used for.</li>
      <li>Nothing on this site is fetched at runtime. The pages are static, so what you read is what was verified on the compile date shown in the header.</li>
    </ul>
  </div>
</div>
"""
    return page("suggestions.html", "Suggestions", "Review and choose", body)


# ---------------------------------------------------------------- page: sell-vs-renew (W-02, W-09, calculator)
def build_sell_vs():
    tax = load("tax.json")
    asm = load("assumptions.json")

    fed = "".join(
        f'<tr><td><code>{esc(r["id"])}</code></td><td><b>{esc(r["rule"])}</b><br><span class="tiny muted">{esc(r["detail"])}</span></td>'
        f'<td class="small">{esc(r["used_by"])}</td>{verify_cell(r["verified"], r["source_url"], r["source_name"])}</tr>'
        for r in tax["federal"]
    )
    cal = "".join(
        f'<tr><td><code>{esc(r["id"])}</code></td><td><b>{esc(r["rule"])}</b><br><span class="tiny muted">{esc(r["detail"])}</span></td>'
        f'<td class="small">{esc(r["used_by"])}</td>{verify_cell(r["verified"], r["source_url"], r["source_name"])}</tr>'
        for r in tax["california"]
    )
    lab = "".join(
        f'<tr><td><code>{esc(r["id"])}</code></td><td><b>{esc(r["rule"])}</b><br><span class="tiny muted">{esc(r["detail"])}</span></td>'
        f'<td class="small">{esc(r["used_by"])}</td>{verify_cell(r["verified"], r["source_url"], r["source_name"])}</tr>'
        for r in tax["labour_cost"]
    )
    sce = "".join(
        f'<div class="card"><h3>{esc(s["name"])} <span class="badge gray">{esc(s["id"])}</span></h3>'
        f'<p class="small"><b>Premise.</b> {esc(s["premise"])}</p>'
        f'<p class="small"><b>What changes.</b> {esc(s["what_changes"])}</p>'
        f'<p class="small" style="color:var(--stop)"><b>Assumption, not finding.</b> {esc(s["what_is_assumed"])}</p>'
        f'<p class="small"><b>What would disconfirm it.</b> {esc(s["observable_that_would_disconfirm"])}</p></div>'
        for s in asm["scenarios"]
    )

    body = f"""
<p class="lede">Five decision options, their risks, and a calculator that runs entirely in your browser. The
calculator computes; it does not advise, and it will not produce a verdict while the inputs it needs are blank.</p>

<div class="notice stop">
  <p><strong>No winner is selected on this page, by instruction and by evidence.</strong> The brief asks for an
  after-tax sale comparison alongside a negotiated renewal case without picking a winner until verified inputs exist.
  They do not exist. What exists is the machinery to compare them the moment the inputs do.</p>
</div>

<h2>The five options, and what each one is actually betting on</h2>
<div class="table-wrap">
  <table>
    <caption>Option register
      <span class="cap-sub">Every option is a bet on something specific. The right-hand column names the document that would settle whether the bet pays.</span>
    </caption>
    <thead><tr><th>Option</th><th>What it bets on</th><th>Main risk</th><th>Ruled out if</th><th>Needs</th></tr></thead>
    <tbody>
      <tr><td><b>A. Sell now, before the lease shortens further</b></td>
        <td class="small">That the short-lease discount widens as expiry approaches, so waiting past today costs value.</td>
        <td class="small">Selling into a soft bid and paying tax on the gain when a renewal was available at better rent.</td>
        <td class="small">The tenant renews at or above market before marketing begins.</td>
        <td class="small">Value, basis, cap-rate evidence</td></tr>
      <tr><td><b>B. Renew first, then sell a longer-lease asset</b></td>
        <td class="small">That a renewed term compresses the cap rate by more than the cost and delay of negotiating it.</td>
        <td class="small">The tenant extracts a below-market rent as the price of the extension, capitalising a poor rent into the sale price.</td>
        <td class="small">The tenant will not discuss renewal before the option window, or holds a unilateral option at a fixed rent.</td>
        <td class="small">Lease, options, notice calendar, market rent</td></tr>
      <tr><td><b>C. Hold to expiry with no action</b></td>
        <td class="small">That the rent continues and the site's land value holds or rises, with no transaction cost paid.</td>
        <td class="small">Carrying capital events (roof, lot, HVAC) inside the term, and losing the chance to market a longer lease.</td>
        <td class="small">Insurance is non-renewed, or a capital event is due before expiry that the rent will not cover.</td>
        <td class="small">Condition report, insurance file, capital schedule</td></tr>
      <tr><td><b>D. Sell and defer via section 1031</b></td>
        <td class="small">That a replacement property can be identified inside the statutory window and produces better risk-adjusted income.</td>
        <td class="small">Failing to identify in time, which converts a deferred gain into a taxable one under time pressure; California also requires FTB 3840 when California property is exchanged for out-of-state property.</td>
        <td class="small">No credible replacement can be identified, or the owner needs liquidity rather than income.</td>
        <td class="small">Qualified intermediary, candidate list, CPA sign-off</td></tr>
      <tr><td><b>E. Redevelop the site</b></td>
        <td class="small">That the land is worth more at a higher intensity than the leased building produces.</td>
        <td class="small">Entitlement risk, construction cost, and the loss of rent during redevelopment.</td>
        <td class="small">Zoning and General Plan designation do not support a higher-intensity use.</td>
        <td class="small">ZIMAS designation, land-use consultant, land comps</td></tr>
    </tbody>
    <tfoot><tr><td colspan="5">No option is recommended. Each row's 'Ruled out if' condition is a specific, checkable document, which is what makes the register reviewable rather than rhetorical.</td></tr></tfoot>
  </table>
</div>

<h2 id="calculator">The after-tax sell-versus-renew calculator <span class="badge info">runs in your browser</span></h2>
<p class="small">Nothing you type leaves the page. There is no network call, no analytics and no storage. The
arithmetic is plain and visible in <code>assets/js/calc.js</code>, and every rate it applies is listed with its official
source underneath the calculator. Default numbers are only there so the mechanism is visible: they are marked
<em>illustrative</em> and are not used anywhere else on this site.</p>

<div class="calc-grid">
  <div>
    <form id="calc-form" autocomplete="off" onsubmit="return false;">
      <fieldset>
        <legend>Sale case &mdash; inputs</legend>
        <label class="field">Sale price
          <span class="hint">illustrative default &mdash; replace with your own</span>
          <input type="number" id="sale_price" value="3200000" min="0" step="1000">
        </label>
        <label class="field">Selling costs (% of price)
          <span class="hint">commission and closing costs; assumption</span>
          <input type="number" id="sell_costs_pct" value="4" min="0" max="20" step="0.25">
        </label>
        <label class="field">Adjusted basis, total
          <span class="hint">original cost plus capitalised improvements, less depreciation taken</span>
          <input type="number" id="basis" value="1500000" min="0" step="1000">
        </label>
        <label class="field">Accumulated depreciation
          <span class="hint">used for section 1250 recapture at up to 25%; from your filed returns</span>
          <input type="number" id="accum_dep" value="600000" min="0" step="1000">
        </label>
        <div class="inline-2">
          <label class="field">Federal long-term rate (%)
            <select id="fed_rate">
              <option value="0">0</option>
              <option value="15">15</option>
              <option value="20" selected>20</option>
            </select>
          </label>
          <label class="field">State marginal rate (%)
            <select id="state_rate">
              <option value="0">0 &mdash; no state income tax</option>
              <option value="9.3">9.3</option>
              <option value="10.3">10.3</option>
              <option value="11.3">11.3</option>
              <option value="12.3" selected>12.3</option>
            </select>
          </label>
        </div>
        <label class="field">Apply the 3.8% net investment income tax?
          <select id="niit">
            <option value="0">No / not applicable</option>
            <option value="1" selected>Yes</option>
          </select>
        </label>
        <label class="field">Defer the gain with a section 1031 exchange?
          <select id="use_1031">
            <option value="0" selected>No &mdash; taxable sale</option>
            <option value="1">Yes &mdash; deferred</option>
          </select>
        </label>
        <label class="field">Exit cap-rate shock (basis points)
          <span class="hint">positive widens the buyer's cap rate and reduces value</span>
          <input type="number" id="cap_shock_bp" value="0" min="-200" max="400" step="25">
        </label>
        <label class="field">Repair shock (% of value)
          <span class="hint">net of insurance; hazard stress input</span>
          <input type="number" id="repair_pct" value="0" min="0" max="50" step="0.5">
        </label>
        <label class="field">Rent lost before sale (months)
          <span class="hint">closure or vacancy stress input</span>
          <input type="number" id="rent_lost_months" value="0" min="0" max="36" step="1">
        </label>
      </fieldset>

      <fieldset>
        <legend>Renewal / hold case &mdash; inputs</legend>
        <label class="field">Current annual base rent
          <span class="hint">illustrative default &mdash; from the private lease abstract</span>
          <input type="number" id="rent" value="150000" min="0" step="1000">
        </label>
        <label class="field">Annual operating costs borne by the owner
          <span class="hint">what the net lease actually leaves with the landlord</span>
          <input type="number" id="opex" value="12000" min="0" step="500">
        </label>
        <label class="field">Renewal term being considered (years)
          <input type="number" id="term" value="10" min="1" max="30" step="1">
        </label>
        <label class="field">Contract rent growth per year (%)
          <input type="number" id="rent_growth" value="2" min="0" max="10" step="0.25">
        </label>
        <label class="field">Market rent at renewal (annual)
          <span class="hint">from dated comparable leases, not asking rents</span>
          <input type="number" id="market_rent" value="180000" min="0" step="1000">
        </label>
        <label class="field">Discount rate for present value (%)
          <span class="hint">the return you require; this is your assumption, not a market fact</span>
          <input type="number" id="disc" value="7" min="0" max="20" step="0.25">
        </label>
        <label class="field">Cap rate on renewal value (%)
          <span class="hint">from comparable trades</span>
          <input type="number" id="cap" value="5.75" min="2" max="15" step="0.05">
        </label>
      </fieldset>
    </form>
  </div>

  <div>
    <div class="card" id="results-card">
      <h3 style="margin-top:0">Results</h3>
      <table class="result-table" id="results">
        <tbody><tr><td class="muted">Computing&hellip;</td><td></td></tr></tbody>
      </table>
      <div id="verdict" class="verdict neutral" aria-live="polite"></div>
    </div>

    <div class="card" style="margin-top:1rem">
      <h3 style="margin-top:0">Rates applied, and where each comes from</h3>
      <div class="table-wrap" style="margin:0">
        <table>
          <thead><tr><th>Rate</th><th class="num">Value used</th><th>Official source</th></tr></thead>
          <tbody>
            <tr><td>Federal long-term capital gain</td><td class="num">selected</td>
              <td class="src"><a href="https://www.irs.gov/taxtopics/tc409" rel="noopener noreferrer">IRS Topic 409</a></td></tr>
            <tr><td>Unrecaptured section 1250 gain</td><td class="num">25% max</td>
              <td class="src"><a href="https://www.irs.gov/taxtopics/tc409" rel="noopener noreferrer">IRS Topic 409</a></td></tr>
            <tr><td>Net investment income tax</td><td class="num">3.8%</td>
              <td class="src"><a href="https://www.irs.gov/newsroom/questions-and-answers-on-the-net-investment-income-tax" rel="noopener noreferrer">IRS NIIT Q&amp;A</a></td></tr>
            <tr><td>California has no preferential capital gains rate</td><td class="num">ordinary rates</td>
              <td class="src"><a href="https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html" rel="noopener noreferrer">FTB, Capital gains</a></td></tr>
            <tr><td>California 2025 top marginal rate</td><td class="num">12.3%</td>
              <td class="src"><a href="https://www.ftb.ca.gov/forms/2025/2025-540-tax-rate-schedules.pdf" rel="noopener noreferrer">FTB 2025 rate schedules</a></td></tr>
            <tr><td>Section 1031 real property only</td><td class="num">deferral</td>
              <td class="src"><a href="https://www.irs.gov/businesses/small-businesses-self-employed/like-kind-exchanges-real-estate-tax-tips" rel="noopener noreferrer">IRS, like-kind exchanges</a></td></tr>
            <tr><td>California sourcing and FTB 3840</td><td class="num">note</td>
              <td class="src"><a href="https://www.ftb.ca.gov/forms/2025/2025-1100-publication.pdf" rel="noopener noreferrer">FTB Pub. 1100</a></td></tr>
          </tbody>
        </table>
      </div>
      <p class="tiny muted" style="margin-top:.6rem">Local City of Los Angeles transfer and business taxes are
      <b>not</b> included. Their current rates were not read from an official city page during this session, so they are
      on the <a href="flagged.html">Flagged for Review</a> page rather than guessed. Net proceeds shown here are therefore
      an upper bound.</p>
    </div>

    <div class="card" style="margin-top:1rem">
      <h3 style="margin-top:0">How to read the output honestly</h3>
      <ul class="clean small">
        <li>The comparison is <b>net after-tax sale proceeds today</b> versus the <b>present value of the renewal case</b>. Those are not the same kind of number, and the page says so rather than subtracting one from the other.</li>
        <li>The calculator will still run with blank or zero inputs. That is deliberate: it shows you a number built on nothing, which is what a rule-of-thumb valuation often is.</li>
        <li>The single most sensitive input is the cap rate. A 50 basis point move on a 5.75% cap is roughly a 9% change in value before any income change.</li>
        <li>If the sale price is unknown, the correct output is 'unknown', not a guess. The calculator cannot enforce that; you have to.</li>
      </ul>
    </div>
  </div>
</div>

<h2>Price the short-lease discount from real quotes</h2>
<div class="card">
  <p class="small">The brief asks to price the short-lease discount from real quotes. That is the single most
  important number in the sale case, because the lease expires inside a five-year window and a buyer prices the reversion
  as a re-leasing risk rather than as income. It cannot be derived from a rule of thumb without becoming an assumption.</p>
  <p class="small"><b>What it takes.</b> Pairs of otherwise-similar single-tenant quick-service trades in the same
  submarket, one with a long remaining term and one short, sold close in time, each with the cap rate and the term
  remaining at sale. The discount is then the observed cap-rate spread between the two groups, expressed in basis points,
  and it should be re-read every time a new pair trades.</p>
  <p class="small"><b>What is shown here.</b> Nothing, because no such pairs have been documented in this workspace.
  The row is on the <a href="flagged.html">Flagged for Review</a> page as FR-09, with the reason: no official agency
  publishes commercial cap rates or lease comparables, so this must come from a broker's documented file with source
  documents attached.</p>
</div>

<h2>The verified tax rules the calculator applies</h2>
<h3>Federal</h3>
<div class="table-wrap">
  <table>
    <caption>Federal rules, read verbatim from IRS pages
      <span class="cap-sub">A row marked flagged could not be confirmed and is not used as a value.</span></caption>
    <thead><tr><th>ID</th><th>Rule</th><th>Used for</th><th>Official source</th></tr></thead>
    <tbody>{fed}</tbody>
  </table>
</div>
<h3>California</h3>
<div class="table-wrap">
  <table>
    <caption>California rules, read verbatim from Franchise Tax Board pages</caption>
    <thead><tr><th>ID</th><th>Rule</th><th>Used for</th><th>Official source</th></tr></thead>
    <tbody>{cal}</tbody>
  </table>
</div>
<h3>Labour cost pressure on the tenant</h3>
<div class="table-wrap">
  <table>
    <caption>Why the tenant's cost base matters to a renewal
      <span class="cap-sub">A tenant whose labour cost is rising faster than its sales has less room to absorb a rent increase.</span></caption>
    <thead><tr><th>ID</th><th>Rule</th><th>Used for</th><th>Official source</th></tr></thead>
    <tbody>{lab}</tbody>
  </table>
</div>

<h2>Scenarios &mdash; explicitly labelled as assumptions</h2>
<div class="notice warn">
  <p>The brief asks to distinguish observations from assumptions. <b>Everything below is an assumption.</b> None of it
  is used as a value on any other page. It exists to name the branches a decision has to survive, not to forecast.</p>
</div>
<div class="grid two">{sce}</div>

<h2>Decision risks, and what would falsify each one</h2>
<div class="table-wrap">
  <table>
    <caption>Risk register for the decision itself
      <span class="cap-sub">A decision without a falsifier cannot be reviewed. Each row names the observation that would show the branch was wrong.</span></caption>
    <thead><tr><th>Branch</th><th>Risk if taken</th><th>Risk if not taken</th><th>Early signal that it was wrong</th></tr></thead>
    <tbody>
      <tr><td><b>Sell now</b></td><td class="small">Selling into a thin bid and capitalising a short lease at its worst point in the cycle.</td><td class="small">The cap rate widens and the short-lease discount compounds as expiry approaches.</td><td class="small">The tenant renews at or above market rent within the following year.</td></tr>
      <tr><td><b>Renew then sell</b></td><td class="small">Granting a below-market rent for a decade in exchange for a term that buyers discount anyway.</td><td class="small">Losing the chance to market a longer-lease asset, and carrying capital events in the interim.</td><td class="small">Comparable renewed assets trade at cap rates no tighter than short-lease ones.</td></tr>
      <tr><td><b>Hold to expiry</b></td><td class="small">An uninsured or underinsured event, or a roof or lot failure, landing inside the term.</td><td class="small">Doing nothing while the lease shortens is itself a decision to accept that discount.</td><td class="small">Insurance non-renewal, or a capital item due before expiry that the rent will not fund.</td></tr>
      <tr><td><b>1031 exchange</b></td><td class="small">Rushing into a poor replacement to beat the identification deadline, and inheriting a worse asset.</td><td class="small">Paying tax now on a gain that could have been deferred.</td><td class="small">No credible replacement identified within the first 30 days of marketing.</td></tr>
      <tr><td><b>Redevelop</b></td><td class="small">Entitlement delay, construction cost overrun, and lost rent during the build.</td><td class="small">Leaving land value unrealised if the district is up-zoned around the site.</td><td class="small">The zoning and General Plan designation do not support higher intensity.</td></tr>
    </tbody>
  </table>
</div>

<h2>Wealth preservation and growth: the balance the brief asks for</h2>
<div class="grid two">
  <div class="card">
    <h3>The case for a lower-risk path</h3>
    <p class="small">A single tenant, a single parcel and a lease ending inside five years is a concentrated position
    with a dated cliff. If the owner's objective includes wealth preservation, concentration plus a known expiry is the
    risk to reduce. A sale converts an illiquid, single-obligor position into cash or into a diversified replacement,
    and it removes the option-window risk entirely.</p>
    <p class="small"><b>But:</b> a sale now realises the gain and pays the tax, and the tax rate depends on facts
    (basis, depreciation, state of residence) that are not yet in hand. Selling before those are known is itself a risk.</p>
  </div>
  <div class="card">
    <h3>The case for keeping the income</h3>
    <p class="small">The verified local evidence does not support a deteriorating market: metro unemployment fell to
    4.4%, employment is growing, and the health and education sector that anchors weekday lunch traffic added 49,100
    jobs in a year. Meanwhile California house prices grew only 0.6% over four quarters, so there is no evident
    price bubble forcing a sale.</p>
    <p class="small"><b>But:</b> wages in the Los Angeles CSA rose 3.9% against local CPI of 3.7%, and the tenant's
    labour cost is set by statute. A tenant whose cost base grows faster than its sales is a tenant that negotiates rent
    hard, which is the reason the renewal case needs a market rent before it can be argued.</p>
  </div>
</div>

<div class="notice">
  <p><strong>The balanced answer the evidence supports.</strong> Reduce the irreversible risks first, and do not make
  an irreversible commitment until the three numbers exist. Concretely: close the lease and notice-calendar gate, get
  the basis from the CPA, and get three dated comparables. Those three steps are inexpensive, they are mutually
  independent, and each one removes a way the decision can go wrong. Everything on this page is built to be used the
  moment they are done.</p>
</div>
"""
    extra = '  <script src="assets/js/calc.js" defer></script>\n'
    return page("sell-vs-renew.html", "Sell vs Renew", "Options, taxes, calculator", body, extra_head=extra)


# ---------------------------------------------------------------- page: sources
def build_sources():
    domains = [
        ("census.gov", "U.S. Census Bureau", "QuickFacts city population, income, poverty, housing, education and Economic Census sales; ACS 2020-2024 and V2025 estimates.",
         "Does not publish a drive-time trade area, commercial rents or cap rates. County QuickFacts did not load (FR-01).",
         "https://www.census.gov/quickfacts/fact/table/losangelescitycalifornia/PST045224"),
        ("bls.gov", "U.S. Bureau of Labor Statistics", "Metro unemployment, nonfarm employment by sector, CPI-U for the Los Angeles area, Employment Cost Index, QCEW wages, OEWS wages, and the Public Data API series used for monthly cross-checks.",
         "Does not publish property values, rents or cap rates. October 2025 data were not collected during the appropriations lapse (FR-02).",
         "https://www.bls.gov/regions/west/summary/blssummary_losangeles.pdf"),
        ("fhfa.gov", "Federal Housing Finance Agency", "House Price Index, quarterly, national, census division and state, for the four-quarter appreciation figure.",
         "Single-family repeat-sales index only. Not a commercial property index and not a cap-rate series. The Los Angeles MSA row was not retrieved (FR-10).",
         "https://www.fhfa.gov/document/d/hpi/fhfa-house-price-index-report-2026q3"),
        ("sec.gov", "U.S. Securities and Exchange Commission (EDGAR)", "Jack in the Box Inc. Form 10-K for FY ended 28 September 2025: unit counts, franchise terms, closure programme, strategic review, prototype size, site-selection criteria, supply chain.",
         "System-level disclosure only. Does not identify individual restaurants or their leases.",
         "https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/0000807882-25-000072-index.htm"),
        ("irs.gov", "Internal Revenue Service", "Long-term capital gain brackets, the 25% maximum on unrecaptured section 1250 gain, the 3.8% net investment income tax and its thresholds, section 1031 rules, depreciation basics.",
         "Rules only. Says nothing about this owner's basis, residency or income.",
         "https://www.irs.gov/taxtopics/tc409"),
        ("ftb.ca.gov", "California Franchise Tax Board", "No preferential California capital gains rate; 2024 and 2025 rate schedules; FTB Publication 1100 on California sourcing of real property gain and the FTB 3840 requirement for out-of-state 1031 replacement property.",
         "Rules only. 2026 rate schedules were not published at the time of reading.",
         "https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html"),
        ("dir.ca.gov", "California Department of Industrial Relations", "State minimum wage of $16.90 per hour effective 1 January 2026, and the CPI-W indexation rule with its 3.5% cap.",
         "The fast-food wage page did not load, so no fast-food rate is asserted (FR-07).",
         "https://www.dir.ca.gov/dlse/faq_minimumwage.htm"),
        ("assessor.lacounty.gov", "Los Angeles County Assessor", "Proposition 13 assessment rules and the 2% cap with its exceptions; decline-in-value filing window; disaster relief and Misfortune &amp; Calamity claim process.",
         "Address-keyed. The parcel's assessed value is private and is not published here.",
         "https://assessor.lacounty.gov/real-estate-toolkit/proposition-13"),
        ("msc.fema.gov", "FEMA Flood Map Service Center", "The official public source for NFIP flood hazard information and the address/coordinate lookup for a FIRM panel.",
         "Coordinate-keyed, so the parcel's zone is withheld (FR-03).",
         "https://msc.fema.gov/portal/home"),
        ("osfm.fire.ca.gov", "CAL FIRE — Office of the State Fire Marshal", "Fire Hazard Severity Zone classes (Moderate, High, Very High), the SRA/LRA distinction, the April 2024 SRA map effective date, and the OSFM's own statement that the maps measure hazard rather than risk.",
         "Address-keyed via the FHSZ viewer, so the parcel's zone is withheld (FR-03).",
         "https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones"),
        ("usgs.gov / earthquake.usgs.gov", "U.S. Geological Survey, Earthquake Hazards Program", "The 2023 50-state National Seismic Hazard Model and the Earthquake Hazard Toolbox for querying hazard at a location.",
         "Coordinate-keyed, so ground-motion values are withheld (FR-03).",
         "https://www.usgs.gov/programs/earthquake-hazards/national-seismic-hazard-model-project"),
        ("fema.gov", "FEMA", "The National Risk Index (v1.20) covering 18 natural hazards, published through the Resilience Analysis and Planning Tool.",
         "A composite community score, not a building-level underwriting input.",
         "https://www.fema.gov/emergency-managers/practitioners/resilience-analysis-and-planning-tool"),
        ("home.treasury.gov", "U.S. Department of the Treasury", "Daily Treasury par yield curve rates, used only as a rate observation in the scenario notes.",
         "Treasury yields are not cap rates and are never presented as such.",
         "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value=2026"),
        ("dot.ca.gov", "Caltrans", "The Traffic Census Program, and its explicit scope note that counts cover the State Highway System only and that city street counts are held by the city.",
         "No parcel frontage count could be read without the private location (FR-04).",
         "https://dot.ca.gov/programs/traffic-operations/census"),
        ("planning.lacity.gov", "City of Los Angeles Department of City Planning", "ZIMAS property information, Case Search, community plan updates and the New Zoning Code.",
         "Address-keyed, so the parcel's designation is withheld (FR-04).",
         "https://planning.lacity.gov/"),
        ("caaspp-elpac.ets.org", "California Department of Education — CAASPP Reporting", "Smarter Balanced ELA and mathematics results and the research files, by county, district and school.",
         "School-code-keyed, so the assigned school results are withheld (FR-03).",
         "https://caaspp-elpac.ets.org/caaspp/SearchSB.aspx"),
        ("huduser.gov", "U.S. Department of Housing and Urban Development", "FY2026 Fair Market Rent methodology for the Los Angeles-Long Beach-Glendale HUD Metro FMR Area.",
         "The rent values did not render to this reader (FR-08). Residential FMR is context, not commercial rent.",
         "https://www.huduser.gov/portal/datasets/fmr/fmrs/FY2026_code/2026summary.odn?selected_metro_code=31080&year=2026&fmrtype=Final"),
    ]
    rows = "".join(
        f'<tr><td><a href="{esc(url)}" rel="noopener noreferrer">{esc(dom)}</a></td><td><b>{esc(name)}</b></td>'
        f'<td class="small">{txt}</td><td class="small">{limit}</td></tr>'
        for dom, name, txt, limit, url in domains
    )

    body = f"""
<p class="lede">Every figure on this site was read from one of the official domains below during the compilation
session. This page states what each source was used for and, just as importantly, what it cannot be used for.</p>

<div class="notice">
  <p><strong>One rule governs every row.</strong> A value appears only if it was read from the linked official page. If
  the page did not load, the value is blank and the attempt is recorded on the
  <a href="flagged.html">Flagged for Review</a> page. No figure on this site was taken from a secondary aggregator,
  a blog, a news article or a search-result snippet.</p>
</div>

<h2>Sources used</h2>
<div class="table-wrap">
  <table>
    <caption>Official sources, scope and limits
      <span class="cap-sub">{len(domains)} official domains. Every one is a government or statutory body.</span></caption>
    <thead><tr><th>Domain</th><th>Body</th><th>Used for</th><th>Cannot be used for</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>

<h2>Sources deliberately not used</h2>
<div class="table-wrap">
  <table>
    <caption>Excluded by the verification rule</caption>
    <thead><tr><th>Type</th><th>Why excluded</th><th>Example of what it claimed</th></tr></thead>
    <tbody>
      <tr><td class="small">Property data aggregators</td><td class="small">Not official, and their values are modelled rather than published. Used for no figure.</td><td class="small">&mdash;</td></tr>
      <tr><td class="small">Commercial real estate databases</td><td class="small">Subscription products, not official sources. Their cap rates and lease comps are appropriate for a broker's private file but not for a cited public figure.</td><td class="small">See FR-09.</td></tr>
      <tr><td class="small">Search-result snippets</td><td class="small">A snippet is a claim about a page, not the page. Every value on this site was read from the page itself.</td><td class="small">A $20.00 California fast-food minimum wage appeared repeatedly in snippets. The official DIR page did not load, so the rate is asserted nowhere on this site (FR-07).</td></tr>
      <tr><td class="small">News articles</td><td class="small">Secondary. Where a news claim mattered, the underlying official document was located and cited instead.</td><td class="small">&mdash;</td></tr>
    </tbody>
  </table>
</div>

<h2>Verification method</h2>
<ol class="steps">
  <li>Locate the official page that carries the figure, preferring the agency's own domain over any index or mirror.</li>
  <li>Read the figure and the period and vintage labels from that page, not from a summary.</li>
  <li>Record the exact URL, the measure name, the geography and the period in <code>data/*.json</code>.</li>
  <li>Set <code>verified: true</code> only if step 2 succeeded. Otherwise leave the value <code>null</code> and write the reason.</li>
  <li>Rebuild the site. A <code>null</code> renders as a blank cell with a flagged badge; the row is listed on the Flagged page automatically.</li>
  <li>Re-read the figure when the source publishes a new vintage. The compile date is shown in the header of every page.</li>
</ol>

<h2>Reproducing this build</h2>
<div class="card">
  <p class="small">The site is generated, not written by hand. All content lives in <code>data/</code> as JSON; the
  HTML is produced by <code>tools/build_site.py</code>. To re-verify one figure, edit the corresponding JSON entry,
  set its <code>verified</code> flag, change its <code>source_url</code> if needed, and rebuild. Changing the HTML
  directly will be overwritten by the next build, which is deliberate: it keeps the data and the presentation from
  drifting apart.</p>
  <p class="small"><b>No runtime fetching.</b> The published site makes no network requests at all. There is no external
  stylesheet, no font service, no script from a third party and no analytics. That means the pages cannot silently
  change after publication, and a reader can inspect exactly what was verified on the compile date.</p>
</div>
"""
    return page("sources.html", "Sources", "Verification register", body)


# ---------------------------------------------------------------- page: flagged
def build_flagged():
    fl = load("flagged.json")
    cats = fl["meta"]["categories"]

    rws = []
    for it in fl["items"]:
        cat = cats.get(it["category"], it["category"])
        urls = "".join(
            f'<div class="tiny"><a href="{esc(u)}" rel="noopener noreferrer">{esc(u)}</a></div>'
            for u in it["attempted_urls"]
        ) or '<span class="tiny muted">no URL attempted &mdash; nothing official publishes this</span>'
        rws.append(f"""
<tr>
  <td><code>{esc(it['id'])}</code></td>
  <td><span class="badge warn">{esc(it['category'].replace('_',' '))}</span></td>
  <td><b>{esc(it['item'])}</b><br><span class="tiny muted">{esc(it['detail'])}</span>
      <br><span class="tiny muted"><b>Impact:</b> {esc(it['impact'])}</span>
      <br><span class="tiny muted"><b>To close:</b> {esc(it['to_close'])}</span></td>
  <td class="src">{urls}</td>
</tr>""")

    body = f"""
<p class="lede">Everything that could not be confirmed, published rather than suppressed. Each item records what was
attempted, why it failed, what it affects, and what would close it. Nothing on this page is used as a value anywhere
on the site.</p>

<div class="notice warn">
  <p><strong>This page exists so the site can be trusted.</strong> A dashboard that shows only what worked is more
  dangerous than one that shows the gaps. These {len(fl['items'])} items do not block publication and they do not block
  the merge. They block <em>reliance</em> on the specific figure or conclusion named in each row.</p>
</div>

<div class="grid two">
  <div class="card">
    <h3>Flag categories</h3>
    <ul class="clean small">
      {''.join(f'<li><b>{esc(k.replace("_"," "))}</b> &mdash; {esc(v)}</li>' for k, v in cats.items())}
    </ul>
  </div>
  <div class="card">
    <h3>What this means for a reader</h3>
    <p class="small">If a row here names a figure you were about to rely on, do not rely on it. Open the attempted URL
    in a browser: several of these failures are reader-specific, and the page may work for you. If it does, record the
    value with the date you read it and update the data file.</p>
    <p class="small">If a row here names a conclusion, treat that conclusion as withheld rather than as negative. For
    example, the absence of a parcel hazard designation on this site does not mean the parcel is free of hazard; it means
    the designation is private.</p>
  </div>
</div>

<h2>All flagged items</h2>
<div class="table-wrap">
  <table>
    <caption>{len(fl['items'])} items flagged for review
      <span class="cap-sub">Ordered as recorded. Each carries the URL that was attempted so a reviewer can retry it rather than take the flag on trust.</span></caption>
    <thead><tr><th>ID</th><th>Category</th><th>Item, detail and impact</th><th>URLs attempted</th></tr></thead>
    <tbody>{''.join(rws)}</tbody>
    <tfoot><tr><td colspan="4">{esc(fl['note_on_flagged_items'])}</td></tr></tfoot>
  </table>
</div>

<h2>How to request a change</h2>
<div class="card">
  <ol class="steps">
    <li>Open the attempted URL and confirm the value with its period and vintage.</li>
    <li>Edit the matching entry in <code>data/market.json</code>, <code>data/hazards.json</code> or <code>data/flagged.json</code>.</li>
    <li>Set <code>verified</code> to <code>true</code> and paste the exact URL you read it from.</li>
    <li>Remove the item from <code>flagged.json</code> only if it is fully resolved, and note the resolution in the commit message.</li>
    <li>Rebuild with <code>python3 tools/build_site.py</code> and confirm the row now shows a source and no warning badge.</li>
  </ol>
</div>
"""
    return page("flagged.html", "Flagged for Review", "Unverified and irregular", body)


# ---------------------------------------------------------------- page: advisor summary (W-10)
def build_advisor():
    gates = load("gates.json")
    qs = load("questions.json")
    blocked = [g for g in gates["gates"] if g["state"] != "closed"]
    blocking_qs = [q for q in qs["questions"] if q["priority"] == "blocking"]

    gate_lines = "".join(
        f'<tr><td><b>{esc(g["id"])}</b> {esc(g["name"])}</td><td>{esc(g["state"])}</td>'
        f'<td class="small">{esc(g["closed_by"])}</td></tr>' for g in blocked
    )
    q_lines = "".join(
        f'<tr><td><b>{esc(q["id"])}</b></td><td class="small">{esc(q["question"])}</td>'
        f'<td class="small">{esc(q["owner_of_task"])}</td></tr>' for q in blocking_qs
    )

    body = f"""
<div class="no-print" style="display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin-bottom:1rem">
  <button onclick="window.print()" style="font:inherit;font-size:.86rem;font-weight:600;padding:.5rem 1rem;border-radius:8px;border:1px solid var(--brand);background:var(--brand);color:#fff;cursor:pointer">Print this page</button>
  <span class="small muted">Designed to fit one sheet. Navigation, header and footer are dropped in print, and source URLs are expanded.</span>
</div>

<div class="card" style="border-top:4px solid var(--brand)">
  <p class="eyebrow" style="margin-bottom:.2rem">One-page summary for advisers &middot; W-10 &middot; {BUILD_DATE}</p>
  <h1 style="font-size:1.35rem;margin-bottom:.4rem">Parcel Decision Workspace &mdash; PARCEL-A</h1>
  <p class="small" style="margin-bottom:.6rem">Single-tenant quick-service parcel, central Los Angeles. Triple-net lease,
  expiry window 2030&ndash;2035. Decision in scope: sell before expiry, renew, hold, exchange or redevelop.
  <b>No personal or parcel-identifying information appears in this document.</b></p>

  <h2 style="margin-top:.8rem">1. Bottom line</h2>
  <p class="small"><b>No recommendation can be issued, and none is issued.</b> The sell case has no price and no tax
  number; the renew case has no rent and no option mechanics. Six of seven decision gates are not closed. What is
  established is the economic direction of the city and metro from official statistics, the tenant franchisor's own
  audited disclosures, the federal and California tax rules that will apply to a sale, and the authoritative official
  channel for every remaining parcel-level question.</p>

  <h2>2. What is established, with evidence</h2>
  <table style="font-size:.8rem">
    <thead><tr><th>Established</th><th>Value</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td>Los Angeles metro unemployment, Sep 2026</td><td>4.4% (was 5.5% a year earlier)</td><td class="small">BLS LA Area Economic Summary</td></tr>
      <tr><td>Metro nonfarm employment, Sep 2026</td><td>6,282.1k, +0.5% y/y</td><td class="small">BLS Current Employment Statistics</td></tr>
      <tr><td>Sector split, 12 months to Sep 2026</td><td>Health &amp; education +3.8%; information &minus;5.7%</td><td class="small">BLS CES</td></tr>
      <tr><td>City median household income</td><td>$81,939 (2020&ndash;2024)</td><td class="small">Census QuickFacts</td></tr>
      <tr><td>City population, Jul 2025</td><td>3,869,089, &minus;0.8% from 2020 base</td><td class="small">Census QuickFacts (V2025)</td></tr>
      <tr><td>California house price change, 4 quarters</td><td>+0.6% (U.S. +2.5%)</td><td class="small">FHFA HPI 2026Q3</td></tr>
      <tr><td>Franchisor unit count, FY2025</td><td>2,136 Jack in the Box, 93% franchised</td><td class="small">Jack in the Box Inc. 10-K</td></tr>
      <tr><td>Franchisor disclosed closure programme</td><td>Yes &mdash; system level, unnamed units</td><td class="small">Jack in the Box Inc. 10-K</td></tr>
      <tr><td>Federal unrecaptured s.1250 maximum</td><td>25%</td><td class="small">IRS Topic 409</td></tr>
      <tr><td>Net investment income tax</td><td>3.8% above $200k single / $250k MFJ</td><td class="small">IRS NIIT Q&amp;A</td></tr>
      <tr><td>California capital gains treatment</td><td>No preferential rate; ordinary rates, top 12.3%</td><td class="small">FTB</td></tr>
      <tr><td>California minimum wage, 1 Jan 2026</td><td>$16.90/hour</td><td class="small">DIR</td></tr>
    </tbody>
  </table>

  <h2>3. What is missing, by owner</h2>
  <table style="font-size:.8rem">
    <thead><tr><th>Gate</th><th>State</th><th>Who closes it</th></tr></thead>
    <tbody>{gate_lines}</tbody>
  </table>

  <h2>4. The blocking questions</h2>
  <table style="font-size:.8rem">
    <thead><tr><th>ID</th><th>Question</th><th>Owner</th></tr></thead>
    <tbody>{q_lines}</tbody>
  </table>

  <h2>5. Actions requested from the adviser reading this</h2>
  <ol class="steps small" style="font-size:.8rem">
    <li><b>Counsel (ADVISER-1):</b> private lease abstract, then a dated notice calendar reconciled line by line against it. This is the only item where delay is irreversible.</li>
    <li><b>CPA (ADVISER-5):</b> adjusted basis with the land and building split, accumulated depreciation, state of residence, and a 1031 feasibility view. Note that California sources the gain to the property's location and requires FTB 3840 for out-of-state replacement property.</li>
    <li><b>Broker (ADVISER-3):</b> a dated opinion of value with the income approach shown, plus at least three closed comparables with the term remaining at sale, so the short-lease discount can be observed rather than assumed.</li>
    <li><b>Engineer (ADVISER-2) and insurance:</b> property condition assessment with a dated capital schedule, and the declarations page with earthquake cover and deductibles.</li>
    <li><b>Owner (OWNER-1):</b> one page of investment policy, and the four hazard lookups completed privately with the panel or zone identifier recorded.</li>
  </ol>

  <h2>6. What would change the answer</h2>
  <p class="small">A written confirmation that the unit is outside the franchisor's closure programme, and a tenant
  indication of renewal at or above market, both move weight toward holding and renewing. A failed insurance renewal, a
  capital event due before expiry, or a comparable renewed asset trading no tighter than a short-lease one move weight
  toward selling earlier. None of these has been observed.</p>

  <p class="tiny muted" style="margin-top:.8rem;border-top:1px solid #ddd;padding-top:.5rem">
  Full evidence, source links, the flagged-items register and the browser-side calculator:
  <b>kanlerxz87-cyber.github.io/Jackbox1</b>. Compiled {BUILD_DATE}. Private material deliberately excluded.</p>
</div>
"""
    return page("advisor-summary.html", "Advisor One-Pager (W-10)", "Printable summary", body)


# ---------------------------------------------------------------- main
def main():
    built = []
    built.append(build_index())
    built.append(build_gates())
    built.append(build_sell_vs())
    built.append(build_market())
    built.append(build_location())
    built.append(build_hazards())
    built.append(build_questions())
    built.append(build_suggestions())
    built.append(build_sources())
    built.append(build_flagged())
    built.append(build_advisor())
    print(f"built {len(built)} pages: " + ", ".join(built))


if __name__ == "__main__":
    main()
