"""Shared guards for the private workflow (standard library only).

Design rule: the parcel location and every per-tract result live ONLY under the git-ignored
private/ folder. Nothing here prints a coordinate, a street address or a tract id.
"""
import csv
import io
import json
import math
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MIN_TRACTS_PUBLIC = 10          # a public aggregate must cover at least this many tracts
CA_BOUNDS = (32.0, 42.1, -124.6, -114.0)   # lat_min, lat_max, lon_min, lon_max (coarse California box)
MISSING_BELOW = -100_000_000    # Census annotation sentinels are large negatives; treated as missing, never interpreted


def die(msg):
    raise SystemExit("REFUSED: " + msg)


@dataclass(frozen=True)
class Paths:
    repo: Path = REPO_ROOT

    @property
    def private(self):
        return self.repo / "private"

    @property
    def out(self):
        return self.private / "out"

    @property
    def location(self):
        return self.private / "location.json"


def require_private_ignored(paths=None):
    """Refuse to run unless private/ is ignored by git in this repository."""
    paths = paths or Paths()
    try:
        r = subprocess.run(["git", "-C", str(paths.repo), "check-ignore", "-q", "private/"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        die("could not run git to confirm that private/ is ignored")
    if r.returncode != 0:
        die("private/ is not ignored by git here. Add 'private/' to .gitignore first")


def private_path(paths, *parts):
    """Resolve a path and refuse anything that would land outside private/."""
    p = paths.private.joinpath(*parts).resolve()
    if not p.is_relative_to(paths.private.resolve()):
        die("path escapes the private folder")
    return p


def write_private(paths, rel, text):
    p = private_path(paths, *Path(rel).parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    try:
        p.chmod(0o600)
    except OSError:
        pass
    return p


def load_location(paths=None):
    """Return (lat, lon) from private/location.json; never echo the values."""
    paths = paths or Paths()
    f = private_path(paths, "location.json")
    if not f.exists():
        die("private/location.json not found. Create it with numeric 'lat' and 'lon' (see README)")
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        lat, lon = float(d["lat"]), float(d["lon"])
    except (ValueError, KeyError, TypeError):
        die("private/location.json must contain numeric 'lat' and 'lon'")
    la0, la1, lo0, lo1 = CA_BOUNDS
    if not (la0 <= lat <= la1 and lo0 <= lon <= lo1) or (lat == 0 and lon == 0):
        die("location is a placeholder or outside California")
    return lat, lon


def haversine_miles(lat1, lon1, lat2, lon2):
    r = 3958.7613
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def detect_delimiter(header):
    return max(["|", "\t", ","], key=header.count)


def read_delimited_text(text):
    """Parse a delimited text table (Gazetteer files are pipe-delimited; older ones were tab-delimited)."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines:
        return []
    delim = detect_delimiter(lines[0])
    rdr = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delim)
    rows = []
    for r in rdr:
        rows.append({(k or "").strip(): (v or "").strip() for k, v in r.items()})
    return rows


def read_gazetteer(path):
    """Read a Gazetteer tracts file given as .txt or .zip (first .txt member)."""
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".txt")]
            if not names:
                die("no .txt member in the zip")
            return read_delimited_text(z.read(names[0]).decode("utf-8", errors="replace"))
    return read_delimited_text(p.read_text(encoding="utf-8", errors="replace"))


def pick_col(row, *candidates):
    low = {k.lower(): k for k in row}
    for c in candidates:
        if c.lower() in low:
            return low[c.lower()]
    return None


def sum_moe(moes):
    """Margin of error of a sum of independent estimates (root of sum of squares)."""
    return math.sqrt(sum(m * m for m in moes))


def cv(estimate, moe):
    """Coefficient of variation from an ACS 90% margin of error."""
    if estimate in (None, 0) or moe is None:
        return None
    return (moe / 1.645) / abs(estimate)


def clean_num(v):
    """Parse an API/CSV value; None for blanks, non-numbers and Census annotation sentinels."""
    if v in (None, "", "null"):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x <= MISSING_BELOW else x


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * q
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def public_guard(n_tracts):
    if n_tracts < MIN_TRACTS_PUBLIC:
        die(f"only {n_tracts} tracts; a public aggregate needs at least {MIN_TRACTS_PUBLIC} so no small area is exposed")
