#!/usr/bin/env python3
"""Build a static, privacy-first decision-support site from verified JSON tables.

Every published table row is rendered from a row in web/data/*.json. A row is
considered publishable only when its status is 'verified' and every source id
resolves to an official source in sources.json. Blank/unverified rows are
rendered with an explicit 'UNVERIFIED — left blank' badge and appear on the
Flagged for Review page.

No parcel identifiers, owner names, addresses, lease files or owner financials
are read or written by this script.
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # /home/user/Jackbox1/web
OUT = ROOT.parent                                     # /home/user/Jackbox1
DATA = ROOT / "data"
PUBLIC = ROOT  # generated HTML lives in web/ so other sessions' root files stay untouched

RETRIEVED = "2026-11-25"
SITE_BASE = "Jackbox1"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SOURCES = load("sources.json")["sources"]
SRC = {s["id"]: s for s in SOURCES}
FINDINGS = load("findings.json")
QUESTIONS = load("questions.json")
GATES = load("gates.json")
FLAGGED = load("flagged.json")
SUGGESTIONS = load("suggestions.json")
RISKS = load("risks.json")

# ---------------------------------------------------------------------------
# Verification: fail the build if any row lacks official source links.
# ---------------------------------------------------------------------------
errors: list[str] = []
OFFICIAL_HOSTS = (
    ".gov", "census.gov", "bls.gov", "irs.gov", "sec.gov", "scag.ca.gov",
    "cde.ca.gov", "dot.ca.gov", "insurance.ca.gov", "boe.ca.gov", "ftb.ca.gov",
    "dof.ca.gov", "lacounty.gov", "lacity.org", "usgs.gov", "fema.gov",
    "conservation.ca.gov", "edd.ca.gov", "oag.ca.gov",
)

for s in SOURCES:
    u = s["url"]
    if not u.startswith("https://"):
        errors.append(f"source {s['id']} is not https: {u}")
    if not any(h in u for h in OFFICIAL_HOSTS) and "github.com" not in u:
        errors.append(f"source {s['id']} host is not recognised: {u}")

checked_rows = 0
for fname, table in (("findings.json", FINDINGS), ("questions.json", QUESTIONS),
                     ("gates.json", GATES), ("flagged.json", FLAGGED),
                     ("suggestions.json", SUGGESTIONS), ("risks.json", RISKS)):
    for row in table["rows"]:
        checked_rows += 1
        src_cell = ""
        for i, col in enumerate(table["columns"]):
            if col in ("sources", "official_source", "source"):
                src_cell = row[i]
        if not src_cell:
            errors.append(f"{fname}: row {row[0]} has no source link")
            continue
        for sid in src_cell.split("|"):
            if sid not in SRC:
                errors.append(f"{fname}: row {row[0]} references unknown source {sid}")
            elif not SRC[sid]["official"] and sid != "PORTAL-GITHUB-REPO":
                errors.append(f"{fname}: row {row[0]} references non-official source {sid}")

for row in FINDINGS["rows"]:
    rid, status, value, sources = row[0], row[7], row[5], row[8]
    if status == "verified" and (value is None or str(value).strip() == ""):
        errors.append(f"findings.json: {rid} is 'verified' but has a blank value")
    if status != "verified" and str(value).strip() != "":
        errors.append(f"findings.json: {rid} is unverified but has a value ({value!r})")
    if not sources:
        errors.append(f"findings.json: {rid} has no source")

if errors:
    raise SystemExit("VERIFICATION FAILED:\n  - " + "\n  - ".join(errors))

# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------
def esc(x) -> str:
    return html.escape(str(x), quote=True)


def source_links(cell: str) -> str:
    out = []
    for sid in cell.split("|"):
        s = SRC[sid]
        label = f"{s['agency']} — {s['title']}"
        out.append(
            f'<a class="src" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer" '
            f'title="{esc(label)}">{esc(sid)} ↗</a>'
        )
    return " ".join(out)


def status_badge(status: str) -> str:
    if status.startswith("verified") or status.startswith("answered"):
        return '<span class="badge ok">verified</span>'
    if status in ("partial", "recommended", "choose", "high", "highest", "medium"):
        return f'<span class="badge part">{esc(status)}</span>'
    if status in ("gated", "needs review"):
        return f'<span class="badge flag">{esc(status)}</span>'
    return f'<span class="badge blank">{esc(status)}</span>'


def table_html(table: dict, rows=None, cls="data-table", highlight_blank=True) -> str:
    cols = table["columns"]
    rows = rows if rows is not None else table["rows"]
    head = "".join(f"<th>{esc(c.replace('_', ' ').title())}</th>" for c in cols)
    body = []
    for r in rows:
        cells = []
        for i, c in enumerate(cols):
            v = r[i]
            if c in ("sources", "official_source", "source"):
                cells.append(f'<td class="sources">{source_links(str(v))}</td>')
            elif c == "status":
                cells.append(f'<td class="status">{status_badge(str(v))}</td>')
            elif (v is None or str(v).strip() == "") and highlight_blank:
                cells.append('<td class="empty"><em>UNVERIFIED — left blank</em></td>')
            elif c in ("question", "answer", "note", "why_it_matters", "next_action", "discovery", "risk_balancing", "metric", "impact_channels", "action"):
                cells.append(f'<td class="wide">{esc(v)}</td>')
            else:
                cells.append(f"<td>{esc(v)}</td>")
        rid = esc(r[0])
        body.append(f'<tr id="{rid}">' + "".join(cells) + "</tr>")
    return (f'<div class="table-wrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def finding_rows(group: str):
    return [r for r in FINDINGS["rows"] if r[1] == group]


def count(label: str, n: int) -> str:
    return f'<div class="stat"><span class="stat-n">{n}</span><span class="stat-l">{esc(label)}</span></div>'


NAV = [
    ("index.html", "Overview", "home"),
    ("summary.html", "Executive summary", "summary"),
    ("gates.html", "Decision gates", "gates"),
    ("questions.html", "Questions & answers", "questions"),
    ("economy.html", "Economy & trade area", "economy"),
    ("operator.html", "Tenant direction", "operator"),
    ("hazards.html", "Hazards & insurance", "hazards"),
    ("tax.html", "After-tax module", "tax"),
    ("calculator.html", "Private calculator", "calculator"),
    ("risks.html", "Risks & scenarios", "risks"),
    ("suggestions.html", "Suggestions", "suggestions"),
    ("sources.html", "Sources", "sources"),
    ("repo-review.html", "Repo review", "repo"),
    ("flagged.html", "⚑ Flagged for Review", "flagged"),
    ("privacy.html", "Privacy", "privacy"),
    ("print.html", "Print advisor summary", "print"),
]

CATEGORY = {
    "home": "Start here", "summary": "Decision", "gates": "Decision",
    "questions": "Decision", "print": "Decision", "suggestions": "Decision",
    "economy": "Evidence", "operator": "Evidence", "hazards": "Evidence",
    "tax": "Evidence", "risks": "Evidence", "calculator": "Tools",
    "sources": "Verification", "repo": "Verification", "flagged": "Verification",
    "privacy": "Verification",
}


def nav_html(active: str) -> str:
    grouped: dict[str, list] = defaultdict(list)
    for fn, label, key in NAV:
        grouped[CATEGORY[key]].append((fn, label, key))
    out = []
    for cat in ("Start here", "Decision", "Evidence", "Tools", "Verification"):
        out.append(f'<div class="nav-cat">{esc(cat)}</div>')
        for fn, label, key in grouped[cat]:
            cls = "active" if key == active else ""
            out.append(f'<a class="nav-link {cls}" href="{fn}">{esc(label)}</a>')
    return "\n".join(out)


def page(title: str, key: str, intro: str, content: str, extra_head: str = "", extra_script: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="description" content="Privacy-first, source-verified decision support for a single-tenant NNN property in central Los Angeles. Aggregate findings only.">
<title>{esc(title)} — {SITE_BASE}</title>
<link rel="stylesheet" href="assets/css/site.css">
{extra_head}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="brand"><span class="brand-mark">JB</span><span><strong>{SITE_BASE}</strong><small>Decision support · aggregate findings only</small></span></div>
  <div class="topbar-right">
    <span class="pill">No parcel or owner identifiers</span>
    <a class="pill warn" href="flagged.html">⚑ Flagged for Review</a>
  </div>
</header>
<div class="layout">
  <aside class="sidebar"><nav aria-label="Site navigation">{nav_html(key)}</nav>
    <div class="sidebar-foot">Retrieved {RETRIEVED} · UTC<br>Every table row links an official source.</div>
  </aside>
  <main id="main" class="main">
    <div class="page-head"><div class="crumb">{esc(CATEGORY[key])}</div><h1>{esc(title)}</h1><p class="lede">{intro}</p></div>
    {content}
    <footer class="foot"><a href="index.html">← Overview</a> · <a href="sources.html">Sources</a> · <a href="privacy.html">Privacy</a> · <a href="print.html">Print one-page summary</a><br>
      This site publishes aggregate, non-identifying findings only. No personal information, owner/parcel identifiers, addresses, APNs, lease files or owner finances are published.</footer>
  </main>
</div>
{extra_script}
</body>
</html>
"""


