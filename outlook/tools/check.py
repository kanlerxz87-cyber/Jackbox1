#!/usr/bin/env python3
"""Validate the outlook module: data rules, built HTML, links, privacy. Standard library only.

  python3 outlook/tools/check.py              run all checks against the committed files
  python3 outlook/tools/check.py --selftest   prove the checker rejects bad input (negative tests)
Exit status 0 = pass, 1 = fail.
"""
import copy
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402
from common import ROOT, load_all, host_ok  # noqa: E402

REPO = ROOT.parent
KINDS = {"observation", "derived", "framework", "process", "blank"}
METHODS = {"opened", "excerpt", "failed", "other-session"}
READ = {"opened", "excerpt"}

PRIVACY = [
    (re.compile(r"\b\d{4}\s+(?:[NSEW]\s+)?[A-Z][a-z]+\s+(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway)\b"), "street address"),
    (re.compile(r"\b\d{3}-\d{3}-\d{3}\b"), "APN-style number"),
    (re.compile(r"\b\d{4}-\d{3}-\d{3}\b"), "LA assessor-style parcel number"),
    (re.compile(r"(?:ZIP|ZIP\s*Code|Postal)\s*[:#]?\s*\d{5}\b", re.I), "ZIP with label"),
    (re.compile(r"\b[A-Za-z ]+,\s*CA\s+9\d{4}\b"), "city, state, ZIP"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "email address"),
    (re.compile(r"\b\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"), "phone number"),
    (re.compile(r"\b(?:SSN|social security)\b", re.I), "social security reference"),
    (re.compile(r"\b\d{2}-\d{7}\b"), "EIN pattern"),
    (re.compile(r"\b(?:LLC|LP|Inc\.?)\s*#?\s*\d"), "entity plus number"),
    (re.compile(r"(?<![\d.])-?\d{2,3}\.\d{4,}\b"), "coordinate-like decimal"),
    (re.compile(r"\b90015\b"), "ZIP 90015 (known stale reference)"),
]
BAD_TAGS = re.compile(r"<\s*(script|form|input|iframe|object|embed|button|textarea|select)\b|javascript:|\son[a-z]+\s*=|\sstyle\s*=", re.I)


# ------------------------------------------------------------------ data rules
def groups(d):
    p, dr, pe, op, wf = d["projections"], d["drivers"], d["peers"], d["options"], d["workflow"]
    return {
        "pop_rows": p["pop_rows"], "emp_rows": p["emp_rows"], "k12_rows": p["k12_rows"], "rev_rows": p["rev_rows"], "proj_blank": p["blank"],
        "calendar": dr["calendar"], "drivers": dr["drivers"], "peer_rows": pe["rows"], "peer_ops": pe["ops"],
        "options": op["options"], "wealth": op["wealth"], "swan": op["swan"],
        "gates": wf["gates"], "rules": wf["rules"], "no_regret": wf["no_regret"], "questions": wf["questions"], "suggestions": wf["suggestions"],
    }


