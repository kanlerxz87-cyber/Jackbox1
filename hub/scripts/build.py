#!/usr/bin/env python3
"""
Deterministic static-site builder for hub/** (Session S-a293043a).
Generates all 15 HTML pages inside hub/ from hub/data/sources.json and
hub/data/dataset.json with zero external CDNs or telemetry.
"""

from __future__ import annotations
import html
import json
from pathlib import Path

HUB_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = HUB_DIR / "data"

NAV_ITEMS = [
    ("index.html", "Overview"),
    ("gates.html", "W-03 Gates"),
    ("lease.html", "Lease & Notice"),
    ("trade-area.html", "W-01 Trade Area"),
    ("tenant.html", "Operator (JACK)"),
    ("valuation.html", "W-02 Tax & Quotes"),
    ("calculator.html", "Calculator"),
    ("hazards.html", "W-04 Hazards"),
    ("risks.html", "BAU & Tail Risks"),
    ("model.html", "Model & Back-Test"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged"),
    ("summary.html", "W-10 One-Pager"),
    ("sources.html", "Sources"),
]


def esc(val: object) -> str:
    return html.escape("" if val is None else str(val), quote=True)


def badge(text: str) -> str:
    t = text.strip()
    low = t.lower()
    if low in ("verified", "done"):
        cls = "badge-verified"
    elif "unverified" in low or "blocked" in low or "blank" in low or "private" in low:
        cls = "badge-unverified"
    elif low in ("urgent", "critical") or "black swan" in low:
        cls = "badge-urgent"
    elif low == "high":
        cls = "badge-high"
    elif low in ("medium", "in progress"):
        cls = "badge-medium"
    elif "proposed" in low:
        cls = "badge-proposed"
    else:
        cls = "badge-low"
    return f'<span class="badge {cls}">{esc(t)}</span>'


def blank_pill(label: str = "UNVERIFIED — PRIVATE INPUT REQUIRED") -> str:
    return f'<span class="blank-cell">{esc(label)}</span>'


def src_link(src_id: str, sources_map: dict[str, dict]) -> str:
    s = sources_map[src_id]
    title = f'{s["agency"]} — {s["title"]} (Verified {s["verified_on"]})'
    return (
        f'<a class="src-link" href="{esc(s["url"])}" target="_blank" '
        f'rel="noopener noreferrer" title="{esc(title)}">{esc(src_id)}</a>'
    )


def render_shell(
    filename: str,
    page_title: str,
    hero_h1: str,
    hero_lead: str,
    hero_tags: list[str],
    body_html: str,
    meta: dict,
    extra_scripts: str = "",
) -> str:
    nav_links = []
    for href, label in NAV_ITEMS:
        cls = ' class="active"' if href == filename else ""
        nav_links.append(f'<a href="{href}"{cls}>{esc(label)}</a>')

    tags_html = "".join(hero_tags)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page_title)} — Central LA NNN QSR Decision Hub</title>
  <link rel="stylesheet" href="assets/css/hub.css">
</head>
<body>
  <div class="privacy-bar">
    <div><strong>PRIVACY FIREWALL ACTIVE ({esc(meta["parcel_id"])}):</strong> Zero street address, APN, owner identity, lease rent, store sales, or tax basis appear in this public repository.</div>
    <div>As of <strong>{esc(meta["as_of"])}</strong> · <a href="../index.html">Repository Portal</a> · <a href="sources.html">34 Official Sources</a></div>
  </div>

  <header class="site-header">
    <div class="header-inner">
      <div class="brand-row">
        <div class="brand-title"><a href="index.html">Central LA NNN QSR — Independent Decision Hub</a></div>
        <div class="brand-meta">
          {badge(meta["decision_status"])}
          {badge("Model " + meta["model_version"])}
          <span>Verified {esc(meta["as_of"])}</span>
        </div>
      </div>
      <nav class="main-nav" aria-label="Primary sections">
        {"".join(nav_links)}
      </nav>
    </div>
  </header>

  <main class="container">
    <section class="page-hero">
      <h1>{esc(hero_h1)}</h1>
      <p class="lead">{esc(hero_lead)}</p>
      <div class="hero-tags">{tags_html}</div>
    </section>

    {body_html}
  </main>

  <footer class="site-footer">
    <div>Independent Advisory Verification Workspace ({esc(meta["owner_session"])}) · Static HTML/CSS/JS · Zero Analytics, Zero Cookies, Zero Telemetry.</div>
    <div><a href="summary.html">Printable One-Page Summary</a> · <a href="flagged.html">Flagged Repo Audit</a> · <a href="../index.html">Back to Root Portal</a></div>
  </footer>
  {extra_scripts}