def card(title: str, body: str, tag: str = "") -> str:
    t = f'<span class="tag">{esc(tag)}</span>' if tag else ""
    return f'<section class="card">{t}<h2>{esc(title)}</h2>{body}</section>'


def section(title: str, body: str, sub: str = "") -> str:
    s = f'<p class="sub">{esc(sub)}</p>' if sub else ""
    return f'<section class="section"><h2>{esc(title)}</h2>{s}{body}</section>'


def build_index() -> str:
    verified = sum(1 for r in FINDINGS["rows"] if r[7] == "verified")
    blanks = sum(1 for r in FINDINGS["rows"] if r[7] != "verified")
    cards = []
    for fn, label, key in NAV[1:]:
        cats = {"Decision": "Decision", "Evidence": "Evidence", "Tools": "Tools", "Verification": "Verification"}
        if key in ("print",):
            desc = "One-page printable handout for authorized advisers."
        elif key == "summary":
            desc = "What is known, what is missing, and the current non-decision."
        elif key == "gates":
            desc = "Eight gates; no winner may be selected until verified inputs exist."
        elif key == "questions":
            desc = "Clear questions, sourced answers, and how to discover what is missing."
        elif key == "economy":
            desc = "Population, income, jobs, schools, traffic, business activity and projections."
        elif key == "operator":
            desc = "Multi-period same-store sales, unit counts, closures and franchise rental revenue."
        elif key == "hazards":
            desc = "Parcel zone status is blank until an APN is available; official portals only."
        elif key == "tax":
            desc = "Verified federal/California rules and the after-tax sale comparison."
        elif key == "calculator":
            desc = "Runs only in your browser; nothing is uploaded or stored."
        elif key == "risks":
            desc = "Business-as-usual and rare black-swan scenarios for every decision."
        elif key == "suggestions":
            desc = "Choose a reviewer path before implementing changes."
        elif key == "sources":
            desc = "Official source register with retrieval status and manual-review links."
        elif key == "repo":
            desc = "Line-by-line repository review and verification method."
        elif key == "flagged":
            desc = "All irregularities and unverified items, clearly labelled."
        elif key == "privacy":
            desc = "Anonymisation rules and the never-published list."
        else:
            desc = ""
        cards.append(f'<a class="tile" href="{fn}"><span class="tile-cat">{esc(CATEGORY[key])}</span><h3>{esc(label)}</h3><p>{esc(desc)}</p><span class="tile-go">Open →</span></a>')
    intro = ("A clean, category-organized dashboard for one single-tenant NNN quick-service property around central Los Angeles. "
             "The lease expiry is known only as a range (2030–2035). No sell/hold winner is selected because verified private inputs do not exist. "
             "Every published table row links an official source; unconfirmed values are blank and flagged.")
    content = f"""
    <div class="hero">
      <div><span class="eyebrow">Decision status</span><h2>No winner selected — evidence gates are open</h2>
      <p>The only defensible current course is a gated, privacy-first process: protect identity, fix the tract set, abstract the lease and notice calendar, verify parcel hazards and market quotes, then compare an after-tax sale with a negotiated renewal. This is a process recommendation, not a property-value conclusion.</p>
      <div class="hero-actions"><a class="btn primary" href="print.html">Print one-page summary</a><a class="btn" href="flagged.html">See flagged items</a></div></div>
      <div class="hero-figure"><span class="figure-label">Lease expiry supplied</span><strong>2030–2035</strong><span class="figure-note">exact date unverified · private lease only</span></div>
    </div>
    <div class="stats">{count("verified finding rows", verified)}{count("blank / flagged rows", blanks)}{count("official sources", len(SOURCES))}{count("decision gates open", 8)}</div>
    {section("Explore the site", '<div class="tiles">' + "".join(cards) + "</div>", "Categories: Decision · Evidence · Tools · Verification. All findings are aggregate and non-identifying.")}
    {section("What this site will never publish", '<ul class="never"><li>Owner names, personal information or owner financials</li><li>Street addresses, APNs, parcel IDs or tenant-unit identifiers</li><li>Lease files, rent rolls, quotes containing identifying details, or tax returns</li><li>Any inferred value for a blank cell</li></ul>')}
    """
    return page("Overview", "home", intro, content)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def build_summary() -> str:
    known = [
        "The property is a single-tenant NNN quick-service restaurant asset around central Los Angeles; the lease expiration is reported only as a range (2030–2035).",
        "Official regional evidence is mixed: DOF reports county population −0.6% and city −0.9% in 2025–26, while EDD reports county nonfarm employment +0.9% year over year in October 2026 and food-services employment +7,500.",
        "Jack in the Box system same-store sales moved from +0.4% (Q1 FY2025) to (4.4%) (Q2) and (7.1%) (Q3), with FY2025 at (4.2%); system units fell from 2,191 to 2,136.",
        "Federal and California tax mechanics are verified: 0/15/20% federal long-term rates, 25% maximum on unrecaptured §1250 gain, 3.8% NIIT, and California taxes capital gains as ordinary income.",
        "Parcel hazard status is not known; CAL FIRE, FEMA, CGS and USGS provide official portals and regional context only.",
    ]
    missing = [
        "APN/address, fixed Census tract set, zoning, frontage AADT, school catchment and competitor set.",
        "Executed lease, exact expiry, rent, escalations, options, guarantees and a notice calendar reconciled to the abstract.",
        "Owner basis, depreciation schedule, loan terms, filing status, tax rate area and current secured tax bill.",
        "Verified arm's-length short-lease QSR quotes, comparable sale pairs, and a written negotiated renewal proposal.",
        "Engineering, seismic, flood and fire parcel lookups, insurance quotes, and sufficient comparable history for a back-test.",
    ]
    def li(items): return "".join(f"<li>{esc(x)}</li>" for x in items)
    content = f"""
    <div class="callout neutral"><strong>Executive summary.</strong> Do not sell, renew or commit yet. Verified public evidence supports a regional profile, not a parcel-level investment conclusion. no sell/renew/hold winner can reasonably be selected until the private inputs exist; the site therefore publishes blanks and flags instead of guessed numbers.</div>
    {card("Known — verified from official sources", f'<ol class="tight">{li(known)}</ol><p class="note">Each item is traceable to a row in the <a href="sources.html">source register</a> and linked on the category pages.</p>', "observations")}
    {card("Missing — left blank and flagged", f'<ol class="tight">{li(missing)}</ol><p class="note">See <a href="flagged.html">Flagged for Review</a> and <a href="questions.html">Questions &amp; answers</a>.</p>', "gaps")}
    {card("Best current course (process, not a winner)", '<p>Protect privacy → fix tract set → abstract lease + notice calendar → verify parcel hazards, planning, traffic, schools and competitors → collect quotes/comps and a negotiated renewal → compute the after-tax sale case with the browser-only calculator → back-test a versioned cash-flow model only if sufficient verified comparable history exists → choose a risk-balanced path privately with authorized advisers.</p><p class="note">This balances wealth preservation and growth opportunity without pretending that a regional proxy is a parcel fact.</p>', "recommendation")}
    {section("Decision-gate snapshot", table_html(GATES, cls="data-table slim"))}
    """
    return page("Executive summary", "summary", "What is known, what is missing, and the only defensible course before verified inputs exist.", content)


