"""Shared helpers for the outlook module build and check scripts (standard library only)."""
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]          # .../outlook
DATA = ROOT / "data"
RETRIEVED = "2026-11-26"

# Hosts that may appear as source links. Anything ending in .gov is government.
# The others are named individually and are labelled by tier on the Sources page.
EXTRA_HOSTS = {
    "la28.org": "event-organizer",
    "metro.net": "government (transit agency)",
    "businesswire.com": "issuer-primary",
    "q4cdn.com": "issuer-primary",
    "github.com": "repository",
}


def host_ok(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host.endswith(".gov") or host == "gov":
        return True
    return any(host == h or host.endswith("." + h) for h in EXTRA_HOSTS)


def load(name: str):
    with open(DATA / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


def load_all():
    return {n: load(n) for n in ("sources", "projections", "drivers", "peers", "options", "workflow", "flags")}


# ---------- numbers ----------
def pct_change(a, b):
    return (b - a) / a * 100.0


def diff(a, b):
    return b - a


def compound_pct(xs):
    p = 1.0
    for x in xs:
        p *= 1.0 + x / 100.0
    return (p - 1.0) * 100.0


OPS = {"pct_change": lambda v: pct_change(v[0], v[1]),
       "diff": lambda v: diff(v[0], v[1]),
       "compound_pct": compound_pct}


def raw_index(data):
    """Collect numeric raw values by row id from every observation table."""
    idx = {}
    p = data["projections"]
    for key in ("pop_rows", "k12_rows", "rev_rows"):
        for r in p[key]:
            idx[r["id"]] = r["raw"]
    return idx


def derived_values(data):
    idx = raw_index(data)
    out = {}
    for d in data["projections"]["derived"]:
        vals = [idx[i] for i in d["inputs"]]
        out[d["id"]] = OPS[d["op"]](vals)
        idx[d["id"]] = out[d["id"]]
    return out


def fmt_num(v, unit="", signed=False, decimals=None):
    if v is None:
        return ""
    neg = v < 0
    if unit == "%":
        dec = 2 if decimals is None else decimals
        s = f"{abs(v):,.{dec}f}%"
    else:
        s = f"{abs(round(v)):,.0f}"
    if neg:
        return "\u2212" + s
    return ("+" + s) if signed and v > 0 else s
