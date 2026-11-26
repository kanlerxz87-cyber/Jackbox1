#!/usr/bin/env python3
"""Build the outlook module pages from outlook/data/*.json (standard library only).

Usage:  python3 outlook/tools/build.py            write outlook/*.html
        python3 outlook/tools/build.py --stdout   print a dict of page names -> sizes (used by check.py)
Output is deterministic: no timestamps other than the fixed retrieval date.
"""
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, RETRIEVED, load_all, derived_values, fmt_num, EXTRA_HOSTS  # noqa: E402

E = html.escape
PAGES = [
    ("index", "Overview", "Summary, key figures, gate status"),
    ("projections", "Projections", "Official county projections and a vintage check"),
    ("drivers", "Drivers and dates", "Dated events and area drivers"),
    ("peers", "Tenant and peers", "Tenant-brand and peer sales trends"),
    ("options", "Options", "Every option with everyday and black-swan risks"),
    ("risks", "Black swans", "Shock events and how they propagate"),
    ("wealth", "Owner wealth levers", "Official rules that shape after-tax outcomes"),
    ("rules", "Decision rules", "Gates, conditional rules, no-regret actions"),
    ("questions", "Questions", "Known and unknown, with ways to find out"),
    ("suggestions", "Suggestions", "Paths a reviewer picks before anything is built"),
    ("workflow", "Private workflow", "How the location is used without entering Git"),
    ("flagged", "Flagged for review", "Irregularities with source links"),
    ("sources", "Sources", "Every source, how it was retrieved"),
]


class Ctx:
    def __init__(self):
        self.d = load_all()
        self.src = {s["id"]: s for s in self.d["sources"]["sources"]}
        self.flags = {f["id"]: f for f in self.d["flags"]["flags"]}
        self.dv = derived_values(self.d)

    # ----- cells -----
    def srcs(self, ids):
        if not ids:
            return ""
        out = []
        for i in ids:
            s = self.src[i]
            out.append(f'<a href="{E(s["url"])}" title="{E(s["publisher"])}: {E(s["title"])}">{i}</a> '
                       f'<span class="m m-{s["method"]}">{s["method"]}</span>')
        return "<br>".join(out)

    def flag(self, fid):
        if not fid:
            return ""
        return f'<a class="flag" href="flagged.html#{fid}" title="{E(self.flags[fid]["title"])}">{fid}</a>'

    def ref_cell(self, row):
        """Reference cell: source links, else a visible blank marker with a flag link."""
        s = self.srcs(row.get("src", []))
        f = self.flag(row.get("flag"))
        if not row.get("src"):
            return f'<span class="blank">no official source exists for this item</span> {f}'.strip()
        return (s + (" " + f if f else "")).strip()


def table(caption, heads, rows, cls=""):
    th = "".join(f'<th scope="col">{h}</th>' for h in heads)
    body = "".join(rows)
    return (f'<div class="tw"><table class="{cls}"><caption>{E(caption)}</caption>'
            f'<thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>')


def tr(rid, cells, cls=""):
    c = "".join(cells)
    idattr = f' id="{rid}"' if rid else ""
    clsattr = f' class="{cls}"' if cls else ""
    return f"<tr{idattr}{clsattr}>{c}</tr>"


def td(x, cls=""):
    return f'<td class="{cls}">{x}</td>' if cls else f"<td>{x}</td>"


def kind_badge(kind):
    return f'<span class="k k-{kind}">{kind}</span>'


# ---------------- charts (inline SVG, no scripts, no inline CSS) ----------------
_SVG = [0]


def _sid():
    _SVG[0] += 1
    return f"svg{_SVG[0]}"