</body>
</html>
"""


def collect_all_unverified(data: dict) -> list[dict]:
    items = []
    for row in data["executive"]["summary_rows"]:
        if row["status"] == "unverified":
            items.append({
                "page": "Overview",
                "href": "index.html",
                "id": "EX-PRIV",
                "item": row["item"],
                "note": row["note"],
                "source_id": row["source_id"],
            })
    for row in data["lease"]["rows"]:
        if row["status"] == "unverified":
            items.append({
                "page": "Lease & Notice",
                "href": "lease.html",
                "id": row["id"],
                "item": row["clause"],
                "note": row["verification_step"],
                "source_id": row["source_id"],
            })
    for row in data["tradearea"]["private_parcel_gaps"]:
        if row["status"] == "unverified":
            items.append({
                "page": "W-01 Trade Area",
                "href": "trade-area.html",
                "id": row["id"],
                "item": row["field"],
                "note": row["protocol"],
                "source_id": row["source_id"],
            })
    for row in data["tenant"]["private_gaps"]:
        if row["status"] == "unverified":
            items.append({
                "page": "Operator (JACK)",
                "href": "tenant.html",
                "id": row["id"],
                "item": row["field"],
                "note": row["why_critical"],
                "source_id": row["source_id"],
            })
    for row in data["valuation"]["short_lease_quotes"]:
        if row["status"] == "unverified":
            items.append({
                "page": "W-02 Tax & Quotes",
                "href": "valuation.html",
                "id": row["id"],
                "item": row["term_bucket"],
                "note": row["notes"],
                "source_id": row["source_id"],
            })
    for row in data["hazards"]["parcel_screen"]:
        if row["status"] == "unverified":
            items.append({
                "page": "W-04 Hazards",
                "href": "hazards.html",
                "id": row["id"],
                "item": row["check"],
                "note": row["action"],
                "source_id": row["source_id"],
            })
    for row in data["model"]["observations_vs_assumptions"]:
        if row["value"] is None:
            items.append({
                "page": "Model & Back-Test",
                "href": "model.html",
                "id": row["id"],
                "item": row["variable"],
                "note": row["treatment"],
                "source_id": row["source_id"],
            })
    return items


def build_index(data: dict, smap: dict) -> str:
    ex = data["executive"]
    kpis_html = []
    for k in ex["kpis"]:
        kpis_html.append(f"""
        <div class="kpi-card">
          <div>
            <div class="kpi-label">{esc(k["label"])}</div>
            <div class="kpi-value">{esc(k["value"])}</div>
            <div class="kpi-sub">{esc(k["sub"])}</div>
          </div>
          <div class="kpi-src">{badge(k["status"])} {src_link(k["source_id"], smap)}</div>
        </div>""")

    alerts_html = []
    for a in ex["alerts"]:
        cls = "alert-urgent" if a["severity"] == "URGENT" else "alert-high"
        alerts_html.append(f"""
        <div class="alert {cls}">
          <div class="alert-title">{badge(a["severity"])} <span>{esc(a["title"])}</span> {src_link(a["source_id"], smap)}</div>
          <p>{esc(a["detail"])}</p>
        </div>""")

    rows_html = []
    for r in ex["summary_rows"]:
        val_cell = blank_pill() if r["value"] is None else esc(r["value"])
        rows_html.append(f"""
        <tr>
          <td><strong>{esc(r["item"])}</strong></td>
          <td>{badge(r["status"])}</td>
          <td>{val_cell}</td>
          <td>{esc(r["note"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    gate_counts = {"Done": 0, "In Progress": 0, "Blocked — Private Input": 0, "Gated": 0}
    for g in data["gates"]:
        gate_counts[g["status"]] = gate_counts.get(g["status"], 0) + 1

    cards = [
        ("gates.html", "W-03 Decision-Gate Board", f"10 sequential gates: {gate_counts['Done']} Done, {gate_counts['In Progress']} In Progress, {gate_counts['Blocked — Private Input']} Blocked on Private Inputs, {gate_counts['Gated']} Gated."),
        ("lease.html", "Lease & Notice Calendar", "12 critical contractual fields (expiry, options, guarantor, NNN carve-outs, Prop 13 pass-through, ROFR, casualty) kept blank for privacy."),
        ("trade-area.html", "W-01 Trade Area & Macro", "Oct 2026 BLS/EDD (193.2k QSR jobs), Jan 2026 CA DOF E-1, Census SAIPE/PEP, LAUSD, SCAG 2050, AB 1228 ($20/hr), and offline tract protocol."),
        ("tenant.html", "Operator Credit (JACK)", "SEC EDGAR FY2024 through Q3 FY2026 & Nov 17, 2026 8-K: 2,115 units, -15.4% rental spread, May 2031 ARD notes, and C-suite exits."),
        ("valuation.html", "W-02 2026 Tax Rules & Quotes", "Verified 2026 IRS/FTB/BHSA/§1031/Form 3840 & Jul 1, 2026 Measure ULA ($5.4M/$10.9M) schedules + blank 3-broker quote ledger."),
        ("calculator.html", "Private Browser-Only Calculator", "100% local zero-telemetry Sell-vs-Renew / §1031 / Hold model with exact 2026 Federal, progressive CA, ULA, step-up & stress tests."),
        ("hazards.html", "W-04 Hazards & Insurance", "USGS 28 M4.5+ quakes, 88 LA FEMA declarations, CGS EQ Zapp, CAL FIRE 2025 LRA, FAIR Plan 2028 sunset, and compound stress matrix."),
        ("risks.html", "BAU & Black-Swan Risks", "Exhaustive risk matrix across all 4 strategic paths (Taxable Sale, §1031, Early Renewal, Hold-to-Expiry) covering BAU + tail shocks."),
        ("model.html", "Model & FHFA Back-Test Audit", "Observations vs. Assumptions firewall + full 51.5-year (1975–2026) FHFA HPI audit correcting prior small-sample overlap bias."),
        ("questions.html", "Known vs. Unknown Questions", "12 high-impact decision questions separating verified public facts from missing private inputs with discovery costs and timelines."),
        ("suggestions.html", "Suggestions & Decision Tracks", "4 strategic tracks and 8 concrete proposals presented cleanly for owner/reviewer selection BEFORE implementation."),
        ("flagged.html", "Flagged for Review (Repo Audit)", f"{len(data['flagged_irregularities'])} verified repo-wide irregularities & defects plus complete ledger of all blank private rows."),
    ]
    cards_html = "".join(
        f'<a class="nav-card" href="{href}"><h3>{esc(title)}</h3><p>{esc(desc)}</p></a>'
        for href, title, desc in cards
    )

    body = f"""
    <div class="kpi-grid">{"".join(kpis_html)}</div>

    <div class="alert-stack">{"".join(alerts_html)}</div>

    <section class="section">
      <h2>Executive Status Snapshot</h2>
      <p class="section-intro">Every verified public benchmark is directly linked to its primary government or SEC source as of 2026-11-26. All parcel-specific and owner-specific fields remain intentionally blank to preserve privacy; no strategic winner is declared prematurely.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Dimension</th><th>Status</th><th>Verified Baseline / Private State</th><th>Decision Relevance</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(rows_html)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Workspace Navigation — Explore by Domain</h2>
      <p class="section-intro">Navigate directly to any analytical workstream or launch the <a href="calculator.html">Private Browser-Only Calculator</a> / <a href="summary.html">W-10 Printable One-Page Advisor Summary</a>.</p>
      <div class="card-grid">{cards_html}</div>
    </section>
    """
    return render_shell(
        "index.html",
        "Executive Overview",
        "Central Los Angeles NNN QSR — Sell-Before-Expiry vs. Renew/Hold Decision Hub",
        "An independent, primary-source verified advisory workspace for evaluating a single-tenant Jack in the Box NNN lease expiring within 2030–2035. Built with strict privacy boundaries, exact 2026 tax/ULA rules, SEC filings through November 17, 2026, and zero invented parcel data.",
        [badge("Decision Open — No Winner Declared"), badge("34 Official Primary Sources"), badge("Zero Telemetry")],
        body,
        data["meta"],
    )


def build_gates(data: dict, smap: dict) -> str:
    rows = []
    for g in data["gates"]:
        rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(g["id"])}</strong></td>
          <td>{esc(g["workstream"])}</td>
          <td><strong>{esc(g["gate"])}</strong></td>
          <td>{badge(g["status"])}</td>
          <td>{esc(g["owner"])}</td>
          <td>{esc(g["completion_rule"])}</td>
          <td>{esc(g["blocking_gap"])}</td>
          <td>{src_link(g["source_id"], smap)}</td>
        </tr>""")
    body = f"""
    <section class="section">
      <h2>W-03 Decision-Gate Progress Board</h2>
      <p class="section-intro">Final sell-vs-renew commitment (Gate G-10) is intentionally blocked until Gates G-02 through G-09 clear with verified private lease, tax, hazard, operator, and broker quote inputs. Do not initiate renewal negotiations or broker listings out of sequence.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Gate</th><th>Workstream</th><th>Milestone</th><th>Status</th><th>Lead</th><th>Completion Criteria</th><th>Current Blocking Gap</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "gates.html",
        "W-03 Decision-Gate Board",
        "W-03 Decision-Gate Progress Board",
        "Sequential execution checklist preventing premature commitment, missed notice deadlines, or uncalibrated tax/valuation errors.",
        [badge("10 Sequential Gates"), badge("G-10 Gated")],
        body,
        data["meta"],
    )


def build_lease(data: dict, smap: dict) -> str:
    rows = []
    for r in data["lease"]["rows"]:
        val = blank_pill("BLANK — ABSTRACT PRIVATELY") if r["value"] is None else esc(r["value"])
        rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(r["id"])}</strong></td>
          <td><strong>{esc(r["clause"])}</strong></td>
          <td>{badge(r["status"])}</td>
          <td>{val}</td>
          <td>{esc(r["why_critical"])}</td>
          <td>{esc(r["verification_step"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")
    body = f"""
    <div class="alert alert-high">
      <div class="alert-title">{badge("Privacy Firewall")} <span>No Executed Lease Document Stored in Public Git</span></div>
      <p>{esc(data["lease"]["intro"])}</p>
    </div>
    <section class="section">
      <h2>Private Lease Abstract & Notice-Calendar Checklist (12 Mandatory Clauses)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Lease Clause / Term</th><th>Status</th><th>Parcel Value</th><th>Why It Moves Value / Leverage</th><th>Offline Verification Step</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "lease.html",
        "Lease & Notice Calendar",
        "Private Lease Abstract & Notice-Calendar Reconciliation",
        "Complete legal & financial extraction checklist for PARCEL-001. Every contractual cell stays blank in the public repository and feeds directly into Gate G-02 and the private calculator.",
        [badge("Gate G-02 Blocked — Private Input"), badge("Zero Lease Data Published")],
        body,
        data["meta"],
    )


def build_trade_area(data: dict, smap: dict) -> str:
    reg_rows = []
    for r in data["tradearea"]["regional_baselines"]:
        reg_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(r["id"])}</strong></td>
          <td><strong>{esc(r["metric"])}</strong></td>
          <td>{esc(r["geography"])}</td>
          <td class="mono">{esc(r["period"])}</td>
          <td>{badge(r["status"])}</td>
          <td class="mono"><strong>{esc(r["value"])}</strong></td>
          <td>{esc(r["context"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    priv_rows = []
    for p in data["tradearea"]["private_parcel_gaps"]:
        priv_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(p["id"])}</strong></td>
          <td><strong>{esc(p["field"])}</strong></td>
          <td>{badge(p["status"])}</td>
          <td>{blank_pill("BLANK — RUN OFFLINE ON PARCEL")}</td>
          <td>{esc(p["protocol"])}</td>
          <td>{src_link(p["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <section class="section">
      <h2>Verified Los Angeles Regional Baselines (Observations Only — Updated 2026-11-26)</h2>
      <p class="section-intro">Regional baselines frame labor demand, QSR wage pressure, inflation, population trajectory, and household formation across Los Angeles County and the City of Los Angeles. They do NOT substitute for parcel-specific 1/3/5-mile Census tracts or frontage traffic counts.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Indicator</th><th>Geography</th><th>Period</th><th>Status</th><th>Verified Figure</th><th>Underwriting Context</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(reg_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Parcel-Specific Trade-Area Intake (Intentionally Blank — Offline Assembly Protocol)</h2>
      <p class="section-intro">Zero proxy ZIP codes are fabricated here (see FLAG-10 in Flagged for Review). Assemble these 4 inputs privately using PARCEL-001's actual coordinates.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Required Parcel-Level Input</th><th>Status</th><th>Parcel Value</th><th>Official Offline Protocol</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(priv_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "trade-area.html",
        "W-01 Trade Area & Macro",
        "W-01 Trade Area Context & Los Angeles Regional Baselines",
        "Separates verified county/city labor, wage, inflation, demographic, school, and planning observations from withheld parcel-level trade-area tracts and arterial traffic counts.",
        [badge("11 Verified Macro Baselines"), badge("4 Private Parcel Inputs Blank")],
        body,
        data["meta"],
    )


def build_tenant(data: dict, smap: dict) -> str:
    kpis = []
    for k in data["tenant"]["kpis"]:
        kpis.append(f"""
        <div class="kpi-card">
          <div>
            <div class="kpi-label">{esc(k["label"])}</div>
            <div class="kpi-value">{esc(k["value"])}</div>
            <div class="kpi-sub">{esc(k["note"])}</div>
          </div>
          <div class="kpi-src">{badge("verified")} {src_link(k["source_id"], smap)}</div>
        </div>""")

    s_rows = []
    for r in data["tenant"]["series"]:
        s_rows.append(f"""
        <tr>
          <td><strong>{esc(r["period"])}</strong></td>
          <td class="mono">{esc(r["system_sss"])}</td>
          <td class="mono">{esc(r["units_end"])}</td>
          <td class="mono">{esc(r["open_close"])}</td>
          <td class="mono">{esc(r["franchise_rent_rev"])}</td>
          <td>{esc(r["key_signal"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    p_rows = []
    for p in data["tenant"]["private_gaps"]:
        p_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(p["id"])}</strong></td>
          <td><strong>{esc(p["field"])}</strong></td>
          <td>{badge(p["status"])}</td>
          <td>{blank_pill("BLANK — PRIVATE STORE AUDIT")}</td>
          <td>{esc(p["why_critical"])}</td>
          <td>{src_link(p["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <div class="kpi-grid">{"".join(kpis)}</div>

    <div class="alert alert-urgent">
      <div class="alert-title">{badge("HIGH")} <span>Critical Update Beyond Prior Repo Trees (Corrects FLAG-05)</span> {src_link("SRC-20", smap)}</div>
      <p>Earlier repository summaries stopped at Q1 FY2026 (ended Jan 18, 2026) and quoted superseded guidance. Official SEC EDGAR filings through <strong>2026-11-17</strong> document Q2/Q3 FY2026 unit contraction to 2,115 stores, -15.4% 40-week franchise net rental spread compression, $500M 2026-1 Notes maturing May 2031 ARD, dividend/buyback suspension, Mark King's May 2026 appointment as Interim CEO, the Sep 2026 GreenWood Investors extension through 2028, and the Nov 17, 2026 simultaneous planned departures of the CFO, CLO, and CTO. FY2026 Form 10-K remains unfiled as of 2026-11-26.</p>
    </div>

    <section class="section">
      <h2>Verified Corporate & Brand Trajectory — Jack in the Box Inc. (CIK 0000807882)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Reporting Period</th><th>System SSS</th><th>Ending Units</th><th>Open / Close</th><th>Franchise Rent / Margin</th><th>Key Credit & Governance Signal</th><th>SEC Filing</th></tr>
          </thead>
          <tbody>{"".join(s_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Store-Level & Counterparty Unknowns (PARCEL-001 Private Audit)</h2>
      <p class="section-intro">Corporate system stress does not automatically mean PARCEL-001 is weak—high-volume urban Central LA drive-thrus can outperform system averages. Confirm the actual store economics and legal guarantor privately.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Required Store / Guarantor Verification</th><th>Status</th><th>Parcel Value</th><th>Why It Drives Renewal Odds</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(p_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "tenant.html",
        "Operator Trends (JACK)",
        "Operator Trend Evidence — Jack in the Box Inc. (SEC EDGAR Through 2026-11-17)",
        "Multi-year and FY2026 YTD operating, rental-spread, debt-maturity, and governance trajectory verified directly from SEC EDGAR filings, separated cleanly from unknown parcel-level store sales and guarantor identity.",
        [badge("SEC Verified 2026-11-26"), badge("FY2026 10-K Pending")],
        body,
        data["meta"],
    )


def build_valuation(data: dict, smap: dict) -> str:
    t_rows = []
    for r in data["valuation"]["tax_rules_2026"]:
        t_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(r["id"])}</strong></td>
          <td><strong>{esc(r["rule"])}</strong></td>
          <td class="mono">{esc(r["rate_or_threshold"])}</td>
          <td>{esc(r["impact"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    q_rows = []
    for q in data["valuation"]["short_lease_quotes"]:
        q_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(q["id"])}</strong></td>
          <td><strong>{esc(q["term_bucket"])}</strong></td>
          <td>{badge(q["status"])}</td>
          <td>{blank_pill("BOV #1")}</td>
          <td>{blank_pill("BOV #2")}</td>
          <td>{blank_pill("BOV #3")}</td>
          <td>{blank_pill("LTV / DSCR")}</td>
          <td>{esc(q["notes"])}</td>
          <td>{src_link(q["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <div class="alert alert-info">
      <div class="alert-title">{badge("Interactive Tool")} <span>Run Exact 2026 After-Tax Math Privately</span></div>
      <p>Every statutory rule in the table below is coded directly into the zero-telemetry <a href="calculator.html"><strong>Private Sell-vs-Renew / §1031 Calculator</strong></a> — including 2026 IRS Rev. Proc. 2025-32 LTCG brackets, 25% §1250 recapture, 3.8% NIIT, progressive 2026 CA FTB Schedules X/Y/Z + 1% BHSA above $1,000,000, LA County DTT ($0.55/$500), City of LA Base ($2.25/$500 = 0.45%), and effective July 1, 2026 Measure ULA ($5.4M / $10.9M).</p>
    </div>

    <section class="section">
      <h2>Verified 2026 Federal, California, Property & Transfer Tax Rulebook</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Statutory Tax Rule</th><th>Verified 2026 Rate / Threshold</th><th>Sell-vs-Renew Financial Impact</th><th>Official Source</th></tr>
          </thead>
          <tbody>{"".join(t_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Short-Lease Market Cap-Rate & Financing Quote Ledger (Gate G-08 — Intentionally Blank)</h2>
      <p class="section-intro">Zero synthetic cap-rate spreads are invented here. Collect three dated written broker opinions of value (BOVs) and two commercial lender quotes across remaining-term buckets before finalizing valuation comparisons.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Lease-Term Valuation Bucket</th><th>Status</th><th>Broker 1</th><th>Broker 2</th><th>Broker 3</th><th>Lender Quote</th><th>Calibration Role</th><th>Anchor Source</th></tr>
          </thead>
          <tbody>{"".join(q_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "valuation.html",
        "W-02 Tax Rules & Quotes",
        "W-02 After-Tax Valuation Rulebook (2026) & Short-Lease Quote Ledger",
        "Complete verified 2026 federal, California, Los Angeles transfer-tax/ULA, §1031, Prop 13, and Prop 8 rules paired with an unfabricated broker-quote ledger.",
        [badge("2026 Statutory Rules Verified"), badge("ULA $5.4M / $10.9M Eff. Jul 1, 2026"), badge("Quotes Blank — Gate G-08")],
        body,
        data["meta"],
    )


def build_calculator(data: dict, smap: dict) -> str:
    body = f"""
    <div class="alert alert-info">
      <div class="alert-title">{badge("Zero Telemetry Verified")} <span>100% Local Browser RAM Execution</span> {src_link("SRC-23", smap)}</div>
      <p>Nothing you type here leaves your computer. <code>hub/assets/js/calculator.js</code> makes zero network calls, sets zero cookies, and writes nothing to browser storage. Refreshing the page or clicking <strong>Clear All Inputs</strong> wipes your figures instantly. <strong>No parcel numbers are pre-filled.</strong></p>
    </div>

    <div id="synthetic_warning" class="alert alert-urgent" style="display:none;">
      <div class="alert-title">{badge("SYNTHETIC TEST MODE")} <span>Hypothetical Formula-Test Numbers Loaded — NOT PARCEL-001</span></div>
      <p>These numbers are purely illustrative to verify calculator math (including Measure ULA tiering and 2026 progressive CA brackets). Replace with your real private inputs or click <strong>Clear All Inputs</strong>.</p>
    </div>

    <div class="calc-grid">
      <form id="calc_form" autocomplete="off" onsubmit="return false;">
        <div class="calc-group">
          <h3>1. Property Income, Valuation & Jurisdiction (Private Inputs)</h3>
          <div class="field-grid">
            <div class="field">
              <label for="in_noi">Current Annual NOI ($)</label>
              <input id="in_noi" type="number" step="1000" min="0" placeholder="Enter private NOI">
              <small>Net rent after any landlord expenses.</small>
            </div>
            <div class="field">
              <label for="in_sale_cap">Today's Unrenewed Sale Cap Rate (%)</label>
              <input id="in_sale_cap" type="number" step="0.05" min="1" max="20" placeholder="From Broker BOVs">
              <small>Anchor: 10-Yr Treasury = 4.91%.</small>
            </div>
            <div class="field">
              <label for="in_price_override">OR Direct Gross Sale Price Override ($)</label>
              <input id="in_price_override" type="number" step="10000" min="0" placeholder="Optional override">
              <small>Overrides NOI / Cap Rate if entered.</small>
            </div>
            <div class="field">
              <label for="in_jurisdiction">Transfer-Tax Jurisdiction</label>
              <select id="in_jurisdiction">
                <option value="city_la">City of Los Angeles (0.45% Base + ULA + 0.11% County)</option>
                <option value="uninc_la">Unincorporated LA County (0.11% County DTT only)</option>
                <option value="custom">Other LA County City (0.11% County + Custom City %)</option>
              </select>
              <small>ULA eff. 7/1/2026: 4% &gt;$5.4M, 5.5% &ge;$10.9M.</small>
            </div>
            <div class="field" id="custom_city_wrap" style="display:none;">
              <label for="in_custom_city_pct">Custom City Transfer Rate (%)</label>
              <input id="in_custom_city_pct" type="number" step="0.01" min="0" placeholder="e.g. 0.45">
              <small>Added on top of 0.11% LA County DTT.</small>
            </div>
            <div class="field">
              <label for="in_sell_cost_pct">Brokerage & Escrow Costs (%)</label>
              <input id="in_sell_cost_pct" type="number" step="0.1" min="0" max="15" placeholder="e.g. 3.0">
              <small>Excludes transfer taxes (computed separately).</small>
            </div>
          </div>
        </div>

        <div class="calc-group">
          <h3>2. Owner Tax Profile & Debt (2026 IRS + CA FTB Exact Rules)</h3>
          <div class="field-grid">
            <div class="field">
              <label for="in_filing_status">2026 Tax Filing Status</label>
              <select id="in_filing_status">
                <option value="mfj">Married Filing Jointly (MFJ)</option>
                <option value="single">Single</option>
                <option value="hoh">Head of Household (HOH)</option>
                <option value="mfs">Married Filing Separately (MFS)</option>
                <option value="trust">Irrevocable Trust / Estate</option>
              </select>
              <small>Selects exact 2026 IRS & CA FTB brackets.</small>
            </div>
            <div class="field">
              <label for="in_basis">Adjusted Tax Basis Today ($)</label>
              <input id="in_basis" type="number" step="10000" min="0" placeholder="From CPA schedule">
              <small>Original cost + capex − depreciation.</small>
            </div>
            <div class="field">
              <label for="in_depr">Accumulated §1250 Depreciation ($)</label>
              <input id="in_depr" type="number" step="10000" min="0" placeholder="0 if land/stepped-up">
              <small>Taxed up to 25% federal + CA ordinary.</small>
            </div>
            <div class="field">
              <label for="in_other_income">Other Taxable Income in Sale Year ($)</label>
              <input id="in_other_income" type="number" step="10000" min="0" placeholder="0">
              <small>Stacks gain accurately into LTCG/NIIT/BHSA.</small>
            </div>
            <div class="field">
              <label for="in_debt">Existing Mortgage Payoff ($)</label>
              <input id="in_debt" type="number" step="10000" min="0" placeholder="0 if free & clear">
              <small>Subtracted from sale &amp; terminal proceeds.</small>
            </div>
            <div class="field">
              <label for="in_prepay">Prepayment / Defeasance Penalty ($)</label>
              <input id="in_prepay" type="number" step="1000" min="0" placeholder="0">
              <small>Applies to Sale-Today scenarios.</small>
            </div>
          </div>
        </div>

        <div class="calc-group">
          <h3>3. Hold / Negotiated Renewal Path &amp; Optional Stress Test</h3>
          <div class="field-grid">
            <div class="field">
              <label for="in_rem_yrs">Remaining Primary Term (Years)</label>
              <input id="in_rem_yrs" type="number" step="1" min="0" max="20" placeholder="4 to 9 yrs">
              <small>Years left until 2030–2035 expiry.</small>
            </div>
            <div class="field">
              <label for="in_renew_yrs">Renewal / Extra Hold Years</label>
              <input id="in_renew_yrs" type="number" step="1" min="0" max="25" placeholder="0, 5, 10, 15">
              <small>Total hold horizon = Primary + Renewal.</small>
            </div>
            <div class="field">
              <label for="in_esc_pct">Annual NOI Escalation (%/yr)</label>
              <input id="in_esc_pct" type="number" step="0.1" min="-5" max="10" placeholder="e.g. 2.0">
              <small>Compare vs LA CPI-U +3.7% YoY.</small>
            </div>
            <div class="field">
              <label for="in_renew_reset_pct">Rent Reset at Renewal (%)</label>
              <input id="in_renew_reset_pct" type="number" step="1" min="-50" max="50" placeholder="0 (or -10 / +10)">
              <small>One-time step at start of renewal.</small>
            </div>
            <div class="field">
              <label for="in_renew_capex">Renewal TI / LC / Roof Capex ($)</label>
              <input id="in_renew_capex" type="number" step="5000" min="0" placeholder="0">
              <small>Out-of-pocket landlord renewal spend.</small>
            </div>
            <div class="field">
              <label for="in_cf_tax_pct">Effective Tax Rate on Annual Rent (%)</label>
              <input id="in_cf_tax_pct" type="number" step="1" min="0" max="55" placeholder="e.g. 35">
              <small>Combined Fed + CA tax on annual NOI.</small>
            </div>
            <div class="field">
              <label for="in_debt_service">Annual Debt Service ($/yr)</label>
              <input id="in_debt_service" type="number" step="1000" min="0" placeholder="0">
              <small>Annual P&amp;I if encumbered.</small>
            </div>
            <div class="field">
              <label for="in_disc_pct">After-Tax Discount Rate (%/yr)</label>
              <input id="in_disc_pct" type="number" step="0.25" min="1" max="20" placeholder="e.g. 6.5">
              <small>Anchor: 10-Yr Treasury 4.91% + risk spread.</small>
            </div>
            <div class="field">
              <label for="in_exit_cap">Terminal Exit Cap Rate (%)</label>
              <input id="in_exit_cap" type="number" step="0.05" min="2" max="20" placeholder="Same as today if blank">
              <small>Applied to Year N+1 forward NOI.</small>
            </div>
            <div class="field">
              <label for="in_stress_vac_months">Stress: Vacancy / Downtime (Months)</label>
              <input id="in_stress_vac_months" type="number" step="1" min="0" max="12" placeholder="0 (BAU)">
              <small>Lost rent at expiry/shock year.</small>
            </div>
            <div class="field">
              <label for="in_stress_repair">Stress: Uninsured Repair / EQ Deductible ($)</label>
              <input id="in_stress_repair" type="number" step="10000" min="0" placeholder="0 (BAU)">
              <small>Compound seismic / roof shock.</small>
            </div>
            <div class="field">
              <label for="in_stress_cap_bps">Stress: Exit Cap-Rate Widening (bps)</label>
              <input id="in_stress_cap_bps" type="number" step="25" min="0" max="500" placeholder="0 (BAU)">
              <small>e.g. 100 bps = +1.00% wider exit cap.</small>
            </div>
          </div>
          <div style="margin-top:0.75rem;">
            <label style="font-size:0.84rem;font-weight:600;color:#14284b;cursor:pointer;">
              <input id="in_step_up" type="checkbox" style="width:auto;margin-right:0.4rem;">
              Model IRC §1014 Estate Step-Up in Basis at End of Hold (Eliminates Terminal Income Tax; Transfer Taxes Still Apply)
            </label>
          </div>
          <div class="btn-row">
            <button type="button" id="btn_clear_calc" class="btn btn-danger">Clear All Inputs</button>
            <button type="button" id="btn_load_synthetic" class="btn btn-secondary">Test Formula With Synthetic Example (NOT Subject Parcel)</button>
          </div>
        </div>
      </form>

      <div>
        <div id="calc_status_banner" class="result-banner">
          <div class="rb-title">AWAITING PRIVATE OWNER INPUTS</div>
          <div class="rb-main">Enter NOI, Sale Cap Rate &amp; Tax Basis</div>
          <div class="rb-sub">Outputs appear live in browser memory only.</div>
        </div>

        <div class="case-grid">
          <div class="case-box">
            <h4>Case A: Sell Today (Taxable)</h4>
            <div class="cb-val" id="out_case_a">—</div>
            <div class="cb-note">Net after-tax cash in pocket today.</div>
          </div>
          <div class="case-box">
            <h4>Case B: Sell Today (§1031)</h4>
            <div class="cb-val" id="out_case_b">—</div>
            <div class="cb-note">Reinvestable equity (ULA still owed; Form 3840 tracks CA).</div>
          </div>
          <div class="case-box">
            <h4>Case C: Hold / Renew (PV)</h4>
            <div class="cb-val" id="out_case_c">—</div>
            <div class="cb-note">PV of after-tax cash flows + terminal net exit.</div>
          </div>
          <div class="case-box">
            <h4>Comparable PV Bridge (C − A)</h4>
            <div class="cb-val" id="out_bridge">—</div>
            <div class="cb-note">Break-even terminal cap: <strong id="out_breakeven_cap">—</strong></div>
          </div>
        </div>

        <div class="section" style="padding:1rem;">
          <h2 style="font-size:1.05rem;">Line-by-Line 2026 Tax &amp; Present-Value Bridge</h2>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Line Item</th><th>Computed Output</th><th>Statutory Authority</th></tr>
              </thead>
              <tbody>
                <tr><td>Implied Gross Sale Price Today</td><td class="mono" id="out_gross_price">—</td><td>{src_link("SRC-04", smap)}</td></tr>
                <tr><td>Brokerage &amp; Closing Costs</td><td class="mono" id="out_sell_cost">—</td><td>{src_link("SRC-26", smap)}</td></tr>
                <tr><td>LA County Documentary Transfer Tax ($0.55/$500)</td><td class="mono" id="out_transfer_county">—</td><td>{src_link("SRC-30", smap)}</td></tr>
                <tr><td>City of LA Base Transfer Tax ($2.25/$500 = 0.45%)</td><td class="mono" id="out_transfer_city">—</td><td>{src_link("SRC-30", smap)}</td></tr>
                <tr><td>City of LA Measure ULA (<span id="out_ula_tier">—</span>)</td><td class="mono" id="out_transfer_ula">—</td><td>{src_link("SRC-30", smap)}</td></tr>
                <tr><td>Total Taxable Gain (Realized − Basis)</td><td class="mono" id="out_total_gain">—</td><td>{src_link("SRC-24", smap)}</td></tr>
                <tr><td>Federal Unrecaptured §1250 Tax (25% Cap)</td><td class="mono" id="out_fed_1250">—</td><td>{src_link("SRC-24", smap)}</td></tr>
                <tr><td>Federal LTCG Tax (2026 Rev. Proc. 2025-32)</td><td class="mono" id="out_fed_ltcg">—</td><td>{src_link("SRC-23", smap)}</td></tr>
                <tr><td>Federal NIIT (3.8% IRC §1411)</td><td class="mono" id="out_fed_niit">—</td><td>{src_link("SRC-25", smap)}</td></tr>
                <tr><td>California Incremental Tax (2026 FTB + 1% BHSA &gt;$1M)</td><td class="mono" id="out_ca_tax">—</td><td>{src_link("SRC-27", smap)}</td></tr>
                <tr><td><strong>Total Income Taxes (Effective Rate: <span id="out_eff_rate">—</span>)</strong></td><td class="mono"><strong id="out_total_tax">—</strong></td><td>{src_link("SRC-28", smap)}</td></tr>
                <tr><td>Debt Payoff &amp; Prepayment Penalty</td><td class="mono" id="out_debt_payoff">—</td><td>{src_link("SRC-04", smap)}</td></tr>
                <tr><td><strong>Case A — Net After-Tax Cash Proceeds Today</strong></td><td class="mono"><strong id="out_net_a">—</strong></td><td>{src_link("SRC-23", smap)}</td></tr>
                <tr><td><strong>Case B — Net §1031 Reinvestable Equity Today</strong></td><td class="mono"><strong id="out_net_b">—</strong></td><td>{src_link("SRC-26", smap)}</td></tr>
                <tr><td>Case C — PV of Annual After-Tax Cash Flows (incl. Capex/Stress)</td><td class="mono" id="out_pv_cf">—</td><td>{src_link("SRC-04", smap)}</td></tr>
                <tr><td>Case C — PV of Terminal After-Tax Exit Proceeds</td><td class="mono" id="out_pv_term">—</td><td>{src_link("SRC-27", smap)}</td></tr>
                <tr><td><strong>Case C — Total Present Value (Hold / Renew Path)</strong></td><td class="mono"><strong id="out_net_c">—</strong></td><td>{src_link("SRC-05", smap)}</td></tr>
              </tbody>
            </table>
          </div>
          <p style="font-size:0.78rem;color:#6b7280;margin:0.65rem 0 0;">Advisory Notice: Planning calculator only — not legal or CPA tax advice. Confirm passive loss carryforwards, entity-level California franchise taxes, installment-sale eligibility, and Prop 13 buyer underwriting with qualified California counsel before acting.</p>
        </div>
      </div>
    </div>
    """
    return render_shell(
        "calculator.html",
        "Private Browser-Only Calculator",
        "Private Sell-vs-Renew, §1031 & Compound-Stress Calculator (2026 Tax Rules)",
        "Enter your private NOI, basis, cap-rate quotes, and stress parameters locally in browser memory. Uses exact 2026 IRS LTCG brackets, 25% §1250, 3.8% NIIT, progressive 2026 CA FTB Schedules X/Y/Z + 1% BHSA, County DTT, City Base 0.45%, and July 1, 2026 Measure ULA ($5.4M / $10.9M).",
        [badge("Zero Telemetry"), badge("2026 IRS & FTB Exact"), badge("ULA Jul 1, 2026 Active"), badge("No Fake Defaults")],
        body,
        data["meta"],
        extra_scripts='<script src="assets/js/calculator.js"></script>',
    )


def build_hazards(data: dict, smap: dict) -> str:
    r_rows = []
    for r in data["hazards"]["regional_context"]:
        r_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(r["id"])}</strong></td>
          <td><strong>{esc(r["peril"])}</strong></td>
          <td>{badge(r["status"])}</td>
          <td class="mono"><strong>{esc(r["value"])}</strong></td>
          <td>{esc(r["detail"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    p_rows = []
    for p in data["hazards"]["parcel_screen"]:
        p_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(p["id"])}</strong></td>
          <td><strong>{esc(p["check"])}</strong></td>
          <td>{badge(p["status"])}</td>
          <td>{blank_pill("BLANK — RUN ON PARCEL")}</td>
          <td>{esc(p["action"])}</td>
          <td>{src_link(p["source_id"], smap)}</td>
        </tr>""")

    c_rows = []
    for c in data["hazards"]["compound_stress"]:
        c_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(c["id"])}</strong></td>
          <td><strong>{esc(c["scenario"])}</strong></td>
          <td>{esc(c["trigger"])}</td>
          <td>{esc(c["cash_flow_impact"])}</td>
          <td>{esc(c["mitigation"])}</td>
          <td>{src_link(c["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <section class="section">
      <h2>Verified Regional Hazard &amp; California Insurance Regime (2026-11-26)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Hazard / Insurance Peril</th><th>Status</th><th>Verified Official Metric</th><th>Underwriting Context</th><th>Official Source</th></tr>
          </thead>
          <tbody>{"".join(r_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>PARCEL-001 Engineering, Hazard Zone &amp; Insurance Screen (Intentionally Blank — Gate G-05)</h2>
      <p class="section-intro">Every parcel-specific zone determination requires exact address/coordinates and must be executed offline using the linked statutory tools.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Parcel Diligence Item</th><th>Status</th><th>Parcel Result</th><th>Required Offline Verification Action</th><th>Tool / Source</th></tr>
          </thead>
          <tbody>{"".join(p_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Compound Stress Scenarios (Feed Directly Into Calculator Stress Inputs)</h2>
      <p class="section-intro">Real-world real-estate tail losses are compound: physical/insurance disruption coincides with rent loss and widened exit cap rates. Test each scenario in <a href="calculator.html">hub/calculator.html</a>.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Compound Scenario</th><th>Trigger Mechanism</th><th>Cash-Flow &amp; Capital Impact</th><th>Owner Mitigation</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(c_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "hazards.html",
        "W-04 Hazards & Insurance",
        "W-04 Parcel Hazard Screening, California Insurance Regime & Compound Stress",
        "Directly verified USGS seismic counts, CGS statutory zones, OpenFEMA LA disaster history (including Jan 2025 wildfires), CAL FIRE 2025 LRA / 2026 SRA updates, and CDI FAIR Plan limits (sunsetting Dec 31, 2028).",
        [badge("28 M4.5+ Quakes Since 1990"), badge("88 LA FEMA Declarations"), badge("Parcel Maps Blank — Gate G-05")],
        body,
        data["meta"],
    )


def build_risks(data: dict, smap: dict) -> str:
    rows = []
    for r in data["risks"]:
        rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(r["id"])}</strong></td>
          <td><strong>{esc(r["path"])}</strong></td>
          <td>{badge(r["regime"])}</td>
          <td><strong>{esc(r["risk"])}</strong></td>
          <td>{esc(r["mechanism"])}</td>
          <td>{esc(r["mitigation"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")
    body = f"""
    <section class="section">
      <h2>Complete Decision-Path Risk Register (4 Strategic Paths × BAU + Black-Swan Tail Events)</h2>
      <p class="section-intro">Every choice carries distinct downside risk—selling early exposes capital to heavy tax/ULA erosion and loss of estate step-up, whereas renewing or holding concentrates exposure to JACK corporate restructuring, AB 1228 margin compression, vacancy, and uninsured Central LA seismic shocks.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Strategic Path</th><th>Regime</th><th>Specific Risk</th><th>Economic Mechanism</th><th>Mitigation / Control</th><th>Official Source</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "risks.html",
        "BAU & Black-Swan Risks",
        "Decision-Path Risk Matrix — Business-As-Usual (BAU) & Black-Swan Shocks",
        "Side-by-side downside architecture across Taxable Sale, §1031 Exchange, Early Renewal / Blend-and-Extend, and Hold-to-Expiry / Re-Tenant / Redevelop.",
        [badge("4 Strategic Paths"), badge("BAU + Black-Swan Coverage")],
        body,
        data["meta"],
    )


def build_model(data: dict, smap: dict) -> str:
    v_rows = []
    for v in data["model"]["versions"]:
        v_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(v["version"])}</strong></td>
          <td class="mono">{esc(v["date"])}</td>
          <td>{esc(v["scope"])}</td>
          <td>{badge(v["backtest_status"])}</td>
          <td>{esc(v["gate_note"])}</td>
          <td>{src_link(v["source_id"], smap)}</td>
        </tr>""")

    oa_rows = []
    for o in data["model"]["observations_vs_assumptions"]:
        val = blank_pill("BLANK — USER PRIVATE INPUT") if o["value"] is None else esc(o["value"])
        oa_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(o["id"])}</strong></td>
          <td><strong>{esc(o["variable"])}</strong></td>
          <td>{badge(o["classification"])}</td>
          <td class="mono">{val}</td>
          <td>{esc(o["treatment"])}</td>
          <td>{src_link(o["source_id"], smap)}</td>
        </tr>""")

    bt_rows = []
    for b in data["model"]["fhfa_backtest"]:
        bt_rows.append(f"""
        <tr>
          <td><strong>{esc(b["metric"])}</strong></td>
          <td class="mono"><strong>{esc(b["result"])}</strong></td>
          <td>{esc(b["interpretation"])}</td>
          <td>{src_link(b["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <section class="section">
      <h2>Model Version Ledger &amp; Release Gates</h2>
      <p class="section-intro">No projection may be treated as decision-grade until v1.0 clears Gate G-09 with executed lease terms, private tax basis, and dated closed Central LA NNN comparable sales.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Version</th><th>Date / Trigger</th><th>Scope</th><th>Back-Test Status</th><th>Governance Rule</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(v_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Strict Firewall: Verified Observations vs. Private Inputs &amp; Assumptions</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Variable / Parameter</th><th>Classification</th><th>Current Value</th><th>Modeling Treatment</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(oa_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Independent Quantitative Back-Test Audit — FHFA Los Angeles HPI (1975 Q1–2026 Q3, 207 Quarters)</h2>
      <p class="section-intro">We independently ran Python correlation and peak-to-trough drawdown checks across the complete 51.5-year official FHFA series (<code>ATNHPIUS31084Q</code>) to audit prior repository claims (see FLAG-09). Result: cyclical mean reversion is real (r = -0.41 to -0.42), NOT r = -0.937 (which was inflated by 7 heavily overlapping 2020–2021 quarters), and historical LA downcycles inflict 21%–36% decade-long drawdowns. Crucially, FHFA HPI is a residential proxy — commercial NNN cash-flow back-testing stays BLOCKED until closed QSR comps exist.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Quantitative Back-Test Check</th><th>Verified Computation (2026-11-26)</th><th>Advisory Interpretation</th><th>Data Source</th></tr>
          </thead>
          <tbody>{"".join(bt_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "model.html",
        "Model & Back-Test Audit",
        "Versioned Cash-Flow Model Governance & FHFA 1975–2026 Back-Test Audit",
        "Enforces strict separation between verified observations, user sensitivity assumptions, and private parcel inputs, while publishing an audited 51.5-year LA cycle back-test.",
        [badge("Model v0.1-audit"), badge("Cash-Flow Back-Test Gated (v1.0)"), badge("51.5-Yr FHFA Verified")],
        body,
        data["meta"],
    )


def build_questions(data: dict, smap: dict) -> str:
    rows = []
    for q in data["questions"]:
        rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(q["id"])}</strong></td>
          <td><strong>{esc(q["category"])}</strong></td>
          <td>{esc(q["known"])}</td>
          <td><strong>{esc(q["unknown"])}</strong></td>
          <td>{esc(q["decision_impact"])}</td>
          <td>{esc(q["action"])}</td>
          <td>{src_link(q["source_id"], smap)}</td>
        </tr>""")
    body = f"""
    <section class="section">
      <h2>Known vs. Unknown Decision Questions &amp; Discovery Playbook (12 Priority Items)</h2>
      <p class="section-intro">Use this playbook to brief real-estate counsel, CPA, insurance broker, and NNN investment-sales brokers without leaking parcel identity publicly.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Domain</th><th>What Is Verified Today</th><th>What Remains Unknown (Private)</th><th>Why It Moves the Decision</th><th>Concrete Discovery Action</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "questions.html",
        "Questions & Discovery",
        "Required Information, Known-vs-Unknown Gaps & Discovery Playbook",
        "Maps every verified public anchor directly against the specific private question needed to unlock Gates G-02 through G-10.",
        [badge("12 Priority Discovery Items")],
        body,
        data["meta"],
    )


def build_suggestions(data: dict, smap: dict) -> str:
    t_rows = []
    for t in data["suggestions"]["tracks"]:
        t_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(t["id"])}</strong></td>
          <td><strong>{esc(t["name"])}</strong></td>
          <td>{esc(t["focus"])}</td>
          <td>{esc(t["pros"])}</td>
          <td>{esc(t["cons"])}</td>
          <td>{badge(t["status"])}</td>
          <td>{src_link(t["source_id"], smap)}</td>
        </tr>""")

    p_rows = []
    for p in data["suggestions"]["proposals"]:
        p_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(p["id"])}</strong></td>
          <td><strong>{esc(p["area"])}</strong></td>
          <td><strong>{esc(p["proposal"])}</strong></td>
          <td>{esc(p["benefit"])}</td>
          <td>{esc(p["cost_risk"])}</td>
          <td>{badge(p["status"])}</td>
          <td>{src_link(p["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <div class="alert alert-info">
      <div class="alert-title">{badge("Reviewer Approval Required")} <span>Suggestions Presented Before Implementation</span></div>
      <p>No strategic track or cross-scope repository change has been pre-adopted. Review the four strategic tracks and eight concrete proposals below and select which items to authorize next.</p>
    </div>

    <section class="section">
      <h2>Strategic Execution Tracks (Choose Sequence After Gate G-02 / G-06)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Strategic Track</th><th>Execution Sequence</th><th>Key Advantages</th><th>Key Trade-Offs</th><th>Status</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(t_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Concrete Process, Modeling &amp; Repository Proposals</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Area</th><th>Proposal</th><th>Expected Benefit</th><th>Cost / Governance Note</th><th>Status</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(p_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "suggestions.html",
        "Suggestions & Reviewer Menu",
        "Suggestions, Strategic Tracks & Proposed Next Actions (For Review Before Implementation)",
        "Clear, neutral choice architecture laying out strategic sequencing tracks, immediate tax/diligence proposals, and cross-repository cleanup options for owner/reviewer selection.",
        [badge("4 Strategic Tracks"), badge("8 Concrete Proposals"), badge("No Pre-Adopted Winner")],
        body,
        data["meta"],
    )


def build_flagged(data: dict, smap: dict) -> str:
    irr_rows = []
    for f in data["flagged_irregularities"]:
        irr_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(f["id"])}</strong></td>
          <td>{badge(f["severity"])}</td>
          <td class="mono" style="font-size:0.78rem;">{esc(f["locations"])}</td>
          <td>{esc(f["defect"])}</td>
          <td><strong>{esc(f["verified_correction"])}</strong></td>
          <td>{esc(f["hub_status"])}</td>
          <td>{src_link(f["source_id"], smap)}</td>
        </tr>""")

    unv = collect_all_unverified(data)
    unv_rows = []
    for u in unv:
        unv_rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(u["id"])}</strong></td>
          <td><a href="{esc(u["href"])}">{esc(u["page"])}</a></td>
          <td><strong>{esc(u["item"])}</strong></td>
          <td>{badge("unverified")}</td>
          <td>{esc(u["note"])}</td>
          <td>{src_link(u["source_id"], smap)}</td>
        </tr>""")

    body = f"""
    <section class="section">
      <h2>Part 1 — Line-by-Line Repository Audit: 14 Verified Irregularities &amp; Defects (2026-11-26)</h2>
      <p class="section-intro">Every item below was verified directly against official primary sources on 2026-11-26 during our full audit of all 8 existing repository trees. All corrections are live inside <code>hub/**</code>; legacy sibling directories remain untouched per multi-session scope ownership rules in <code>COORDINATION.md</code> (see PROP-02 to authorize repo-wide remediation).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Severity</th><th>Verified File Locations</th><th>Defect / Irregularity Found</th><th>Official Primary-Source Correction</th><th>Status in hub/**</th><th>Official Source</th></tr>
          </thead>
          <tbody>{"".join(irr_rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Part 2 — Complete Ledger of All Blank / Unverified Private Rows Across hub/** ({len(unv)} Rows)</h2>
      <p class="section-intro">Auto-aggregated from <code>hub/data/dataset.json</code> so zero hidden gaps exist anywhere in the workspace. Every row below carries <code>value = null</code> by privacy design.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Page</th><th>Blank Private Field</th><th>Status</th><th>Resolution Protocol</th><th>Reference Source</th></tr>
          </thead>
          <tbody>{"".join(unv_rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "flagged.html",
        "Flagged for Review",
        "Flagged for Review — Repository Audit Irregularities & Unverified Ledger",
        "Complete transparency register surfacing all 14 concrete arithmetic, statutory, SEC-staleness, privacy-leak, and back-test defects discovered in existing repo files alongside every intentionally blank private field.",
        [badge("14 Repo Defects Logged"), badge(f"{len(unv)} Private Rows Blank by Design")],
        body,
        data["meta"],
    )


def build_summary(data: dict, smap: dict) -> str:
    ex = data["executive"]
    kpis = "".join(
        f'<div class="kpi-card"><div><div class="kpi-label">{esc(k["label"])}</div>'
        f'<div class="kpi-value">{esc(k["value"])}</div><div class="kpi-sub">{esc(k["sub"])}</div></div>'
        f'<div class="kpi-src">{src_link(k["source_id"], smap)}</div></div>'
        for k in ex["kpis"]
    )
    rows = []
    for r in ex["summary_rows"]:
        val = blank_pill("PRIVATE — OFFLINE") if r["value"] is None else esc(r["value"])
        rows.append(f"""
        <tr>
          <td><strong>{esc(r["item"])}</strong></td>
          <td>{badge(r["status"])}</td>
          <td>{val}</td>
          <td>{esc(r["note"])}</td>
          <td>{src_link(r["source_id"], smap)}</td>
        </tr>""")

    checklist = [
        ("1. Immediate (Before 2026-11-30)", "Tax Counsel / Owner", "Check 2026–27 property tax bill for LA County Prop 8 Decline-in-Value (Form RP-87) eligibility before window closes Nov 30, 2026.", "SRC-29"),
        ("2. Weeks 1–2 (Gate G-02 / G-03)", "Real Estate Counsel", "Abstract executed lease: exact expiry, option notice windows, fixed vs FMV reset, corporate vs franchisee guarantor, NNN carve-outs, Prop 13 pass-through, ROFR, and City of LA ULA jurisdiction.", "SRC-30"),
        ("3. Weeks 2–3 (Gate G-06 / G-07)", "CPA + Owner", "Pull adjusted basis, accumulated §1250 depreciation, entity/estate step-up horizon, debt payoff, and store-level gross sales; run hub/calculator.html locally.", "SRC-28"),
        ("4. Weeks 3–5 (Gate G-08 / G-05)", "3 Brokers + Engineer", "Collect 3 written broker BOVs (3/5/7/15-yr WALT & vacant land) + lender quotes; run offline CGS EQ Zapp, FEMA NFHL, CAL FIRE 2025 LRA, and Property/EQ insurance review.", "SRC-32"),
        ("5. Week 6+ (Gate G-09 / G-10)", "Owner + Advisors", "Promote model to v1.0 after comp calibration; select Track A/B/C/D (Sell Taxable vs §1031 vs Early Renewal vs Hold-to-Expiry).", "SRC-05"),
    ]
    chk_rows = "".join(
        f'<tr><td class="mono"><strong>{esc(t)}</strong></td><td>{esc(o)}</td><td>{esc(a)}</td><td>{src_link(s, smap)}</td></tr>'
        for t, o, a, s in checklist
    )

    body = f"""
    <div class="btn-row no-print" style="margin-bottom:1rem;">
      <button type="button" class="btn btn-primary" onclick="window.print()">Print / Save One-Page PDF</button>
      <a class="btn btn-secondary" href="calculator.html">Open Private Calculator</a>
      <a class="btn btn-secondary" href="flagged.html">View 14 Flagged Repo Findings</a>
    </div>

    <div class="kpi-grid">{kpis}</div>

    <section class="section">
      <h2>Executive Briefing — Sell Before Expiry vs. Renew/Hold (As of 2026-11-26)</h2>
      <p class="section-intro"><strong>Decision Status: OPEN (No Winner Declared).</strong> Public macro, 2026 tax/ULA, hazard, and Jack in the Box SEC filings (through 2026-11-17) are verified. Parcel address, APN, executed lease, tax basis, and broker cap-rate quotes are withheld from public Git by design.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Dimension</th><th>Status</th><th>Verified Fact / Private State</th><th>Advisor Note</th><th>Source</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2>Immediate 6-Week Advisor Action Sequence</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Window</th><th>Lead Advisor</th><th>Action Item</th><th>Primary Source</th></tr>
          </thead>
          <tbody>{chk_rows}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "summary.html",
        "W-10 One-Page Advisor Summary",
        "W-10 Printable One-Page Advisor Briefing — Central LA NNN QSR (PARCEL-001)",
        "Board-ready, privacy-clean summary for briefing real-estate counsel, CPA, NNN brokers, and lenders. Zero parcel identifiers or unverified estimates included.",
        [badge("Print-Optimized"), badge("Zero PII / Parcel IDs"), badge("Verified 2026-11-26")],
        body,
        data["meta"],
    )


def build_sources(data: dict, sources_list: list[dict], smap: dict) -> str:
    rows = []
    for s in sources_list:
        rows.append(f"""
        <tr>
          <td class="mono"><strong>{esc(s["id"])}</strong></td>
          <td>{esc(s["category"])}</td>
          <td><strong>{esc(s["agency"])}</strong></td>
          <td><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a></td>
          <td class="mono">{esc(s["verified_on"])}</td>
          <td>{esc(s["notes"])}</td>
        </tr>""")
    body = f"""
    <section class="section">
      <h2>Master Official Primary-Source Register ({len(sources_list)} Verified Sources — 2026-11-26)</h2>
      <p class="section-intro">Every single data table row across all 15 pages in <code>hub/**</code> links directly to one of the official federal, state, county, municipal, or statutory regional agency URLs below. Zero commercial blogs, broker marketing decks, or unverified third-party aggregators are permitted.</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>ID</th><th>Category</th><th>Issuing Agency</th><th>Document / Data Series (Direct Official Link)</th><th>Verified</th><th>Verified Key Figures &amp; Notes</th></tr>
          </thead>
          <tbody>{"".join(rows)}</tbody>
        </table>
      </div>
    </section>
    """
    return render_shell(
        "sources.html",
        "Official Primary Sources",
        "Master Official Primary-Source Register (34 Verified Sources)",
        "Complete audit trail of every official government, Federal Reserve, SEC EDGAR, and regional planning source verified on 2026-11-26.",
        [badge("34 Official Primary Sources"), badge("100% Allowlisted Gov / Fed / SEC Domains")],
        body,
        data["meta"],
    )


def main() -> None:
    sources_doc = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    data = json.loads((DATA_DIR / "dataset.json").read_text(encoding="utf-8"))
    sources_list = sources_doc["sources"]
    smap = {s["id"]: s for s in sources_list}

    pages = {
        "index.html": build_index(data, smap),
        "gates.html": build_gates(data, smap),
        "lease.html": build_lease(data, smap),
        "trade-area.html": build_trade_area(data, smap),
        "tenant.html": build_tenant(data, smap),
        "valuation.html": build_valuation(data, smap),
        "calculator.html": build_calculator(data, smap),
        "hazards.html": build_hazards(data, smap),
        "risks.html": build_risks(data, smap),
        "model.html": build_model(data, smap),
        "questions.html": build_questions(data, smap),
        "suggestions.html": build_suggestions(data, smap),
        "flagged.html": build_flagged(data, smap),
        "summary.html": build_summary(data, smap),
        "sources.html": build_sources(data, sources_list, smap),
    }

    for fname, content in pages.items():
        (HUB_DIR / fname).write_text(content, encoding="utf-8")

    print(f"Built {len(pages)} HTML pages in {HUB_DIR} using {len(sources_list)} official sources.")


if __name__ == "__main__":
    main()