def build_gates() -> str:
    content = f"""
    <div class="callout">A gate is <em>open</em> until its private inputs are verified. Flagged items are published on <a href="flagged.html">Flagged for Review</a> and do not block the site build; they do block a decision.</div>
    {section("W-03 Decision-gate progress board", table_html(GATES), "Status values: open, partial. No gate is closed yet.")}
    {section("Gate dependencies", '<ol class="tight"><li><strong>G1</strong> identity and tract set unlock G3 and W-01.</li><li><strong>G2</strong> lease abstract + notice calendar unlock G7 and any commitment.</li><li><strong>G5</strong> parcel hazard + engineering + insurance unlock joint stress on loss of rent, repairs and exit liquidity.</li><li><strong>G6/G7</strong> tax mechanics + real quotes unlock the after-tax sale vs negotiated renewal comparison.</li><li><strong>G8</strong> a versioned, back-tested cash-flow model runs only after G1–G7 and sufficient comparable history.</li></ol>')}
    """
    return page("Decision gates", "gates", "Eight gates separate verified observations from the private inputs still required before any sale or renewal commitment.", content)


def build_questions() -> str:
    answered = [r for r in QUESTIONS["rows"] if r[3].startswith("answered")]
    openq = [r for r in QUESTIONS["rows"] if r[3].startswith("open")]
    content = f"""
    <div class="callout neutral">Answers appear only where an official source was retrieved and read. Blank answers are never inferred; the Discovery column tells an authorized adviser how to obtain the missing information offline.</div>
    {section(f"Known — sourced answers ({len(answered)})", table_html(QUESTIONS, answered), "What is known.")}
    {section(f"Missing — questions that must be answered before any decision ({len(openq)})", table_html(QUESTIONS, openq), "What is missing, and suggestions to discover it.")}
    """
    return page("Questions, information & answers", "questions", "A clear list of questions, information and answers that must be addressed before any decision is reasonably made — separating known from missing.", content)


def build_economy() -> str:
    groups = [("population", "Geography, population & demographics"), ("income", "Income levels & poverty"),
              ("housing", "Housing & households"), ("education", "Education & school systems"),
              ("labor", "Job growth, employment & prices"), ("business", "Business activity"),
              ("transport", "Traffic & local planning"), ("projection", "Long-run projection system"),
              ("tract", "Tract-level trend evidence (W-01 / W-12)")]
    body = "".join(section(t, table_html(FINDINGS, finding_rows(g))) for g, t in groups)
    content = f"""
    <div class="callout warnline"><strong>W-01 status:</strong> trade-area figures are blank. City/county rows below are explicitly labelled proxies and cannot be substituted for the parcel's trade area. "Central Los Angeles" is not a Census geography; a fixed tract set must be selected in a secure workflow.</div>
    <div class="analysis"><h2>Findings &amp; analysis</h2>
      <p><strong>Population.</strong> Two official series point the same direction: California DOF E-1 reports provisional 1/1/2026 population of 9,837,286 for the county (−0.6%) and 3,806,201 for the city (−0.9%); Census QuickFacts V2025 shows a −3.2% county / −0.8% city change from the 2020 estimates base to July 1, 2025. These are different vintages and are not comparable to each other.</p>
      <p><strong>Income &amp; housing.</strong> County median household income ($90,112, 2020–2024, 2024 dollars) exceeds the city ($81,939), while city median owner-occupied value is higher ($921,200 vs $834,200). These are proxies; trade-area figures remain blank.</p>
      <p><strong>Jobs &amp; local economy.</strong> EDD reports October 2026 county nonfarm employment at 4,662,800 (preliminary), up 40,700 or 0.9% year over year. Food services and drinking places added 7,500 jobs, while information lost 2,600. Leisure and hospitality added 10,500. BLS shows the metropolitan-division unemployment rate falling from 5.2% in May 2026 to 4.6% (preliminary) in October 2026, and CPI-U 12-month change of 3.7% in September 2026. The sector mix matters more to a quick-service site than the headline rate.</p>
      <p><strong>Schools, traffic, competitors.</strong> CDE reports 497,105 students in Los Angeles Unified in 2025–26; Census reports a 30.4-minute county mean commute; Caltrans publishes 2021–2024 AADT files for the State Highway System only. Parcel catchment, frontage AADT and competitor counts are blank until the tract set and road are fixed.</p>
      <p><strong>Projection system (deep research).</strong> SCAG's adopted Connect SoCal 2024 forecast is used as the official long-range projection, not as a prediction: regional employment 8,976,000 (2019) → 10,276,000 (2050); baseline population 20.8 million in 2050 with a 19.85–21.9 million uncertainty range. SCAG explicitly states that subregional forecasting has higher uncertainty than regional forecasting. Observations and assumptions are separated in every table.</p>
    </div>
    {body}
    """
    return page("Economy & trade area", "economy", "Geography, income levels, school systems, population, job growth, business activity, traffic and every officially verifiable factor influencing the local economy — with regional figures kept alongside blank trade-area rows.", content)


def build_operator() -> str:
    content = f"""
    <div class="analysis"><h2>Direction, not one quarter</h2><p>The series below uses SEC EDGAR filings: three fiscal-2025 quarters plus FY2024/FY2025 annual results. System same-store sales moved <strong>+0.4% → (4.4%) → (7.1%)</strong> across Q1–Q3 FY2025 and finished <strong>(4.2%)</strong> for FY2025 versus <strong>(1.3%)</strong> in FY2024. System restaurants fell 2,191 → 2,136; closures rose 25 → 86, including a Q3 block-closure program. Jack in the Box brand franchise rental revenues fell $347,227k → $332,735k (−4.2%), chiefly from lower percentage rent on lower sales. These are systemwide observations, not the subject unit's rent coverage; that cell remains blank.</p></div>
    {section("Multi-period same-store sales, unit counts, closures & franchise rental revenue", table_html(FINDINGS, finding_rows("operator")))}
    {section("Analysis / findings", '<ul class="tight"><li>Direction is negative across the multi-period system series, despite an improving local employment backdrop; the two are different geographies and must not be netted against each other.</li><li>Franchise rental revenue is reported by the public parent; a franchised unit may have a different obligor. Verify guarantees privately.</li><li>The Del Taco divestiture agreement in the FY2025 10-K is a corporate-structure event, not a fact about this parcel.</li><li>No unit-level sales, rent coverage, closure notice or renewal proposal is published.</li></ul>')}
    """
    return page("Tenant / operator direction", "operator", "A multi-period series of same-store sales, unit counts, closures and franchise rental revenue showing direction rather than one quarter.", content)