def bar_svg(title, desc, items, width=640, bar_h=26, vmin=None, vmax=None, unit="%"):
    """Horizontal bars centred on zero. items: [(label, value or None, note)]"""
    vals = [v for _, v, _ in items if v is not None]
    lo = min(vals + [0]) if vmin is None else vmin
    hi = max(vals + [0]) if vmax is None else vmax
    lo, hi = lo - 1.0, hi + 1.0
    label_w, pad = 230, 40
    plot_w = width - label_w - pad
    zero_x = label_w + (0 - lo) / (hi - lo) * plot_w
    h = 30 + bar_h * len(items) + 14
    sid = _sid()
    parts = [f'<svg class="chart" role="img" aria-labelledby="{sid}t {sid}d" viewBox="0 0 {width} {h}">'
             f'<title id="{sid}t">{E(title)}</title><desc id="{sid}d">{E(desc)}</desc>',
             f'<line x1="{zero_x:.1f}" y1="20" x2="{zero_x:.1f}" y2="{h-8}" stroke="#444" stroke-width="1"/>']
    for n, (label, v, note) in enumerate(items):
        y = 26 + n * bar_h
        parts.append(f'<text x="{label_w-8}" y="{y+15}" text-anchor="end" font-size="12" fill="#1a1a1a">{E(label)}</text>')
        if v is None:
            parts.append(f'<text x="{zero_x+8:.1f}" y="{y+15}" font-size="12" fill="#8a1c1c">blank: not yet published</text>')
            continue
        x0 = label_w + (min(v, 0) - lo) / (hi - lo) * plot_w
        w = abs(v) / (hi - lo) * plot_w
        col = "#1b6b3a" if v >= 0 else "#a02323"
        parts.append(f'<rect x="{x0:.1f}" y="{y+3}" width="{max(w,1):.1f}" height="{bar_h-9}" fill="{col}"/>')
        tx = (x0 + w + 6) if v >= 0 else (x0 - 6)
        anchor = "start" if v >= 0 else "end"
        parts.append(f'<text x="{tx:.1f}" y="{y+16}" text-anchor="{anchor}" font-size="12" fill="#1a1a1a">{fmt_num(v, unit, signed=True, decimals=1)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def line_svg(title, desc, pts, width=640, height=220):
    """pts: [(year, value)] connected, y axis from min to max."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    padl, padr, padt, padb = 74, 16, 14, 28
    pw, ph = width - padl - padr, height - padt - padb

    def X(x): return padl + (x - x0) / (x1 - x0) * pw

    def Y(y): return padt + (1 - (y - y0) / (y1 - y0)) * ph
    path = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in pts)
    sid = _sid()
    parts = [f'<svg class="chart" role="img" aria-labelledby="{sid}t {sid}d" viewBox="0 0 {width} {height}">'
             f'<title id="{sid}t">{E(title)}</title><desc id="{sid}d">{E(desc)}</desc>',
             f'<line x1="{padl}" y1="{padt}" x2="{padl}" y2="{height-padb}" stroke="#444"/>',
             f'<line x1="{padl}" y1="{height-padb}" x2="{width-padr}" y2="{height-padb}" stroke="#444"/>',
             f'<polyline fill="none" stroke="#0b4f8a" stroke-width="2" points="{path}"/>']
    for x, y in pts:
        parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="3" fill="#0b4f8a"/>')
        parts.append(f'<text x="{X(x):.1f}" y="{height-10}" text-anchor="middle" font-size="11" fill="#1a1a1a">{x}</text>')
    for v in (y0, (y0 + y1) / 2, y1):
        parts.append(f'<text x="{padl-6}" y="{Y(v)+4:.1f}" text-anchor="end" font-size="11" fill="#1a1a1a">{v/1e6:.2f}M</text>')
    parts.append("</svg>")
    return "".join(parts)


# ---------------- page shell ----------------
def shell(slug, title, lead, body, ctx):
    cur = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{s}.html"{cur if s == slug else ""}>{E(n)}</a></li>' for s, n, _ in PAGES)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<meta name="robots" content="noindex">
<title>{E(title)} | Outlook and Options module</title>
<link rel="stylesheet" href="assets/outlook.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<p class="brand"><a href="index.html">Outlook and Options module</a> <span class="tag">session S-f6ebb740</span></p>
<p class="crumbs"><a href="../index.html">Main site</a> &middot; <a href="../pages/index.html">Primary analysis pages</a> &middot; <a href="../COORDINATION.md">Coordination board</a></p>
<nav aria-label="Module pages"><ul>{nav}</ul></nav>
</header>
<main id="main">
<h1>{E(title)}</h1>
<p class="lead">{lead}</p>
{body}
</main>
<footer>
<p>Public page. No address, parcel number, owner, lease, rent, basis or coordinate appears in this module; the parcel is called PARCEL-001 and its location is never stored here.
Built from <code>outlook/data/*.json</code> by <code>outlook/tools/build.py</code>; source retrieval date {RETRIEVED}. Not investment, tax or legal advice.</p>
</footer>
</body>
</html>
"""


def legend():
    return ('<p class="legend"><strong>Row kinds.</strong> '
            f'{kind_badge("observation")} an official-source fact with value, vintage and quote or cell locator. '
            f'{kind_badge("derived")} computed by the build script from observations. '
            f'{kind_badge("framework")} analyst reasoning for a reviewer to challenge; it cites an official page only as context. '
            f'{kind_badge("process")} a step or rule; no official source exists for it. '
            f'{kind_badge("blank")} unverified: left empty and flagged. Nothing is inferred.</p>')


# ---------------- pages ----------------
def page_projections(c):
    p = c.d["projections"]
    idx = {r["id"]: r for k in ("pop_rows", "k12_rows", "rev_rows") for r in p[k]}
    out = [f'<p>{E(p["meta"]["scope"])} {E(p["meta"]["reading_rule"])}</p>', legend()]

    # population
    rows = []
    for r in p["pop_rows"]:
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["label"])), td(r["period"]), td(fmt_num(r["raw"], "people"), "num"),
                                 td(E(r.get("locator") or r.get("excerpt", ""))), td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    out.append("<h2 id=\"pop\">1. Population: DOF baseline and the Census estimate</h2>")
    out.append(table("Observed values from the California Department of Finance P-2A file and the Census Bureau",
                     ["ID", "Series", "Year", "Value", "Locator or quote", "Kind", "Source"], rows))
    pts = [(int(r["period"]), r["raw"]) for r in p["pop_rows"][:9]]
    out.append(line_svg("Los Angeles County total population, DOF baseline",
                        "Line chart of DOF July 1 population for Los Angeles County: 2020 to 2025, then projected 2030, 2035 and 2040.", pts))
    out.append('<p class="cap">Chart: Los Angeles County total population from rows P-01 to P-09 (DOF Baseline 2024, Vintage 2026). Years 2026 to 2029 and 2031 to 2034 exist in the file but are not plotted.</p>')
    drows = []
    for d in [x for x in p["derived"] if x["group"] in ("pop", "check")]:
        unit = d["unit"]
        drows.append(tr(d["id"], [td(d["id"]), td(E(d["label"])), td(", ".join(d["inputs"])), td(fmt_num(c.dv[d["id"]], unit, signed=True), "num"),
                                  td(kind_badge("derived")), td(c.ref_cell(d))]))
    out.append("<h2 id=\"pop-derived\">2. Computed changes and cross-check</h2>")
    out.append(table("Derived from the rows above (build-script arithmetic)", ["ID", "Measure", "Inputs", "Result", "Kind", "Source"], drows))

    # employment
    rows = []
    for r in p["emp_rows"]:
        chg = r["proj"] - r["base"]
        pct = chg / r["base"] * 100
        ok = (chg == r["chg_pub"]) and (round(pct, 1) == r["pct_pub"])
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["label"]) + f' <small>(NAICS {E(r["code"])})</small>'),
                                 td(fmt_num(r["base"], "jobs"), "num"), td(fmt_num(r["proj"], "jobs"), "num"),
                                 td(fmt_num(r["chg_pub"], "jobs", signed=True), "num"),
                                 td(fmt_num(r["pct_pub"], "%", signed=True, decimals=1), "num"),
                                 td(fmt_num(pct, "%", signed=True, decimals=1) + (" &#10003;" if ok else " MISMATCH"), "num"),
                                 td(kind_badge(r["kind"])), td(c.ref_cell(r) + f'<br><small>{E(r["locator"])}</small>')]))
    out.append("<h2 id=\"jobs\">3. County employment projections, 2023 to 2033 (EDD)</h2>")
    out.append("<p>Jobs located in Los Angeles County (place of work), annual-average base year 2023. County-wide: not a trade-area figure. EDD notes projections for previous periods are not always comparable to the latest ones "
               + c.flag("OL-F02") + ".</p>")
    out.append(table("Los Angeles-Long Beach-Glendale MD industry employment projections (published April 2026)",
                     ["ID", "Industry", "2023 base", "2033 projected", "Change (published)", "% (published)", "% (recomputed)", "Kind", "Source"], rows))

    # k12
    rows = []
    for r in p["k12_rows"]:
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["label"])), td(r["period"]), td(fmt_num(r["raw"], "students", signed=r["raw"] < 0), "num"),
                                 td("&ldquo;" + E(r["excerpt"]) + "&rdquo;"), td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    d9 = [x for x in p["derived"] if x["id"] == "D-09"][0]
    rows.append(tr(d9["id"], [td(d9["id"]), td(E(d9["label"])), td("10 years"), td(fmt_num(c.dv["D-09"], "%", signed=True), "num"),
                              td("computed from K-01 and K-02"), td(kind_badge("derived")), td(c.ref_cell(d9))]))
    out.append("<h2 id=\"k12\">4. Public school enrollment (DOF 2026 Series, August 2026)</h2>")
    out.append(table("Public K-12 enrollment projection highlights", ["ID", "Measure", "Period", "Value", "Quote", "Kind", "Source"], rows))

    # vintage check
    out.append("<h2 id=\"vintage\">5. How far did an earlier official projection move? (illustrative, not a validated back-test)</h2>")
    out.append("<p>An LAUSD analyst's 2019 slides quote DOF's May 2019 county projection. This table sets that path beside DOF's current series. "
               "<strong>Limits:</strong> the 2019 values are second-hand and rounded; the &lsquo;current&rsquo; series is DOF's own revised estimate, not an independent count; there are only five annual points. "
               + c.flag("OL-F03") + "</p>")
    rows = []
    for yr, rid, did in [(2021, "R-02", "D-14"), (2022, "R-03", "D-15"), (2023, "R-04", "D-16"), (2024, "R-05", "D-17"), (2025, "R-06", "D-18")]:
        proj = idx[rid]["raw"]
        cur = c.dv[did]
        rows.append(tr(f"vint-{yr}", [td(str(yr)), td(fmt_num(proj, "%", signed=True), "num", ), td(fmt_num(cur, "%", signed=True), "num"),
                                       td(fmt_num(cur - proj, "%", signed=True) .replace("%", " pts"), "num"),
                                       td(f"{rid}, {did}"), td(kind_badge("derived")), td(c.srcs(["OL-S06", "OL-S02"]) + " " + c.flag("OL-F03"))]))
    out.append(table("Annual change in Los Angeles County population: 2019-vintage projection versus DOF's current series",
                     ["Year", "2019 vintage (as quoted)", "DOF current series", "Gap", "Rows", "Kind", "Source"], rows))
    drows = []
    for d in [x for x in p["derived"] if x["group"] == "rev" and x["id"] in ("D-10", "D-11", "D-12", "D-13")]:
        drows.append(tr(d["id"], [td(d["id"]), td(E(d["label"])), td(", ".join(d["inputs"])), td(fmt_num(c.dv[d["id"]], d["unit"], signed=True), "num"),
                                  td(kind_badge("derived")), td(c.ref_cell(d))]))
    r1 = idx["R-01"]
    drows.insert(0, tr("R-01", [td("R-01"), td(E(r1["label"])), td("quote"), td(fmt_num(r1["raw"], "people") + " (approx.)", "num"),
                                td(kind_badge("observation")), td(c.ref_cell(r1) + "<br><small>&ldquo;" + E(r1["excerpt"]) + "&rdquo;</small>")]))
    out.append(table("Size of the revision", ["ID", "Measure", "Inputs", "Result", "Kind", "Source"], drows))
    out.append(bar_svg("Cumulative change in Los Angeles County population, 2020 to 2024",
                       "Two bars: the 2019-vintage path compounded over 2021 to 2024, and DOF's current series.",
                       [("2019 vintage path (as quoted)", c.dv["D-12"], ""), ("DOF current series", c.dv["D-13"], "")], unit="%"))

    # blanks
    rows = []
    for b in p["blank"]:
        rows.append(tr(b["id"], [td(b["id"]), td(E(b["label"])), td('<span class="blank">blank: unverified</span>'), td(E(b["why"])),
                                 td(E(b["how_to_fill"])), td(c.srcs(b["src"]) + " " + c.flag(b["flag"]))]))
    out.append("<h2 id=\"gaps\">6. Not retrieved: left blank on purpose</h2>")
    out.append(table("Blank rows", ["ID", "Item", "Value", "Why blank", "How to fill", "Context and flag"], rows))
    return "Projections", ("Official county and state projections for population, jobs and school enrollment, "
                           "plus a check on how much an earlier county projection moved. County level only."), "".join(out)