def check_data(d):
    errs = []
    srcs = {s["id"]: s for s in d["sources"]["sources"]}
    flags = {f["id"]: f for f in d["flags"]["flags"]}
    if len(srcs) != len(d["sources"]["sources"]):
        errs.append("duplicate source ids")
    for s in srcs.values():
        if not s["url"].startswith("https://"):
            errs.append(f'{s["id"]}: source URL is not https')
        if not host_ok(s["url"]):
            errs.append(f'{s["id"]}: host not on the official allowlist: {urlparse(s["url"]).hostname}')
        if s["method"] not in METHODS:
            errs.append(f'{s["id"]}: bad retrieval method {s["method"]}')
        for k in ("publisher", "title", "vintage", "tier", "used_for"):
            if not s.get(k):
                errs.append(f'{s["id"]}: missing {k}')
    for gname, rows in groups(d).items():
        seen = set()
        for r in rows:
            rid = r["id"]
            if rid in seen:
                errs.append(f"{gname}: duplicate row id {rid}")
            seen.add(rid)
            kind = r.get("kind", "blank")
            if kind not in KINDS:
                errs.append(f"{rid}: bad kind {kind}")
            ids = r.get("src", [])
            for i in ids:
                if i not in srcs:
                    errs.append(f"{rid}: unknown source {i}")
            if r.get("flag") and r["flag"] not in flags:
                errs.append(f'{rid}: unknown flag {r["flag"]}')
            if kind == "observation":
                if not ids:
                    errs.append(f"{rid}: observation without a source")
                elif not any(srcs[i]["method"] in READ for i in ids if i in srcs):
                    errs.append(f"{rid}: observation whose sources were never read (failed or other-session only)")
                if not (r.get("excerpt") or r.get("locator")):
                    errs.append(f"{rid}: observation without a quote or locator")
                if r.get("excerpt") and len(r["excerpt"]) > 420:
                    errs.append(f"{rid}: excerpt too long to be a quote")
            if kind in ("framework", "process") and not ids and not r.get("flag"):
                errs.append(f"{rid}: {kind} row with no official reference and no flag")
            if kind == "blank":
                if not r.get("flag"):
                    errs.append(f"{rid}: blank row without a flag")
                for vf in ("raw", "fact", "answer", "value"):
                    if r.get(vf) not in (None, ""):
                        errs.append(f"{rid}: blank row carries a value in '{vf}'")
                if not (r.get("how_to_fill") or r.get("discover")):
                    errs.append(f"{rid}: blank row without a way to fill it")
    # arithmetic checks
    p = d["projections"]
    idx = {r["id"]: r["raw"] for k in ("pop_rows", "k12_rows", "rev_rows") for r in p[k]}
    for r in p["emp_rows"]:
        chg = r["proj"] - r["base"]
        if chg != r["chg_pub"]:
            errs.append(f'{r["id"]}: published change {r["chg_pub"]} != projected-base {chg}')
        if round(chg / r["base"] * 100, 1) != r["pct_pub"]:
            errs.append(f'{r["id"]}: published percent {r["pct_pub"]} != recomputed {round(chg / r["base"] * 100, 1)}')
    if idx["K-01"] + idx["K-03"] != idx["K-02"]:
        errs.append("K-12: K-01 + K-03 != K-02")
    for dd in p["derived"]:
        for i in dd["inputs"]:
            if i not in idx and i not in {x["id"] for x in p["derived"]}:
                errs.append(f'{dd["id"]}: unknown input {i}')
    # independent recomputation of the headline derived values
    exp = {"D-03": (idx["P-08"] - idx["P-06"]) / idx["P-06"] * 100, "D-04": (idx["P-12"] - idx["P-10"]) / idx["P-10"] * 100,
           "D-06": idx["P-06"] - idx["P-13"], "D-10": idx["P-07"] - idx["R-01"]}
    got = build.Ctx().dv if d is not None else {}
    for k, v in exp.items():
        if abs(got.get(k, 1e99) - v) > 1e-6:
            errs.append(f"{k}: build value {got.get(k)} differs from independent recomputation {v}")
    return errs


# ------------------------------------------------------------------ html rules
class Scan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.rows, self.tables = [], [], [], 0
        self._row, self._in_tbody, self.h1, self.meta_csp, self.lang, self.main, self.titles = None, False, 0, False, False, False, 0
        self.captions, self.th_scope = 0, 0
        self._svg = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "svg":
            self._svg += 1
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "meta" and a.get("http-equiv", "").lower() == "content-security-policy":
            self.meta_csp = True
        if tag == "main" and a.get("id") == "main":
            self.main = True
        if tag == "h1":
            self.h1 += 1
        if tag == "title" and not self._svg:
            self.titles += 1
        if tag == "table":
            self.tables += 1
        if tag == "caption":
            self.captions += 1
        if tag == "th" and a.get("scope") == "col":
            self.th_scope += 1
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._row = {"id": a.get("id"), "links": [], "blank": False}
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self._row is not None:
                self._row["links"].append((a["href"], a.get("class", "")))
        if tag == "link" and a.get("href"):
            self.links.append(a["href"])
        if self._row is not None and "blank" in (a.get("class") or "").split():
            self._row["blank"] = True

    def handle_endtag(self, tag):
        if tag == "svg" and self._svg:
            self._svg -= 1
        if tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None
        if tag == "tbody":
            self._in_tbody = False