def build_hazards() -> str:
    content = f"""
    <div class="callout warnline"><strong>W-04 status:</strong> parcel actual earthquake / fire / flood zone status is blank. Regional probabilities and classifications below are context only. The APN/address may be used only in a secure internal workflow with authorized advisers; it is never published here.</div>
    <div class="portal-grid">
      <div class="portal"><h3>🔥 Fire</h3><p>OSFM classifies Moderate / High / Very High hazard. SRA maps effective April 1, 2024; 2025 LRA rollout has four phases; a 2026 SRA comment period is open Nov 9, 2026 – Jan 8, 2027.</p>{source_links('SRC-CALFIRE-FHSZ|PORTAL-ZIMAS')}</div>
      <div class="portal"><h3>🌊 Flood</h3><p>FEMA: 1%+ annual chance is high risk; at least a one-in-four chance over a 30-year mortgage. NFHL covers over 90% of the U.S. population. Address search is required.</p>{source_links('SRC-FEMA-FLOODMAPS|SRC-FEMA-NFHL|PORTAL-FEMA-MSC')}</div>
      <div class="portal"><h3>〰️ Seismic</h3><p>CGS maps Alquist-Priolo fault, liquefaction, landslide and tsunami Zones of Required Investigation; sellers must disclose mapped-zone status at sale. EQ ZApp is authoritative.</p>{source_links('SRC-CGS-SEISMIC|PORTAL-CGS-EQZAPP')}</div>
      <div class="portal"><h3>🛡️ Insurance</h3><p>CDI publishes statewide FAIR Plan counts and homeowner averages. NFIP typically has a 30-day waiting period. Statewide counts are not quotes for this asset.</p>{source_links('SRC-CDI-SIS|SRC-FEMA-NFIP')}</div>
    </div>
    {section("Parcel-level hazard screening (W-04) — actual status blank", table_html(FINDINGS, finding_rows("hazard") + finding_rows("insurance")))}
    {section("Private checks required before any commitment", '<ol class="tight"><li>Run the four official parcel lookups and save dated screenshots in the access-controlled workspace.</li><li>Commission engineering / geotechnical / Phase I reports privately.</li><li>Obtain at least three written insurance quotes (fire, flood, earthquake, business interruption).</li><li>Stress <strong>loss of rent + repairs + exit liquidity jointly</strong> under both business-as-usual and rare black-swan scenarios (see <a href="risks.html">Risks</a>).</li><li>Recheck the 2026 SRA comment outcome before relying on a fire designation.</li></ol>')}
    """
    return page("Hazards & insurance", "hazards", "Parcel actual earthquake, fire and flood zone status replacing regional hazard context — with official portals, private checks and joint stress on loss of rent, repairs and exit liquidity.", content)


def build_tax() -> str:
    content = f"""
    <div class="callout neutral">The site publishes <strong>verified rules, not an owner-specific tax bill</strong>. "Verified tax rules turned into one number comparable with the hold case" happens only in the browser-only calculator after private inputs are entered; nothing is uploaded or stored. Federal 2025 and 2026 thresholds are shown separately because they differ.</div>
    {section("Verified tax rules", table_html(FINDINGS, finding_rows("tax")))}
    {section("After-tax sale comparison alongside a negotiated renewal case", '<div class="compare"><div class="compare-col"><h3>Sale case</h3><ul class="tight"><li>Amount realized − adjusted basis = gain (IRS Topic 409).</li><li>Adjusted basis must be reduced by depreciation allowed or allowable, whichever is greater (Pub. 946).</li><li>Long-term brackets 0/15/20%; unrecaptured §1250 gain up to 25%; NIIT 3.8% on the lesser of NII or MAGI excess.</li><li>California taxes all capital gains as ordinary income; no lower state capital-gain rate.</li><li>Section 1031 is an alternative only for qualifying real property; boot triggers recognition.</li></ul></div><div class="compare-col"><h3>Renew / hold case</h3><ul class="tight"><li>Private rent and escalations (blank here) drive pre-tax NOI.</li><li>Rents are generally net investment income for NIIT purposes.</li><li>Prop 13 limits the base rate to 1% plus voter-approved bonded indebtedness, with a 2% annual assessed-value cap absent a change of ownership or new construction.</li><li>Negotiated renewal term, tenant improvements, credit and downtime are private inputs.</li></ul></div></div><p class="note">Because basis, purchase date, depreciation, loan terms, filing status, tax rate area and the renewal proposal are all unverified, <strong>no single after-tax number is published</strong>. The <a href="calculator.html">private calculator</a> produces that number locally for the reader.</p>')}
    {section("W-02 private sell-versus-hold worksheet", table_html(FINDINGS, finding_rows("market")), "All pricing inputs are blank and flagged: short-lease discount is priced from real quotes only, never inferred.")}
    """
    return page("After-tax module", "tax", "Verified tax rules, the after-tax sale comparison alongside a negotiated renewal case, and the private sell-versus-hold worksheet with no published winner.", content)


def build_risks() -> str:
    content = f"""
    <div class="callout">Risks are listed for <em>every possible decision</em>: sell before expiry, renew/hold, and risks common to both. Business-as-usual events and rare black-swan wildfire/natural-disaster scenarios are labelled. Impact channels explicitly include loss of rent, repairs and exit liquidity.</div>
    {section("Risk register", table_html(RISKS))}
    {section("Deep research for a reliable projection system", '<p>Use <a href="economy.html">SCAG Connect SoCal 2024</a> as the official long-range projection framework, BLS/EDD as observed labour series, DOF as observed population series, SEC filings as observed operator series, and the official hazard/insurance agencies for tail risk. A versioned, back-tested cash-flow model is deliberately <strong>not published</strong>: verified inputs and sufficient comparable history do not yet exist. When built, it must keep observations and assumptions in separate columns, pin data vintages, and re-run whenever a gate changes.</p>')}
    {section("Wealth preservation & growth opportunity", '<p>For the property and the owner as an individual, the risk-balanced course is to avoid an irreversible commitment while the option value of the exact lease date, renewal proposal and quote set is unknown. Balancing means: keep liquidity and privacy (no identifying publication), preserve the renewal option by reconciling the notice calendar, avoid a forced sale into an unpriced short-lease discount, and avoid holding through an uninsured/unengineered hazard exposure. A final winner is selected privately only after the gates close.</p>')}
    """
    return page("Risks & scenarios", "risks", "Risks for every possible decision, business-as-usual events, rare black-swan wildfire/natural-disaster scenarios, and deep research for a reliable projection system.", content)