def page_drivers(c):
    d = c.d["drivers"]
    out = [legend()]
    rows = []
    for r in d["calendar"]:
        refcell = c.ref_cell(r) if r["kind"] != "blank" else (f'<span class="blank">blank: unverified</span> {c.flag(r["flag"])}' + ((" " + c.srcs(r["src"])) if r["src"] else ""))
        quote = ("&ldquo;" + E(r["excerpt"]) + "&rdquo;") if r.get("excerpt") else (f'<span class="blank">{E(r.get("how_to_fill", ""))}</span>')
        note = f'<br><small>{E(r["note"])}</small>' if r.get("note") else ""
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["when"] or "date not stated")), td(r["status"]), td(E(r["event"])),
                                 td(E(r["why"]) + note), td(quote), td(kind_badge(r["kind"])), td(refcell)]))
    out.append("<h2 id=\"dates\">1. Dated events</h2>")
    out.append(table("Calendar of events inside any sale or renewal timeline", ["ID", "When", "Status", "Event", "Why it matters", "Quote or how to fill", "Kind", "Source"], rows))
    rows = []
    for r in d["drivers"]:
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["driver"])), td(E(r["known"])), td(E(r["unknown"])),
                                 td("&ldquo;" + E(r.get("excerpt", "")) + "&rdquo;" if r.get("excerpt") else E(r.get("locator", ""))),
                                 td(c.ref_cell(r))]))
    out.append("<h2 id=\"drivers\">2. Area drivers: what is known and what is not</h2>")
    out.append(table("Drivers", ["ID", "Driver", "Known from official sources", "Unknown", "Quote or locator", "Source"], rows))
    return "Drivers and dates", "Dated events in the next decade and the area forces that could matter, with what is known kept apart from what is not.", "".join(out)