def check_html(pages):
    errs = []
    allids = {}
    scans = {}
    for slug, text in pages.items():
        sc = Scan()
        sc.feed(text)
        scans[slug] = sc
        allids[slug] = set(sc.ids)
        if BAD_TAGS.search(text):
            errs.append(f"{slug}.html: contains a script, form, inline style, event handler or embed")
        if "http://" in text:
            errs.append(f"{slug}.html: plain http link or reference")
        if not (sc.lang and sc.meta_csp and sc.main and sc.h1 == 1 and sc.titles == 1):
            errs.append(f"{slug}.html: missing lang, CSP meta, main landmark, single h1 or title")
        if sc.tables != sc.captions or sc.th_scope == 0 and sc.tables:
            errs.append(f"{slug}.html: every table needs a caption and scoped column headers")
        dup = {i for i in sc.ids if sc.ids.count(i) > 1}
        if dup:
            errs.append(f"{slug}.html: duplicate ids {sorted(dup)[:5]}")
    for slug, sc in scans.items():
        for row in sc.rows:
            ext = [h for h, _ in row["links"] if h.startswith("https://")]
            flaglink = any("flagged.html#" in h for h, _ in row["links"])
            on_flag_page = slug == "flagged" and (row["id"] or "").startswith("OL-F")
            if ext:
                bad = [h for h in ext if not host_ok(h)]
                if bad:
                    errs.append(f"{slug}.html row {row['id']}: link host not allowlisted: {bad[0]}")
            elif not (row["blank"] and (flaglink or on_flag_page)):
                errs.append(f"{slug}.html row {row['id']}: no official source link and no blank-plus-flag marker")
        for h in sc.links:
            if h.startswith("https://"):
                if not host_ok(h):
                    errs.append(f"{slug}.html: external link host not allowlisted {h}")
                continue
            if h.startswith(("mailto:", "tel:")):
                errs.append(f"{slug}.html: contact link {h}")
                continue
            path, _, frag = h.partition("#")
            target = (ROOT / slug).with_suffix(".html") if path == "" else (ROOT / path).resolve()
            if not target.exists() and path:
                errs.append(f"{slug}.html: broken internal link {h}")
            elif frag and target.suffix == ".html":
                tslug = target.stem
                ids = allids.get(tslug)
                if target.parent == ROOT and ids is not None and frag not in ids:
                    errs.append(f"{slug}.html: anchor #{frag} not found in {target.name}")
    return errs


# ------------------------------------------------------------------ privacy
def scrub(text):
    text = re.sub(r'(?:href|src)="[^"]*"', " ", text)
    text = re.sub(r'"url"\s*:\s*"[^"]*"', '"url": ""', text)
    return text


def check_privacy(blobs):
    errs = []
    for name, text in blobs.items():
        for n, line in enumerate(scrub(text).splitlines(), 1):
            for rx, label in PRIVACY:
                if name.endswith(".py") and label == "coordinate-like decimal":
                    continue
                if rx.search(line):
                    errs.append(f"privacy: {label} in {name}:{n}: {line.strip()[:90]}")
    return errs


def repo_blobs():
    blobs = {}
    for base in (ROOT, REPO / "private-workflow"):
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.name == "check.py" and f.parent.name == "tools" and base == ROOT:
                continue  # holds the privacy patterns and negative-test fixtures by necessity
            if f.is_file() and f.suffix in {".html", ".json", ".md", ".css", ".py", ".txt", ".csv"} and "__pycache__" not in f.parts:
                blobs[str(f.relative_to(REPO))] = f.read_text(encoding="utf-8", errors="replace")
    return blobs


def check_gitignore():
    gi = (REPO / ".gitignore").read_text(encoding="utf-8") if (REPO / ".gitignore").exists() else ""
    return [] if re.search(r"^/?private/?\s*$", gi, re.M) else ["private/ is not listed in .gitignore"]


# ------------------------------------------------------------------ run
def run():
    d = load_all()
    errs = check_data(d)
    pages = build.build_all()
    errs += check_html(pages)
    for slug, text in pages.items():
        f = ROOT / f"{slug}.html"
        if not f.exists():
            errs.append(f"{slug}.html is missing: run build.py")
        elif f.read_text(encoding="utf-8") != text:
            errs.append(f"{slug}.html is stale: run outlook/tools/build.py")
    errs += check_privacy(repo_blobs())
    errs += check_gitignore()
    rows = sum(len(g) for g in groups(d).values()) + len(d["projections"]["derived"])
    print(f"checked {len(pages)} pages, {rows} data rows, {len(d['sources']['sources'])} sources, {len(d['flags']['flags'])} flags")
    return errs