def build_suggestions() -> str:
    content = f"""
    <div class="callout neutral"><strong>Reviewer path selector.</strong> Choose the best path below before implementing changes. Path A is recommended because it minimizes the chance of a wrong answer; the others are parallel workstreams, not decisions to sell or hold.</div>
    {section("Suggestions section", table_html(SUGGESTIONS))}
    <div class="path-picker" id="path-picker"><h2>Choose a path</h2><p class="sub">This selector is local to your browser. It highlights a row and does not transmit anything.</p>
      <div class="path-buttons">{"".join(f'<button type="button" class="path-btn" data-path="{esc(r[0])}">{esc(r[0])} · {esc(r[1])}</button>' for r in SUGGESTIONS["rows"])}</div>
      <div id="path-result" class="path-result">Select a path to see the action and its best-fit reviewer.</div>
    </div>
    <script>
    (()=>{{const data={json.dumps({r[0]: {"path": r[1], "action": r[2], "best": r[3], "priority": r[4]} for r in SUGGESTIONS["rows"]}, ensure_ascii=False)};
      const out=document.getElementById('path-result');
      document.querySelectorAll('.path-btn').forEach(b=>b.addEventListener('click',()=>{{
        document.querySelectorAll('.path-btn').forEach(x=>x.classList.remove('sel'));
        b.classList.add('sel'); const d=data[b.dataset.path];
        out.innerHTML='<strong>'+d.path+'</strong><p>'+d.action+'</p><small>Best for: '+d.best+' · Priority: '+d.priority+'</small>';
        const row=document.getElementById(b.dataset.path); if(row){{row.classList.add('flash'); setTimeout(()=>row.classList.remove('flash'),1400);}}
      }}));
    }})();
    </script>
    """
    return page("Suggestions", "suggestions", "A dedicated suggestions section so a reviewer can choose the best path before implementing changes.", content)