def page_peers(c):
    p = c.d["peers"]
    byid = {r["id"]: r for r in p["rows"]}
    out = [f'<p>{E(p["meta"]["scope"])}</p>', f'<p class="note">{E(p["meta"]["definition_note"])}</p>', legend()]
    jack = [("Q4 FY2025", byid["PR-09"]["raw"], ""), ("Q1 FY2026", byid["PR-10"]["raw"], ""), ("Q2 FY2026", byid["PR-11"]["raw"], ""),
            ("Q3 FY2026", byid["PR-12"]["raw"], ""), ("Q4 FY2026 (due 2026-12-09)", None, "")]
    out.append(bar_svg("Jack in the Box system same-store sales, five fiscal quarters",
                       "Bars for Q4 FY2025 to Q3 FY2026 show -7.4, -6.7, -3.8 and -1.1 percent. Q4 FY2026 is blank until 2026-12-09.", jack))
    out.append('<p class="cap">Chart: rows PR-09 to PR-13. Same-store sales are year-over-year changes at restaurants open more than 18 months, as the company reports them.</p>')
    snap = [("Burger King U.S., Q3 2026", byid["PR-07"]["raw"], ""), ("McDonald's U.S., Q3 2026", byid["PR-01"]["raw"], ""),
            ("Jack in the Box, Q3 FY2026*", byid["PR-12"]["raw"], ""), ("Wendy's U.S., Q3 2026", byid["PR-04"]["raw"], "")]
    out.append(bar_svg("Latest reported U.S. sales trend, four burger brands",
                       "Burger King U.S. +8.4 percent, McDonald's U.S. -0.2, Jack in the Box -1.1, Wendy's U.S. -5.7. Periods and definitions differ.", snap))
    out.append('<p class="cap">Chart: rows PR-07, PR-01, PR-12, PR-04. *Jack in the Box&rsquo;s Q3 FY2026 ended 2026-07-05; the others ended 2026-09-27 or 2026-09-30. Compare direction, not level.</p>')
    rows = []
    for r in p["rows"]:
        if r["kind"] == "blank":
            rows.append(tr(r["id"], [td(r["id"]), td(E(r["brand"])), td(E(r["period"])), td(E(r["metric"])), td('<span class="blank">blank: unverified</span>'), td(""),
                                     td("<span class=\"blank\">" + E(r["how_to_fill"]) + "</span>"), td(kind_badge("blank")), td(c.srcs(r["src"]) + " " + c.flag(r["flag"]))]))
            continue
        prior = fmt_num(r["prior"], "%", signed=True, decimals=1) if r["prior"] is not None else '<span class="blank">not in excerpt</span>'
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["brand"])), td(E(r["period"])), td(E(r["metric"])),
                                 td(fmt_num(r["raw"], "%", signed=True, decimals=1), "num"), td(prior, "num"),
                                 td("&ldquo;" + E(r["excerpt"]) + "&rdquo;"), td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    out.append("<h2 id=\"series\">1. Sales trend rows</h2>")
    out.append(table("Same-store, same-restaurant and comparable sales, year over year", ["ID", "Brand", "Period", "Measure", "Value", "Prior-year period", "Quote", "Kind", "Source"], rows))
    rows = []
    for r in p["ops"]:
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["brand"])), td(E(r["period"])), td(E(r["item"])), td(E(r["value"])),
                                 td("&ldquo;" + E(r["excerpt"]) + "&rdquo;"), td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    out.append("<h2 id=\"ops\">2. Tenant-brand operating facts</h2>")
    out.append(table("Jack in the Box operating facts beyond sales", ["ID", "Brand", "Period", "Item", "Value", "Quote", "Kind", "Source"], rows))
    out.append('<p class="note">Brand-level facts say nothing about this unit&rsquo;s sales, rent coverage or lease. Those are private (gates G-02 and G-03).</p>')
    return "Tenant and peers", "Direction of the tenant brand's sales and how three other burger brands compare. Brand-level only.", "".join(out)