def selftest():
    d = load_all()
    ok = True

    def expect(label, errs, needle):
        nonlocal ok
        hit = any(needle in e for e in errs)
        print(("PASS " if hit else "FAIL ") + label)
        ok = ok and hit

    base = check_data(d)
    print(("PASS " if not base else "FAIL ") + "clean data has no errors" + ("" if not base else f": {base[:2]}"))
    ok = ok and not base

    m = copy.deepcopy(d); m["projections"]["pop_rows"][0]["src"] = []
    expect("observation without a source is rejected", check_data(m), "without a source")
    m = copy.deepcopy(d); m["projections"]["pop_rows"][0]["locator"] = ""
    expect("observation without quote or locator is rejected", check_data(m), "without a quote or locator")
    m = copy.deepcopy(d); m["projections"]["blank"][0]["flag"] = ""
    expect("blank row without a flag is rejected", check_data(m), "blank row without a flag")
    m = copy.deepcopy(d); m["drivers"]["calendar"][-1]["raw"] = 5
    expect("blank row carrying a value is rejected", check_data(m), "carries a value")
    m = copy.deepcopy(d); m["sources"]["sources"][0]["url"] = "https://example.com/x"
    expect("non-official host is rejected", check_data(m), "allowlist")
    m = copy.deepcopy(d); m["sources"]["sources"][0]["url"] = "http://dof.ca.gov/x"
    expect("plain http source is rejected", check_data(m), "not https")
    m = copy.deepcopy(d); m["projections"]["emp_rows"][0]["pct_pub"] = 9.9
    expect("wrong published percent is detected", check_data(m), "published percent")
    m = copy.deepcopy(d); m["workflow"]["gates"][0]["src"] = []; m["workflow"]["gates"][0].pop("flag", None)
    expect("process row with no reference and no flag is rejected", check_data(m), "no official reference and no flag")
    m = copy.deepcopy(d); m["workflow"]["questions"][0]["flag"] = "OL-F99"
    expect("unknown flag id is rejected", check_data(m), "unknown flag")
    m = copy.deepcopy(d)
    for i in m["peers"]["rows"][0]["src"]:
        pass
    m["sources"]["sources"][11]["method"] = "failed"; m["peers"]["rows"][0]["src"] = ["OL-S12"]
    expect("observation resting only on a failed retrieval is rejected", check_data(m), "never read")

    pages = build.build_all()
    h = dict(pages); h["index"] = h["index"].replace("</main>", "<script>1</script></main>")
    expect("script tag is rejected", check_html(h), "script")
    h = dict(pages); h["peers"] = h["peers"].replace('<td>PR-01</td>', '<td>PR-01</td>', 1).replace('href="https://www.sec.gov/Archives/edgar/data/63908/000006390826000080/exhibit991-9302026.htm"', 'href="https://example.org/x"', 1)
    expect("row link to a non-official host is rejected", check_html(h), "allowlisted")
    h = dict(pages); h["drivers"] = h["drivers"].replace('href="projections.html#D-03"', 'href="nowhere.html"') + ""
    h["index"] = h["index"].replace('href="projections.html#D-03"', 'href="nowhere.html"')
    expect("broken internal link is rejected", check_html(h), "broken internal link")
    h = dict(pages); h["index"] = h["index"].replace('href="projections.html#D-03"', 'href="projections.html#nope"')
    expect("missing anchor is rejected", check_html(h), "anchor #nope")

    for label, text, needle in [
        ("street address is caught", "Property at 1234 Main Street today", "street address"),
        ("APN-style number is caught", "APN 123-456-789", "APN"),
        ("email is caught", "write to a.b@example.com", "email"),
        ("phone is caught", "call 213-555-0100", "phone"),
        ("coordinates are caught", "location 34.05370, -118.24280", "coordinate"),
        ("ZIP 90015 is caught", "ZIP 90015", "ZIP"),
        ("entity plus number is caught", "Acme LLC 4", "entity"),
    ]:
        expect(label, check_privacy({"x.html": text}), needle)
    expect("py files may hold decimals but not addresses", check_privacy({"t.py": "x = 34.05370"}) or ["none"], "none")
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    problems = run()
    if problems:
        print(f"FAIL: {len(problems)} problem(s)")
        for p in problems[:60]:
            print(" -", p)
        sys.exit(1)
    print("PASS: outlook module checks")