def build_sources() -> str:
    rows = []
    for s in SOURCES:
        rows.append([s["id"], s["agency"], s["title"], s["kind"],
                     "yes" if s["official"] else "repo only",
                     "fetched & read" if s["verified_fetch"] else "manual review only",
                     RETRIEVED if s["verified_fetch"] else "n/a",
                     s["notes"], s["url"]])
    tbl = {"columns": ["id", "agency", "title", "kind", "official", "retrieval", "date", "notes", "url"], "rows": rows}
    # custom table so URL is a link, not a source-id cell
    head = "".join(f"<th>{esc(c.title())}</th>" for c in tbl["columns"])
    body = []
    for r in rows:
        cells = [f'<td><code>{esc(r[0])}</code></td>', f'<td>{esc(r[1])}</td>', f'<td class="wide">{esc(r[2])}</td>',
                 f'<td>{esc(r[3])}</td>', f'<td>{esc(r[4])}</td>', f'<td>{status_badge("verified" if r[5] == "fetched & read" else "manual review only")}</td>',
                 f'<td>{esc(r[6])}</td>', f'<td class="wide">{esc(r[7])}</td>',
                 f'<td><a href="{esc(r[8])}" target="_blank" rel="noopener noreferrer">Open official link ↗</a></td>']
        body.append("<tr>" + "".join(cells) + "</tr>")
    tblhtml = f'<div class="table-wrap"><table class="data-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    content = f"""
    <div class="callout">All values published on this site come from the <em>fetched &amp; read</em> rows. Portal rows are official manual-review links only; no numeric value is taken from a portal that was not fetched. The GitHub repository row is used solely for the repo review.</div>
    {section(f"Official source register ({len(SOURCES)} entries)", tblhtml, "Manual review: open any link. Retrieval date 2026-11-25 UTC.")}
    """
    return page("Sources", "sources", "Official trusted source links for manual review, with retrieval status, agency and verification notes.", content)


def build_repo() -> str:
    items = [
        ["L-01", "README.md", "10-byte project-title placeholder, no trailing newline", "No content, privacy notice, licence, source register or data to verify.", "PORTAL-GITHUB-REPO"],
        ["L-02", ".git / branch state", "Current branch from main at 4aa9dad; five other session branches on the remote", "Parallel claims overlap; scope isolated under web/**.", "PORTAL-GITHUB-REPO"],
        ["L-03", "COORDINATION.md", "Created by this session with a non-overlapping claim and append-only §5+", "Shared board protocol followed; other sessions' §1–§4 preserved as a snapshot.", "PORTAL-GITHUB-REPO"],
        ["L-04", "web/data/*.json", "Every row carries source ids; verified rows have values; unverified rows are blank", "Machine-checked by web/tools/verify.py.", "PORTAL-GITHUB-REPO"],
        ["L-05", "web/tools/build.py", "Static generator; no network calls, no private records, no identifiers", "Escapes all cell text; fails the build on a missing official source.", "PORTAL-GITHUB-REPO"],
        ["L-06", "web/*.html", "Category-organized pages, dashboard UI, tables and analysis", "Internal links checked by web/tools/check_links.py.", "PORTAL-GITHUB-REPO"],
        ["L-07", "index.html (root)", "Small landing page pointing to web/index.html", "Pages source remains main:/ so the root landing page is live.", "PORTAL-GITHUB-REPO"],
        ["L-08", "All published text", "Scanned for APNs, street addresses, owner names, lease files and owner financials", "No identifying values are present; placeholders used.", "PORTAL-GITHUB-REPO"],
    ]
    tbl = {"columns": ["id", "path", "finding", "verification", "sources"], "rows": items}
    content = f"""
    <div class="callout">Line-by-line review of the repository as it existed at the start of this session, plus verification performed on every file this session adds. Irregularities are published on <a href="flagged.html">Flagged for Review</a> and do not block the site.</div>
    {section("Repository review", table_html(tbl))}
    {section("Verification performed", '<ol class="tight"><li><strong>Source check</strong>: every table row resolves to an official source id; every source URL is HTTPS and on a recognised official host (or the repository itself for repo-review rows).</li><li><strong>Value check</strong>: a row marked verified must have a non-blank value; a row not marked verified must have a blank value. No inferred values.</li><li><strong>Privacy scan</strong>: published files are scanned for identifiers, street-address patterns, APN patterns and owner-financial keywords.</li><li><strong>Link check</strong>: all internal href/src targets must exist; external links are opened in a new tab with <code>rel="noopener noreferrer"</code>.</li><li><strong>Build check</strong>: the static site is generated locally, then served over HTTP and checked for 200 responses.</li></ol>')}
    {section("Method limits", '<p>Only pages retrieved and read in this session are used for published values. Search snippets, unofficial summaries and portal pages that were not fetched are never used as data. BLS/EDD preliminary values and mixed Census vintages are flagged. SCAG forecasts are labelled projections. No parcel-specific value is inferred from a regional figure.</p>')}
    """
    return page("Repository review", "repo", "Line-by-line repository review, verification performed, irregularities and method limits.", content)


def build_flagged() -> str:
    blank_rows = [r for r in FINDINGS["rows"] if r[7] != "verified"]
    content = f"""
    <div class="callout warnline"><strong>Flagged for Review.</strong> Every irregularity and unconfirmed item is published here with official source links. Per the coordination protocol, <code>needs review</code> does not block the site build or merge — but it does block any decision.</div>
    {section(f"Irregularities ({len(FLAGGED['rows'])})", table_html(FLAGGED), "Clearly labelled; all have official source links.")}
    {section(f"Unverified / blank published cells ({len(blank_rows)})", table_html(FINDINGS, blank_rows), "Values deliberately left blank; never filled or inferred.")}
    {section("Handoff / change requests", '<ul class="tight"><li><strong>C-01</strong> (to other integration sessions): Pages source is unchanged at <code>main:/</code>; this site provides both a root landing page and <code>web/index.html</code>.</li><li><strong>C-02</strong>: <code>COORDINATION.md</code> is append-only from §5 onward; other sessions should not overwrite this section.</li><li><strong>C-03</strong>: no <code>docs/**</code>, <code>private/**</code>, <code>README.md</code> or <code>.gitignore</code> file was edited by this session.</li></ul>')}
    """
    return page("⚑ Flagged for Review", "flagged", "All flagged irregularities and unverified items, with source links. Nothing here blocks the site build; everything here blocks a premature decision.", content)


def build_privacy() -> str:
    anonymisation = (
        '<ol class="tight">'
        '<li>The subject is described only as "one single-tenant NNN quick-service property around central Los Angeles".</li>'
        '<li>Placeholders are used instead of identifiers; blank cells are labelled UNVERIFIED.</li>'
        '<li>Only aggregate government tables and systemwide public-company filings are reproduced.</li>'
        "<li>The private calculator performs arithmetic in the reader's browser; there are no form submissions, cookies, analytics, localStorage writes or network calls.</li>"
        '<li>The secure workflow (APN/address → tract set → planning/traffic/school/competitor evidence) is described but never executed on a public page.</li>'
        '<li>Authorized advisers keep parcel/owner records in an access-controlled internal workspace or offline.</li>'
        '</ol>'
    )
    official_def = (
        '<p>The California Attorney General defines personal information as information that '
        '"identifies, relates to, or could reasonably be linked with you or your household", '
        'and lists rights to know, delete, correct, opt-out, limit and non-discrimination. '
        'Publicly available property records are excluded from that statutory definition, '
        'but this site applies the stricter project rule anyway.</p>'
        f'<p>{source_links("SRC-OAG-CCPA|SRC-DOF-E1-METHOD")}</p>'
    )
    content = f"""
    <div class="callout"><strong>Privacy is the highest priority.</strong> This website publishes aggregate, non-identifying findings only. Personal information discovered during research is internal-use only and must not appear in the final website product or on the website.</div>
    {section("Never published", '<ul class="never"><li>Owner or tenant personal names, contact details, signatures or personal information</li><li>Street address, APN, parcel ID, PIN, legal description, map sheet or precise geolocation</li><li>Lease files, amendments, memoranda of lease, rent rolls, notices or guarantees</li><li>Owner finances: basis, depreciation schedule, loan terms, tax returns, filing status or account numbers</li><li>Any unit-level operating data that could identify the property</li></ul>')}
    {section("Anonymisation rules actually applied", anonymisation)}
    {section("Verified privacy framework", table_html(FINDINGS, finding_rows("privacy")))}
    {section("Official definition (for manual review)", official_def)}
    """
    return page("Privacy", "privacy", "Anonymisation rules, the never-published list, and the official privacy framework used by this decision-support site.", content)


PRINT_CSS = """<style>
@media print{ .topbar,.sidebar,.foot,.no-print{display:none!important} .layout{display:block} .main{max-width:none;padding:0}
body{font:11pt/1.35 Georgia,serif;color:#000;background:#fff} .page-head h1{font-size:18pt;margin:0 0 4pt}
.lede{font-size:10pt} .card,.section,.callout{break-inside:avoid;border:1px solid #999;box-shadow:none;margin:8pt 0;padding:8pt}
.table-wrap{overflow:visible} table{font-size:8pt} a{color:#000;text-decoration:none} .badge{border:1px solid #333;padding:0 3pt}
h2{font-size:12pt} .sub,.note{font-size:9pt} }
</style>"""


def build_print() -> str:
    content = """
    <div class="no-print callout">Use your browser's Print → Save as PDF. This page is sized to one page; it contains no identifiers and no unverified numbers.</div>
    <div class="print-sheet">
      <h2>One-page advisor summary — single-tenant NNN property (aggregate only)</h2>
      <p class="sub">Lease expiry supplied as a range: <strong>2030–2035</strong>. Exact date unverified. No sell / renew / hold winner selected.</p>
      <div class="print-grid">
        <div><h3>Decision status</h3><p>Evidence gates G1–G8 are open or partial. The only defensible course is a gated process: protect privacy, fix the tract set, abstract the lease and notice calendar, verify parcel hazards and real quotes, then compare an after-tax sale with a negotiated renewal. Do not commit.</p></div>
        <div><h3>Known (official sources)</h3><ul class="tight"><li>County population −0.6%, city −0.9% (DOF, 2025–26); county nonfarm jobs +0.9% y/y and food-services jobs +7,500 (EDD, Oct 2026, preliminary).</li><li>County MHI $90,112 / city $81,939 (ACS 2020–2024, 2024 dollars).</li><li>System same-store sales +0.4% → (4.4%) → (7.1%) across Q1–Q3 FY2025; FY2025 (4.2%); system units 2,191 → 2,136.</li><li>Federal 0/15/20% long-term rates, 25% max §1250 gain, 3.8% NIIT; California taxes capital gains as ordinary income; Prop 13 1% base rate.</li></ul></div>
        <div><h3>Missing (blank + flagged)</h3><ul class="tight"><li>APN/address, fixed tract set, zoning, AADT, school catchment, competitor set, tract-level trends.</li><li>Lease, exact expiry, rent, options, guarantees, notice calendar.</li><li>Basis, depreciation, loan terms, owner tax profile, tax rate area.</li><li>Short-lease quotes, comps, negotiated renewal, engineering and insurance quotes.</li></ul></div>
        <div><h3>Risk balance</h3><p>Preserve liquidity, privacy and the renewal option; avoid an unpriced short-lease discount and an uninsured hazard exposure. Stress loss of rent, repairs and exit liquidity jointly, including business-as-usual and rare wildfire / earthquake / flood scenarios. Select a winner privately only after gates close.</p></div>
      </div>
      <h3>Verified rules & sources (open for manual review)</h3>
      <p class="src-line">
        <a href="https://www.census.gov/quickfacts/fact/table/losangelescountycalifornia,losangelescitycalifornia/INC110223">Census QuickFacts ↗</a>
        <a href="https://dof.ca.gov/media/docs/forecasting/demographics/estimates/e-1_2026_press_release.Pdf">CA DOF E-1 2026 ↗</a>
        <a href="https://labormarketinfo.edd.ca.gov/file/lfmonth/la$pds.pdf">CA EDD Oct 2026 ↗</a>
        <a href="https://www.bls.gov/eag/eag.ca_losangeles_md.htm">BLS EAG ↗</a>
        <a href="https://www.sec.gov/Archives/edgar/data/807882/000080788225000072/jack-20250928.htm">SEC 10-K FY2025 ↗</a>
        <a href="https://www.irs.gov/taxtopics/tc409">IRS Topic 409 ↗</a>
        <a href="https://www.irs.gov/pub/irs-drop/rp-25-32.pdf">Rev. Proc. 2025-32 ↗</a>
        <a href="https://www.ftb.ca.gov/file/personal/income-types/capital-gains-and-losses.html">CA FTB ↗</a>
        <a href="https://www.boe.ca.gov/proptaxes/pdf/pub29.pdf">BOE Pub 29 ↗</a>
        <a href="https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones">CAL FIRE FHSZ ↗</a>
        <a href="https://www.fema.gov/flood-maps">FEMA Flood Maps ↗</a>
        <a href="https://www.conservation.ca.gov/cgs/sh/program">CGS Seismic ↗</a>
        <a href="https://oag.ca.gov/privacy/ccpa">CA AG CCPA ↗</a>
      </p>
      <p class="note">All published findings are aggregate and non-identifying. No personal information, owner/parcel identifiers, addresses, APNs, lease files or owner finances appear on this site. Unverified values are left blank and flagged. See: <a href="flagged.html">Flagged for Review</a> · <a href="sources.html">Sources</a> · <a href="privacy.html">Privacy</a>.</p>
    </div>
    """
    return page("Printable advisor summary (W-10)", "print", "One page for authorized advisers. No identifiers, no inferred numbers, official links for manual review.", content, extra_head=PRINT_CSS)


CALC_JS = r"""
<script>
/* Private, browser-only calculator. No network calls, no storage, no analytics. */
(() => {
  const $ = id => document.getElementById(id);
  const num = id => { const v = parseFloat($(id).value); return Number.isFinite(v) ? v : 0; };
  const money = v => (v < 0 ? '-' : '') + '$' + Math.abs(v).toLocaleString('en-US', {maximumFractionDigits: 0});
  const pct = v => (v * 100).toFixed(1) + '%';

  function federalLTCG(gain, otherTaxableIncome, filingStatus, year) {
    // 2025 / 2026 thresholds from IRS Topic 409 and Rev. Proc. 2025-32 §4.03.
    const t = {
      '2025': { single:[48350,533400], mfs:[48350,300000], mfj:[96700,600050], hoh:[64750,566700] },
      '2026': { single:[49450,545500], mfs:[49450,306850], mfj:[98900,613700], hoh:[66200,579600] }
    }[year][filingStatus];
    const start = Math.max(0, t[0] - otherTaxableIncome);
    const mid   = Math.max(0, Math.min(gain, t[1] - otherTaxableIncome) - start);
    const top   = Math.max(0, gain - start - mid);
    return start * 0 + mid * 0.15 + top * 0.20;
  }
  function niit(nii, magi, filingStatus) {
    const threshold = filingStatus === 'mfj' ? 250000 : filingStatus === 'mfs' ? 125000 : 200000;
    return 0.038 * Math.max(0, Math.min(nii, magi - threshold));
  }
  function ordinaryTax(taxable, filingStatus) {
    // Simplified 2026 ordinary brackets from Rev. Proc. 2025-32 §4.01, used only
    // for the illustrative California estimate. Edges are cumulative ceilings.
    const edges = filingStatus === 'mfj'
      ? [[24800,.10],[100800,.12],[211400,.22],[403550,.24],[512450,.32],[768700,.35],[Infinity,.37]]
      : filingStatus === 'mfs'
      ? [[12400,.10],[50400,.12],[105700,.22],[201775,.24],[256225,.32],[384350,.35],[Infinity,.37]]
      : filingStatus === 'hoh'
      ? [[17700,.10],[67450,.12],[105700,.22],[201750,.24],[256200,.32],[640600,.35],[Infinity,.37]]
      : [[12400,.10],[50400,.12],[105700,.22],[201775,.24],[256225,.32],[640600,.35],[Infinity,.37]];
    let last = 0, tax = 0;
    for (const [ceil, rate] of edges) {
      if (taxable <= last) break;
      tax += (Math.min(taxable, ceil) - last) * rate;
      last = ceil;
      if (!Number.isFinite(ceil)) break;
    }
    return Math.max(0, tax);
  }

  function compute() {
    const salePrice = num('salePrice'), sellingCosts = num('sellingCosts'), basis = num('basis');
    const accumDep = num('accumDep'), loanBalance = num('loanBalance');
    const otherIncome = num('otherIncome'), caOtherTaxable = num('caOtherTaxable');
    const status = $('filingStatus').value, year = $('taxYear').value;
    const caMarginal = num('caMarginal') / 100;
    const annualRent = num('annualRent'), opex = num('opex'), propTax = num('propTax'), insurance = num('insurance');
    const holdYears = Math.max(1, num('holdYears')), renewalCapex = num('renewalCapex');
    const discountRate = num('discountRate') / 100, exitCap = num('exitCap') / 100;

    const amountRealized = salePrice - sellingCosts;
    const adjustedBasis = Math.max(0, basis - accumDep);
    const totalGain = Math.max(0, amountRealized - adjustedBasis);
    const recaptured1250 = Math.min(totalGain, accumDep);
    const residualGain = totalGain - recaptured1250;
    // Unrecaptured §1250 gain is taxed at up to 25%; the rest uses 0/15/20% brackets.
    const fedBrackets = federalLTCG(residualGain, Math.max(0, otherIncome), status, year);
    // Unrecaptured section 1250 gain has a 25% maximum rate; this illustration
    // applies that ceiling. A tax professional should stack the actual brackets.
    const fed1250 = recaptured1250 * 0.25;
    const nii = totalGain + annualRent; // illustrative: sale gain + one year of rent
    const magi = otherIncome + nii;
    const niitTax = niit(nii, magi, status);
    const federalTax = fedBrackets + fed1250 + niitTax;
    const caTax = Math.max(0, ordinaryTax(caOtherTaxable + totalGain, status) - ordinaryTax(caOtherTaxable, status));
    // A flat marginal-rate estimate is shown alongside for sensitivity only.
    const caFlat = totalGain * caMarginal;
    const taxes = federalTax + caTax;
    const netSaleProceeds = amountRealized - loanBalance - taxes;

    const noi = annualRent - opex - propTax - insurance;
    let pv = 0;
    for (let y = 1; y <= holdYears; y++) pv += noi / Math.pow(1 + discountRate, y);
    const exitValue = exitCap > 0 ? noi / exitCap : 0;
    const pvExit = exitValue / Math.pow(1 + discountRate, holdYears);
    const holdPV = pv + pvExit - renewalCapex;

    $('outSale').innerHTML =
      '<tr><th>Amount realized</th><td>' + money(amountRealized) + '</td></tr>' +
      '<tr><th>Adjusted basis (basis − depreciation allowed/allowable)</th><td>' + money(adjustedBasis) + '</td></tr>' +
      '<tr><th>Total gain</th><td>' + money(totalGain) + '</td></tr>' +
      '<tr><th>Unrecaptured §1250 portion (max 25%)</th><td>' + money(recaptured1250) + '</td></tr>' +
      '<tr><th>Federal 0/15/20% tax on residual gain</th><td>' + money(fedBrackets) + '</td></tr>' +
      '<tr><th>Federal §1250 tax (25% ceiling estimate)</th><td>' + money(fed1250) + '</td></tr>' +
      '<tr><th>NIIT estimate (3.8%)</th><td>' + money(niitTax) + '</td></tr>' +
      '<tr><th>California tax — progressive bracket estimate</th><td>' + money(caTax) + '</td></tr>' +
      '<tr><th>California tax — flat marginal-rate estimate (comparison)</th><td>' + money(caFlat) + '</td></tr>' +
      '<tr class="total"><th>After-tax sale proceeds (after loan payoff)</th><td>' + money(netSaleProceeds) + '</td></tr>';
    $('outHold').innerHTML =
      '<tr><th>Annual net operating income (illustrative)</th><td>' + money(noi) + '</td></tr>' +
      '<tr><th>PV of ' + holdYears + ' years of NOI</th><td>' + money(pv) + '</td></tr>' +
      '<tr><th>Illustrative exit value at ' + pct(exitCap) + ' cap</th><td>' + money(exitValue) + '</td></tr>' +
      '<tr><th>PV of exit value</th><td>' + money(pvExit) + '</td></tr>' +
      '<tr><th>Less renewal / tenant-improvement cost</th><td>' + money(-renewalCapex) + '</td></tr>' +
      '<tr class="total"><th>Hold-case present value (illustrative assumptions)</th><td>' + money(holdPV) + '</td></tr>';
    const diff = netSaleProceeds - holdPV;
    $('verdict').innerHTML = '<strong>Illustrative comparison:</strong> after-tax sale proceeds ' + money(netSaleProceeds) +
      ' vs hold-case PV ' + money(holdPV) + ' → difference ' + money(diff) +
      '. <em>Not a recommendation.</em> Every input above is an assumption until the private gates close; no winner is selected by this site.';
    $('verdict').className = 'callout warnline';
  }
  $('calcForm').addEventListener('submit', e => { e.preventDefault(); compute(); });
  $('calcForm').addEventListener('input', () => { /* no storage; recompute only on explicit submit */ });
  $('resetBtn').addEventListener('click', () => {
    $('calcForm').reset();
    $('outSale').innerHTML = '<tr><td colspan="2">Enter private inputs and press Calculate. Nothing is uploaded or stored.</td></tr>';
    $('outHold').innerHTML = '<tr><td colspan="2">Enter private inputs and press Calculate. Nothing is uploaded or stored.</td></tr>';
    $('verdict').className = 'callout neutral';
    $('verdict').textContent = 'No winner is selected. Results appear only in this browser tab after you press Calculate.';
  });
})();
</script>
"""


def build_calculator() -> str:
    def field(id_, label, default="", step="any", hint=""):
        h = f'<small>{esc(hint)}</small>' if hint else ""
        return (f'<label for="{id_}"><span>{esc(label)}</span><input id="{id_}" name="{id_}" type="number" '
                f'step="{step}" min="0" value="{esc(default)}" autocomplete="off">{h}</label>')
    content = f"""
    <div class="callout"><strong>Private by design.</strong> This calculator runs entirely in the reader's browser. It makes no network calls, sets no cookies, writes nothing to localStorage/sessionStorage and submits nothing to a server. Inputs are assumptions; official rules are listed on the <a href="tax.html">After-tax module</a>. Close the tab to discard everything.</div>
    <div class="calc-grid">
    <form id="calcForm" class="calc-form">
      <fieldset><legend>Assumptions — sale case (private)</legend>
        {field('salePrice','Assumed sale price (USD)')}{field('sellingCosts','Selling costs (USD)')}
        {field('basis','Original / adjusted cost basis (USD)','','any','Enter the private tax-file figure.')}
        {field('accumDep','Accumulated depreciation allowed or allowable (USD)','','any','IRS requires basis to be reduced by the greater of allowed or allowable depreciation.')}
        {field('loanBalance','Loan payoff (USD)')}
        {field('otherIncome','Other federal taxable income (USD)')}
        {field('caOtherTaxable','Other California taxable income (USD)')}
        {field('caMarginal','Your CA marginal rate (%)','9.3','0.1','Used only for the flat-rate comparison column.')}
        <label for="filingStatus"><span>Filing status</span><select id="filingStatus" name="filingStatus"><option value="single">Single</option><option value="mfj">Married filing jointly</option><option value="mfs">Married filing separately</option><option value="hoh">Head of household</option></select></label>
        <label for="taxYear"><span>Tax year rules</span><select id="taxYear" name="taxYear"><option value="2026">2026 (Rev. Proc. 2025-32)</option><option value="2025">2025 (IRS Topic 409)</option></select></label>
      </fieldset>
      <fieldset><legend>Assumptions — negotiated renewal / hold case (private)</legend>
        {field('annualRent','Annual base rent (USD)','','any','From the private lease abstract; blank on the public site.')}
        {field('opex','Owner-paid operating expense (USD/yr)')}{field('propTax','Property tax (USD/yr)')}{field('insurance','Insurance (USD/yr)')}
        {field('holdYears','Hold period (years)','5','1')}{field('renewalCapex','Renewal / TI cost (USD)')}
        {field('discountRate','Discount rate (%)','8','0.1','Assumption, not an observed market rate.')}
        {field('exitCap','Exit cap rate (%)','6','0.1','Assumption — the short-lease discount is NOT inferred here.')}
      </fieldset>
      <div class="calc-actions"><button class="btn primary" type="submit">Calculate locally</button><button class="btn" type="button" id="resetBtn">Reset</button></div>
    </form>
    <div class="calc-results">
      <h2>Results (this tab only)</h2>
      <h3>After-tax sale case</h3><table class="result-table"><tbody id="outSale"><tr><td colspan="2">Enter private inputs and press Calculate. Nothing is uploaded or stored.</td></tr></tbody></table>
      <h3>Renew / hold case</h3><table class="result-table"><tbody id="outHold"><tr><td colspan="2">Enter private inputs and press Calculate. Nothing is uploaded or stored.</td></tr></tbody></table>
      <div id="verdict" class="callout neutral">No winner is selected. Results appear only in this browser tab after you press Calculate.</div>
      <p class="note">Method: federal long-term brackets 0/15/20% using 2025 or 2026 thresholds; unrecaptured §1250 gain at up to 25%; 3.8% NIIT on the lesser of net investment income or MAGI excess; California capital gains as ordinary income (progressive estimate plus a flat-rate comparison). Section 1031 is not applied automatically — test it as a separate scenario. State brackets are simplified and the result is an illustration, not tax advice. See <a href="sources.html">official sources</a>.</p>
    </div>
    </div>
    """
    return page("Private browser-only calculator", "calculator", "A private calculator that runs in the reader's browser and turns verified tax rules into one number comparable with the hold case — without publishing or storing any private input.", content, extra_script=CALC_JS)


# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------
(PUBLIC / "assets" / "css").mkdir(parents=True, exist_ok=True)
(PUBLIC / "assets" / "js").mkdir(parents=True, exist_ok=True)

PAGES = {
    "index.html": build_index(), "summary.html": build_summary(), "gates.html": build_gates(),
    "questions.html": build_questions(), "economy.html": build_economy(), "operator.html": build_operator(),
    "hazards.html": build_hazards(), "tax.html": build_tax(), "calculator.html": build_calculator(),
    "risks.html": build_risks(), "suggestions.html": build_suggestions(), "sources.html": build_sources(),
    "repo-review.html": build_repo(), "flagged.html": build_flagged(), "privacy.html": build_privacy(),
    "print.html": build_print(),
}
for fn, text in PAGES.items():
    (PUBLIC / fn).write_text(text, encoding="utf-8")

# Root landing page: small, self-contained, points at web/index.html.
root_landing = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Jackbox1 — Decision support</title>
<style>body{font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f5f7fb;color:#172033;margin:0;display:grid;place-items:center;min-height:100vh}
main{max-width:620px;background:#fff;padding:40px;border-radius:20px;box-shadow:0 18px 50px rgba(20,35,70,.10);border:1px solid #e3e9f5}
h1{font-size:28px;margin:0 0 8px} p{color:#4b5875} .pill{display:inline-block;background:#e8f3ee;color:#186b4b;border-radius:99px;padding:4px 12px;font-size:13px;font-weight:600;margin-bottom:18px}
a.btn{display:inline-block;background:#194b9b;color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:700;margin-top:10px}
small{display:block;color:#6b7794;margin-top:22px}</style></head>
<body><main><span class="pill">Aggregate findings only · no identifiers</span>
<h1>Jackbox1 decision-support site</h1>
<p>Source-verified decision support for one single-tenant NNN property around central Los Angeles. No sell / renew / hold winner is selected until verified private inputs exist. Every table row links an official source; unverified values are left blank and flagged.</p>
<a class="btn" href="web/index.html">Open the dashboard →</a>
<small><a href="web/flagged.html">Flagged for Review</a> · <a href="web/sources.html">Sources</a> · <a href="web/print.html">Printable advisor summary</a></small>
</main></body></html>
"""
(OUT / "index.html").write_text(root_landing, encoding="utf-8")
(OUT / ".nojekyll").write_text("", encoding="utf-8")

print(f"Built {len(PAGES)} pages under {PUBLIC} + root landing page.")
print(f"Verified {checked_rows} table rows against {len(SOURCES)} sources. Errors: {len(errors)}")