def page_options(c):
    o = c.d["options"]
    out = [f'<p class="banner">{E(o["meta"]["no_winner"])}</p>', f'<p class="note">{E(o["meta"]["framework_rule"])}</p>', legend()]
    rows = []
    for r in o["options"]:
        rows.append(tr(r["id"], [td(f'<strong>{r["id"]}</strong><br>{E(r["name"])}<br>{kind_badge(r["kind"])}'),
                                 td(E(r["what"]) + "<br><strong>Verify first:</strong> " + E(r["needs"])),
                                 td(E(r["bau"])), td(E(r["swan"])), td(E(r["owner"])), td(c.ref_cell(r))]))
    out.append(table("Ten options for the property and the owner",
                     ["Option", "What it is and what to verify first", "Everyday risks", "Black-swan exposure", "Owner-level effect", "Context reference"], rows, "wide"))
    out.append('<p>Compare options only on one basis: after-tax, same date, probability-weighted, with the stress set on the <a href="rules.html">Decision rules</a> page.</p>')
    return "Options", "Sell now, sell later, renew, short extension, re-tenant, redevelop, exchange, installment, hold, or hold for heirs: what each needs and risks. No winner.", "".join(out)


def page_risks(c):
    o = c.d["options"]
    out = [legend()]
    rows = []
    for r in o["swan"]:
        q = ("&ldquo;" + E(r["excerpt"]) + "&rdquo;<br>") if r.get("excerpt") else ""
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["event"])), td(E(r["propagation"])), td(E(r["verify"])),
                                 td(q + E(r["evidence"])), td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    out.append(table("Shock events and how each reaches a single-tenant net-lease owner", ["ID", "Event", "How it propagates", "What to verify (parcel-specific, private)", "Evidence seen", "Kind", "Source"], rows, "wide"))
    out.append("<h2 id=\"compound\">Compound stress</h2><p>SW-12 is the test the owner asked for: loss of rent, repair cost and an illiquid exit <em>together</em>. "
               "It is defined, not computed: months of lost rent, repair cost net of insurance, and an exit discount are all private inputs. See <a href=\"rules.html#RULE-4\">RULE-4</a>.</p>")
    return "Black-swan events", "Earthquake, wildfire, flood, tenant failure and other shocks, with how each propagates to the owner and what to verify.", "".join(out)


def page_wealth(c):
    o = c.d["options"]
    out = [legend()]
    rows = []
    for r in o["wealth"]:
        if r["kind"] == "blank":
            rows.append(tr(r["id"], [td(r["id"]), td(E(r["lever"])), td('<span class="blank">blank: unverified</span>'), td(E(r["why"]) + "<br><em>How to fill:</em> " + E(r["how_to_fill"])),
                                     td(kind_badge("blank")), td(c.srcs(r["src"]) + " " + c.flag(r["flag"]))]))
        else:
            rows.append(tr(r["id"], [td(r["id"]), td(E(r["lever"])), td(E(r["fact"]) + "<br>&ldquo;" + E(r["excerpt"]) + "&rdquo;"), td(E(r["why"])),
                                     td(kind_badge(r["kind"])), td(c.ref_cell(r))]))
    out.append(table("Official rules that change after-tax outcomes for an individual owner", ["ID", "Lever", "What the official page says", "Why it matters (and what is unknown)", "Kind", "Source"], rows, "wide"))
    out.append("<p>Not tax or legal advice. Every lever needs the owner's private facts (rows W-08 to W-12) and a qualified adviser before use.</p>")
    return "Owner wealth levers", "What official sources say about basis, estate exclusion, reassessment, exchange and installment sales, kept apart from the owner's private facts.", "".join(out)


def page_rules(c):
    w = c.d["workflow"]
    out = [legend(), '<p class="banner">Default while any gate is open: make no irreversible commitment. Gates closed: 0 of 9.</p>']
    rows = [tr(g["id"], [td(g["id"]), td(E(g["gate"])), td(E(g["pass_when"])), td(g["status"]), td(kind_badge(g["kind"])), td(c.ref_cell(g))]) for g in w["gates"]]
    out.append("<h2 id=\"gates\">1. Decision gates (progress board)</h2>")
    out.append(table("Nine gates that must close before any sell-versus-renew winner is shown", ["ID", "Gate", "Passes when", "Status", "Kind", "Reference"], rows))
    rows = [tr(r["id"], [td(r["id"]), td(E(r["title"])), td(E(r["text"])), td(kind_badge(r["kind"])), td(c.ref_cell(r))]) for r in w["rules"]]
    out.append("<h2 id=\"rules\">2. Conditional rules and break-evens</h2>")
    out.append(table("Rules (all inputs blank until verified)", ["ID", "Rule", "Text", "Kind", "Reference"], rows))
    rows = [tr(r["id"], [td(r["id"]), td(E(r["action"])), td(E(r["why"])), td(kind_badge(r["kind"])), td(c.ref_cell(r))]) for r in w["no_regret"]]
    out.append("<h2 id=\"noregret\">3. No-regret actions</h2>")
    out.append(table("Actions that make sense under every option", ["ID", "Action", "Why", "Kind", "Reference"], rows))
    rows = []
    for r in w["worksheet"]:
        rows.append(tr(r["id"], [td(r["id"]), td(E(r["case"])), td(E(r["line"])), td('<span class="blank">blank: unverified</span>'),
                                 td(E(r["how_to_fill"])), td(kind_badge("blank")), td((c.srcs(r["src"]) + " " if r["src"] else "") + c.flag(r["flag"]))]))
    out.append("<h2 id=\"worksheet\">4. Blank side-by-side worksheet: after-tax sale next to a negotiated renewal</h2>")
    out.append("<p>Every value is blank on purpose. The two cases use one date, one set of tax assumptions and the same units (RULE-1). Do not enter private figures on this public page: complete a private copy offline.</p>")
    out.append(table("After-tax comparison worksheet (template)", ["ID", "Case", "Line", "Value", "How to fill", "Kind", "Reference and flag"], rows))
    return "Decision rules", "Nine gates, conditional rules and break-evens, a blank side-by-side worksheet, and the actions worth taking whichever way the decision goes. No winner is shown.", "".join(out)


def page_questions(c):
    w = c.d["workflow"]
    out = [legend()]
    rows = []
    for q in w["questions"]:
        ans = E(q["answer"]) if q["answer"] else '<span class="blank">blank: unverified</span>'
        loc = f'<br><small>{E(q["locator"])}</small>' if q.get("locator") else ""
        rows.append(tr(q["id"], [td(q["id"]), td(E(q["q"])), td(f'<span class="st st-{q["status"]}">{q["status"]}</span>'), td(ans + loc),
                                 td(E(q["discover"])), td(c.ref_cell(q))]))
    known = sum(1 for q in w["questions"] if q["status"] == "known")
    partly = sum(1 for q in w["questions"] if q["status"] == "partly")
    unk = sum(1 for q in w["questions"] if q["status"] == "unknown")
    out.insert(0, f'<p>{len(w["questions"])} questions: {known} known, {partly} partly known, {unk} unknown. Unknown means no official or private source has been read yet.</p>')
    out.append(table("Questions, information and answers needed before a decision", ["ID", "Question", "Status", "Answer so far", "How to find out", "Reference"], rows, "wide"))
    return "Questions", "What is known, partly known and unknown, with a way to discover each missing item.", "".join(out)


def page_suggestions(c):
    w = c.d["workflow"]
    rows = []
    for s in w["suggestions"]:
        rows.append(tr(s["id"], [td(s["id"]), td(E(s["path"])), td(E(s["what"])), td(E(s["cost"])), td(E(s["benefit"])), td(E(s["risk"])),
                                 td(E(s["if_chosen"])), td(c.ref_cell(s))]))
    body = ('<p class="banner">Nothing in this table has been implemented. A reviewer picks one or more paths by replying with the IDs (for example &ldquo;SUG-1, SUG-3&rdquo;) in the pull request conversation. These suggestions do not pick a sell-versus-renew winner.</p>'
            + legend()
            + table("Paths for a reviewer to choose from", ["ID", "Path", "What", "Cost", "Benefit", "Risk", "If chosen", "Reference"], rows, "wide"))
    return "Suggestions", "Seven paths, with cost, benefit and risk, for a reviewer to pick before anything further is built.", body


WORKFLOW_STEPS = [
    ("Step 0", "Create the git-ignored private folder and a location file", "Owner creates private/location.json with a latitude and longitude. The scripts refuse to run unless private/ is ignored by git.", "Nothing", ["OL-S29"]),
    ("Step 1", "step1_trade_area_tracts.py: choose trade-area tracts offline", "Reads the public Census Gazetteer tract file you downloaded, measures the distance from the location to each tract's internal point, and writes rings (default 1, 3, 5 miles) to private/out/. Approximation: a tract is chosen by its internal point, not by boundary overlap.", "Nothing leaves the machine", ["OL-S29"]),
    ("Step 2 (optional)", "step2_confirm_tract.py: confirm the containing tract", "Default is a dry run that prints a masked request. With --online it sends ONE request to the Census Geocoder and stores the tract in private/out/.", "Dry run: nothing. --online: the coordinates go to a Census server, which may log them", ["OL-S26"]),
    ("Step 3", "step3_acs_tracts.py: ACS 5-year metrics for the tracts", "Asks the Census API for a whole county (never for the parcel), checks every variable label first, filters to your tracts locally, and writes a private per-tract file plus a public-safe aggregate. The aggregate is refused if it covers fewer than ten tracts and never contains tract IDs.", "A county-wide request and your API key; no location", ["OL-S27", "OL-S28"]),
    ("Step 4", "step4_hazard_checklist.py: parcel hazard checklist", "Writes a blank private checklist of official viewers (flood, fire, seismic) for you to complete by hand. No automated lookup is enabled because the flood service failed and the fire service is stale.", "Nothing", ["OL-S33", "OL-S32", "OL-S31"]),
    ("Self-test", "selftest.py: offline tests", "Checks the privacy guards, distance maths, file parsing, margin-of-error arithmetic, the ten-tract rule and that no coordinate is ever printed. Uses synthetic data only.", "Nothing", ["OL-S26"]),
]


def page_workflow(c):
    rows = [tr(f"step-{i}", [td(f"<strong>{E(a)}</strong>"), td(E(b)), td(E(cc)), td(E(dd)), td(c.srcs(ids))]) for i, (a, b, cc, dd, ids) in enumerate(WORKFLOW_STEPS)]
    cmds = ("<pre>python3 private-workflow/step1_trade_area_tracts.py --gazetteer PATH_TO_GAZETTEER_ZIP --county 06037\n"
            "python3 private-workflow/step2_confirm_tract.py            # dry run\n"
            "CENSUS_API_KEY=YOUR_KEY python3 private-workflow/step3_acs_tracts.py --vintage 2024\n"
            "python3 private-workflow/step4_hazard_checklist.py\n"
            "python3 private-workflow/selftest.py</pre>")
    ep = [
        ("Census Geocoder, geographies by coordinates", "Verified 2026-11-26 with a public landmark: the response holds the tract under result.geographies['Census Tracts'].", "verified shape", ["OL-S26"]),
        ("Census Data API (ACS 5-year)", "Needs a key (confirmed). Variable metadata endpoints answered without a key; two labels were checked and the script re-checks all at run time.", "verified; key required", ["OL-S27", "OL-S28"]),
        ("Census Gazetteer tract files", "Official page opened; files are pipe-delimited text with internal-point coordinates, based on 2020 tracts.", "verified", ["OL-S29"]),
        ("FEMA National Flood Hazard Layer service", "HTTP 500 on two URL forms. Not used.", "failed", ["OL-S30"]),
        ("CAL FIRE fire severity service on services.gis.ca.gov", "Layer list shows 2007 and DRAFT boundaries. Not used.", "stale, not used", ["OL-S35"]),
    ]
    erows = [tr(f"ep-{i}", [td(E(a)), td(E(b)), td(E(s)), td(c.srcs(ids))]) for i, (a, b, s, ids) in enumerate(ep)]
    body = (legend() + "<p class=\"banner\">The location never enters the repository. Public code, private data: the scripts live in <code>private-workflow/</code>; their inputs and outputs live in the git-ignored <code>private/</code> folder.</p>"
            + "<h2 id=\"steps\">1. Steps</h2>" + table("Private workflow steps", ["Step", "What it does", "How", "What leaves the machine", "Official source"], rows)
            + "<h2 id=\"cmds\">2. Commands</h2>" + cmds
            + "<h2 id=\"endpoints\">3. Endpoint verification</h2>" + table("What was checked and what failed", ["Endpoint", "Result", "Status", "Source"], erows)
            + "<h2 id=\"rules\">4. Privacy design</h2><ul>"
              "<li>Refuses to run unless <code>private/</code> is git-ignored; refuses to write outside it.</li>"
              "<li>Never prints coordinates; progress messages show counts only.</li>"
              "<li>Public aggregates need at least ten tracts and carry no tract IDs.</li>"
              "<li>Median values cannot be added across tracts. The aggregate reports the spread of tract medians and labels it as such; sums and ratios of counts are exact up to survey margins.</li>"
              "<li>Compare vintages only when the tract IDs match; the script reports tracts missing from a vintage instead of guessing a crosswalk.</li>"
              "<li>The API key comes from an environment variable and is never written to disk.</li></ul>"
            + "<p>Residual risk: the optional online step discloses the location to a government server. Skip it if that matters; step 1 alone gives an approximate tract set.</p>")
    return "Private workflow", "How the parcel location can be used to pick consistent census tracts and screen hazards on the owner's own machine, so no location reaches Git or this website.", body


def page_flagged(c):
    rows = []
    for f in c.d["flags"]["flags"]:
        ev = "<br>".join(f'<a href="{E(c.src[i]["url"])}">{i}</a> <span class="m m-{c.src[i]["method"]}">{c.src[i]["method"]}</span>' for i in f["evidence"]) or '<span class="blank">none: private input</span>'
        rows.append(tr(f["id"], [td(f"<strong>{f['id']}</strong>"), td(f'<span class="sev sev-{f["severity"]}">{f["severity"]}</span>'),
                                 td(f'<strong>{E(f["title"])}</strong><br>{E(f["finding"])}'), td(ev), td(E(f["action"])), td(f["status"])]))
    rr = []
    for r in c.d["flags"]["repo_review"]:
        rr.append(tr(r["id"], [td(r["id"]), td(f'<a href="{E(r["url"])}">{E(r["file"])}</a>'), td(E(r["check"])), td(c.flag(r["flag"]))]))
    return ("Flagged for review",
            "Irregularities and unverified items found in this module, each with source links. None blocks publication; each needs a human look.",
            "".join([legend(), table("Flagged items", ["ID", "Severity", "Finding", "Source links", "Action", "Status"], rows, "wide"),
                     "<h2 id=\"repo\">Repository files to review by hand</h2>",
                     table("Repository review links (GitHub, main branch)", ["ID", "File", "What to check", "Flag"], rr)]))


def page_sources(c):
    rows = []
    for s in c.d["sources"]["sources"]:
        rows.append(tr(s["id"], [td(f"<strong>{s['id']}</strong>"), td(E(s["publisher"])), td(f'<a href="{E(s["url"])}">{E(s["title"])}</a>'), td(E(s["vintage"])),
                                 td(f'<span class="m m-{s["method"]}">{s["method"]}</span>'), td(E(s["tier"])), td(E(s["used_for"]))]))
    note = E(c.d["sources"]["note"])
    return ("Sources", f"Every source used or tried, with how this session retrieved it. {note}",
            table("Source register", ["ID", "Publisher", "Page", "Vintage", "Retrieval", "Tier", "Used for"], rows, "wide"))


def page_index(c):
    p = c.d["projections"]
    peers = {r["id"]: r for r in c.d["peers"]["rows"]}
    w = c.d["workflow"]
    dv = c.dv
    emp = {r["id"]: r for r in p["emp_rows"]}
    k12 = {r["id"]: r for r in p["k12_rows"]}
    tiles = [
        (fmt_num(dv["D-03"], "%", signed=True), "Los Angeles County population, 2025 to 2035 (DOF baseline)", ["OL-S02"], "projections.html#D-03"),
        (fmt_num(dv["D-04"], "%", signed=True), "California population, 2025 to 2035 (DOF baseline)", ["OL-S02"], "projections.html#D-04"),
        (fmt_num(emp["E-08"]["pct_pub"], "%", signed=True, decimals=1), "County restaurant jobs, 2023 to 2033 (EDD)", ["OL-S04"], "projections.html#E-08"),
        (fmt_num(abs(k12["K-04"]["raw"]), "students"), "Projected county K-12 enrollment decline, 2025-26 to 2035-36 (DOF)", ["OL-S05"], "projections.html#K-04"),
        (fmt_num(peers["PR-12"]["raw"], "%", signed=True, decimals=1), "Tenant brand same-store sales, Q3 FY2026 (Q4 FY2025 was " + fmt_num(peers["PR-09"]["raw"], "%", signed=True, decimals=1) + ")", ["OL-S16", "OL-S18"], "peers.html#PR-12"),
        ("2026-12-09", "Tenant brand reports full-year FY2026 results (after market close)", ["OL-S19"], "drivers.html#CAL-03"),
    ]
    tl = "".join(f'<li class="tile"><span class="big">{E(v)}</span><span class="lbl">{E(l)}</span>'
                 f'<span class="tsrc">{c.srcs(ids)} &middot; <a href="{href}">row</a></span></li>' for v, l, ids, href in tiles)
    gates_open = sum(1 for g in w["gates"] if g["status"] == "open")
    kinds = {}
    for grp in [p["pop_rows"], p["emp_rows"], p["k12_rows"], p["rev_rows"], c.d["drivers"]["calendar"], c.d["drivers"]["drivers"], c.d["peers"]["rows"], c.d["peers"]["ops"],
                c.d["options"]["options"], c.d["options"]["wealth"], c.d["options"]["swan"], w["gates"], w["rules"], w["no_regret"], w["questions"], w["suggestions"], w["worksheet"], p["blank"]]:
        for r in grp:
            k = r.get("kind", "blank")
            kinds[k] = kinds.get(k, 0) + 1
    kinds["derived"] = kinds.get("derived", 0) + len(p["derived"])
    counts = " &middot; ".join(f'{k}: {kinds[k]}' for k in ("observation", "derived", "framework", "process", "blank") if k in kinds)
    nav = "".join(f'<li><a href="{s}.html">{E(n)}</a>: {E(desc)}</li>' for s, n, desc in PAGES if s != "index")
    summary = [
        f"<li><strong>Area demand is mixed, county-wide.</strong> DOF's baseline has Los Angeles County at {fmt_num(dv['D-03'], '%', signed=True)} from 2025 to 2035 while California is {fmt_num(dv['D-04'], '%', signed=True)}; DOF projects the largest county K-12 enrollment drop in the state ({fmt_num(abs(k12['K-04']['raw']), 'students')}). EDD projects county jobs {fmt_num(emp['E-01']['pct_pub'], '%', signed=True, decimals=1)} and restaurant jobs {fmt_num(emp['E-08']['pct_pub'], '%', signed=True, decimals=1)} (2023 to 2033). These are county figures, not trade-area figures.</li>",
        f"<li><strong>Treat projections as wide scenarios.</strong> DOF's 2019 vintage (as quoted) had about 10.8 million for 2030; the current baseline has {fmt_num(p['pop_rows'][6]['raw'], 'people')}. That is about {fmt_num(dv['D-11'], '%', signed=True, decimals=1)} in five years (illustrative; see flag OL-F03).</li>",
        f"<li><strong>Tenant brand is improving but still negative.</strong> System same-store sales ran {fmt_num(peers['PR-09']['raw'], '%', signed=True, decimals=1)}, {fmt_num(peers['PR-10']['raw'], '%', signed=True, decimals=1)}, {fmt_num(peers['PR-11']['raw'], '%', signed=True, decimals=1)} and {fmt_num(peers['PR-12']['raw'], '%', signed=True, decimals=1)} over the last four reported periods, with closures and higher bad-debt expense noted. Peers diverge: Burger King U.S. {fmt_num(peers['PR-07']['raw'], '%', signed=True, decimals=1)}, McDonald's U.S. {fmt_num(peers['PR-01']['raw'], '%', signed=True, decimals=1)}, Wendy's U.S. {fmt_num(peers['PR-04']['raw'], '%', signed=True, decimals=1)}. Full-year results arrive 2026-12-09.</li>",
        "<li><strong>Owner-level rules are official but owner facts are blank.</strong> Inherited property generally takes a value-at-death basis; the 2026 federal exclusion is $15,000,000; the California parent-child exclusion does not cover commercial property; Section 1031 is real property only; installment sales still recognize recapture in the sale year. Basis, estate and liquidity facts are private.</li>",
        f"<li><strong>No sell-versus-renew winner.</strong> {gates_open} of {len(w['gates'])} decision gates are open. The lease, tenant strength, buyer quotes, after-tax figures and parcel hazards are all unverified.</li>",
        "<li><strong>Two dates need attention.</strong> The property-tax decline-in-value window closes Monday 2026-11-30 (applicability unknown); the tenant brand reports on 2026-12-09.</li>",
    ]
    body = ('<p class="banner">No sell-versus-renew winner is selected. Decision gates closed: 0 of ' + str(len(w["gates"])) +
            '. A reviewer chooses a path on the <a href="suggestions.html">Suggestions</a> page before anything further is implemented.</p>'
            + f'<ul class="tiles">{tl}</ul>'
            + "<h2 id=\"summary\">Executive summary</h2><ul>" + "".join(summary) + "</ul>"
            + f'<h2 id="status">Evidence status</h2><p>Rows by kind across the module: {counts}. Flagged items: {len(c.d["flags"]["flags"])} (<a href="flagged.html">see list</a>).</p>'
            + legend()
            + "<h2 id=\"pages\">Pages</h2><ul>" + nav + "</ul>"
            + "<h2 id=\"scope\">Scope and overlap</h2><p>This module adds forward-looking official evidence, peer series, an options and wealth framework, and a private location workflow. It does not replace the tenant series on <code>data/tenant.json</code>, the hazard, tax and calculator work of other sessions, or the root landing page. See also the <a href=\"../hub/index.html\">decision hub</a> (including its <a href=\"../hub/calculator.html\">calculator</a>), listed for navigation and not re-verified here. See flag OL-F16.</p>")
    return "Overview", "Forward-looking official evidence, tenant and peer trends, and a no-winner options framework for one single-tenant net-lease restaurant property in central Los Angeles.", body


BUILDERS = {"index": page_index, "projections": page_projections, "drivers": page_drivers, "peers": page_peers, "options": page_options,
            "risks": page_risks, "wealth": page_wealth, "rules": page_rules, "questions": page_questions, "suggestions": page_suggestions,
            "workflow": page_workflow, "flagged": page_flagged, "sources": page_sources}


def build_all():
    _SVG[0] = 0
    c = Ctx()
    out = {}
    for slug, _n, _d in PAGES:
        res = BUILDERS[slug](c)
        title, lead, body = res
        out[slug] = shell(slug, title, lead, body, c)
    return out


def main():
    pages = build_all()
    if "--stdout" in sys.argv:
        for k, v in pages.items():
            print(k, len(v))
        return
    for slug, text in pages.items():
        (ROOT / f"{slug}.html").write_text(text, encoding="utf-8")
    print(f"built {len(pages)} pages into {ROOT}")


if __name__ == "__main__":
    main()
