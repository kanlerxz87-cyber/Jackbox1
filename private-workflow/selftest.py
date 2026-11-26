#!/usr/bin/env python3
"""Offline self-test for the private workflow. Uses synthetic data in temporary folders only.

  python3 private-workflow/selftest.py
No network access is used. Coordinates are computed in code and never appear in a file in the repository.
"""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pw_common as pw  # noqa: E402
import step1_trade_area_tracts as s1  # noqa: E402
import step2_confirm_tract as s2  # noqa: E402
import step3_acs_tracts as s3  # noqa: E402
import step4_hazard_checklist as s4  # noqa: E402

LAT = 30.0 + 4.25            # synthetic point, computed so no coordinate literal is stored
LON = -(100.0 + 18.5)
MILE_DEG = 1 / 69.093        # degrees of latitude per mile
TMP = []


def make_repo(ignore=True):
    d = Path(tempfile.mkdtemp(prefix="pwtest-"))
    TMP.append(d)
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    if ignore:
        (d / ".gitignore").write_text("private/\n")
    (d / "private").mkdir()
    return pw.Paths(d)


def put_location(paths, lat=LAT, lon=LON):
    (paths.private / "location.json").write_text(json.dumps({"lat": lat, "lon": lon}))


def gazetteer_text(miles_list, county="06037", delim="|", lon_name="INTPTLONG"):
    head = delim.join(["USPS", "GEOID", "ALAND", "AWATER", "ALAND_SQMI", "AWATER_SQMI", "INTPTLAT", lon_name])
    rows = [head]
    for i, m in enumerate(miles_list):
        rows.append(delim.join(["CA", f"{county}{100000 + i:06d}", "1", "0", "1", "0", f"{LAT + m * MILE_DEG:.6f}", f"{LON:.6f}"]))
    return "\n".join(rows) + "\n"


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        res = fn(*a, **k)
    return res, buf.getvalue()


class Guards(unittest.TestCase):
    def test_refuses_when_private_not_ignored(self):
        paths = make_repo(ignore=False)
        with self.assertRaises(SystemExit):
            pw.require_private_ignored(paths)

    def test_accepts_when_ignored(self):
        pw.require_private_ignored(make_repo(ignore=True))

    def test_location_validation(self):
        paths = make_repo()
        with self.assertRaises(SystemExit):
            pw.load_location(paths)                                  # missing file
        for bad in ({"lat": 0, "lon": 0}, {"lat": 10.0, "lon": 10.0}, {"lat": None, "lon": None}, {"lat": "x", "lon": 1}):
            (paths.private / "location.json").write_text(json.dumps(bad))
            with self.assertRaises(SystemExit):
                pw.load_location(paths)
        put_location(paths)
        self.assertEqual(pw.load_location(paths), (LAT, LON))

    def test_cannot_escape_private(self):
        paths = make_repo()
        with self.assertRaises(SystemExit):
            pw.private_path(paths, "..", "outside.txt")
        with self.assertRaises(SystemExit):
            pw.write_private(paths, "../outside.txt", "x")

    def test_write_stays_inside(self):
        paths = make_repo()
        p = pw.write_private(paths, "out/a.txt", "hello")
        self.assertTrue(p.resolve().is_relative_to(paths.private.resolve()))


class Maths(unittest.TestCase):
    def test_haversine(self):
        d = pw.haversine_miles(34.0, -118.0, 34.0, -117.0)
        self.assertAlmostEqual(d, 57.28, delta=0.6)
        self.assertAlmostEqual(pw.haversine_miles(LAT, LON, LAT + 3 * MILE_DEG, LON), 3.0, delta=0.02)

    def test_moe_cv_quantile_sentinels(self):
        self.assertAlmostEqual(pw.sum_moe([3, 4]), 5.0)
        self.assertAlmostEqual(pw.cv(100, 16.45), 0.1)
        self.assertIsNone(pw.cv(0, 5))
        self.assertIsNone(pw.clean_num("-666666666"))
        self.assertIsNone(pw.clean_num("-999999999"))
        self.assertEqual(pw.clean_num("123"), 123.0)
        self.assertIsNone(pw.clean_num("abc"))
        self.assertEqual(pw.quantile([1, 2, 3, 4], 0.5), 2.5)
        self.assertEqual(pw.quantile([7], 0.25), 7)


class Parsing(unittest.TestCase):
    def test_delimiters_and_column_names(self):
        for delim, lon_name in (("|", "INTPTLONG"), ("\t", "INTPTLON"), (",", "INTPTLONG")):
            rows = pw.read_delimited_text(gazetteer_text([1.0, 2.0], delim=delim, lon_name=lon_name))
            self.assertEqual(len(rows), 2)
            self.assertIsNotNone(pw.pick_col(rows[0], "INTPTLONG", "INTPTLON"))

    def test_zip_input(self):
        d = Path(tempfile.mkdtemp(prefix="pwzip-"))
        TMP.append(d)
        z = d / "g.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("2026_Gaz_tracts_national.txt", gazetteer_text([1.0, 2.0, 3.0]))
        self.assertEqual(len(pw.read_gazetteer(z)), 3)


class Step1(unittest.TestCase):
    def setUp(self):
        self.paths = make_repo()
        put_location(self.paths)
        self.gz = self.paths.repo / "gaz.txt"
        self.miles = [0.5, 0.9, 2.0, 2.9, 4.0, 4.9, 8.0] + [3.5] * 6 + [1.5] * 4
        self.gz.write_text(gazetteer_text(self.miles))

    def test_ring_assignment_and_outputs(self):
        (chosen, counts), out = quiet(s1.run, str(self.gz), "06037", [1, 3, 5], self.paths)
        self.assertEqual(counts["1.0"], 2)
        self.assertEqual(counts["3.0"], 2 + 4 + 2)              # 0.5, 0.9, four at 1.5, 2.0, 2.9
        self.assertEqual(counts["5.0"], len(self.miles) - 1)    # all but the 8-mile tract
        self.assertTrue(all(g.startswith("06037") for g, _, _ in chosen))
        f = self.paths.out / "trade_area_tracts.csv"
        self.assertTrue(f.exists())
        meta = json.loads((self.paths.out / "trade_area_meta.json").read_text())
        self.assertIn("approximation", meta["method"])
        self.assertNotIn(str(LAT)[:6], json.dumps(meta))

    def test_county_filter(self):
        self.gz.write_text(gazetteer_text([1.0, 2.0], county="06059"))
        chosen, _ = quiet(s1.run, str(self.gz), "06037", [5], self.paths)[0]
        self.assertEqual(chosen, [])

    def test_no_coordinates_or_ids_printed(self):
        _, out = quiet(s1.run, str(self.gz), "06037", [1, 3, 5], self.paths)
        for needle in (f"{LAT:.3f}", f"{abs(LON):.3f}", "06037100"):
            self.assertNotIn(needle, out)

    def test_refuses_if_not_ignored(self):
        paths = make_repo(ignore=False)
        put_location(paths)
        with self.assertRaises(SystemExit):
            quiet(s1.run, str(self.gz), "06037", [1, 3, 5], paths)


class Step2(unittest.TestCase):
    def setUp(self):
        self.paths = make_repo()
        put_location(self.paths)

    def test_masked_url_hides_coordinates(self):
        u = s2.build_url(LAT, LON, masked=True)
        self.assertIn("REDACTED", u)
        self.assertNotIn(f"{LAT:.2f}", u)
        self.assertTrue(u.startswith("https://geocoding.geo.census.gov/geocoder/geographies/coordinates?"))

    def test_parse_shape(self):
        obj = {"result": {"geographies": {"Census Tracts": [{"GEOID": "06037999900"}]}}}
        self.assertEqual(s2.parse_tract(obj), "06037999900")
        for bad in ({}, {"result": {"geographies": {}}}, {"result": {"geographies": {"Census Tracts": []}}}):
            with self.assertRaises(ValueError):
                s2.parse_tract(bad)

    def test_dry_run_sends_nothing(self):
        def boom(url):
            raise AssertionError("network used in dry run")
        _, out = quiet(s2.run, False, self.paths, boom)
        self.assertIn("nothing sent", out)
        self.assertNotIn(f"{LAT:.2f}", out)

    def test_online_with_fake_fetch_stores_privately(self):
        seen = []

        def fake(url):
            seen.append(url)
            return {"result": {"geographies": {"Census Tracts": [{"GEOID": "06037999900"}]}}}
        geoid, out = quiet(s2.run, True, self.paths, fake)
        self.assertEqual(geoid, "06037999900")
        self.assertEqual(len(seen), 1)
        self.assertNotIn("06037999900", out)
        self.assertTrue((self.paths.out / "parcel_tract.json").exists())


def synthetic_acs_csv(path, geoids, drop=()):
    cols = ["GEOID"] + [f"{s}{k}" for s, *_ in s3.VARS for k in ("E", "M")]
    lines = [",".join(cols)]
    for i, g in enumerate(geoids):
        if g in drop:
            continue
        vals = {"B01003_001": 4000 + i * 10, "B19013_001": 50000 + i * 1000, "B25003_001": 1500 + i, "B25003_003": 900 + i,
                "B25064_001": 1500 + i * 5, "B25077_001": 600000 + i * 1000}
        row = [g]
        for s, *_ in s3.VARS:
            row += [str(vals[s]), "-666666666" if (s == "B25077_001" and i == 0) else str(10 + i)]
        lines.append(",".join(row))
    Path(path).write_text("\n".join(lines) + "\n")


class Step3(unittest.TestCase):
    def setUp(self):
        self.paths = make_repo()
        put_location(self.paths)
        self.gz = self.paths.repo / "gaz.txt"
        self.gz.write_text(gazetteer_text([0.5 + 0.1 * i for i in range(14)]))
        quiet(s1.run, str(self.gz), "06037", [1, 3], self.paths)
        self.geoids = [f"06037{100000 + i:06d}" for i in range(14)]

    def test_verify_variables(self):
        good = {c: {"concept": con, "label": (lab or "Estimate!!Total")} for c, _, con, lab in s3.VARS}

        def fetch(url):
            stem = url.rsplit("/", 1)[1].split("E.json")[0]
            return good[stem]
        s3.verify_variables("2024", fetch)
        bad = dict(good)
        bad["B19013_001"] = {"concept": "Something Else", "label": "x"}
        with self.assertRaises(SystemExit):
            s3.verify_variables("2024", lambda url: bad[url.rsplit("/", 1)[1].split("E.json")[0]])

    def test_api_rows_and_sentinels(self):
        head = ["NAME"] + [f"{s}{k}" for s, *_ in s3.VARS for k in ("E", "M")] + ["state", "county", "tract"]
        row = ["x"] + ["10", "2"] * 4 + ["-666666666", "-222222222", "5", "1"] + ["06", "037", "100000"]
        rec = s3.records_from_api_rows([head, row])
        self.assertIn("06037100000", rec)
        self.assertIsNone(rec["06037100000"]["median_gross_rent"][0])
        self.assertEqual(rec["06037100000"]["population"], (10.0, 2.0))

    def test_aggregate_maths(self):
        recs = {g: {"population": (100.0, 3.0), "occupied_units": (40.0, 4.0), "renter_occupied": (10.0, 2.0),
                    "median_hh_income": (50000.0 + i * 1000, 5000.0), "median_gross_rent": (1500.0, None), "median_home_value": (None, None)}
                for i, g in enumerate(self.geoids[:12])}
        agg = s3.aggregate(recs, self.geoids[:12])
        self.assertEqual(agg["additive_counts"]["population"]["sum"], 1200.0)
        self.assertAlmostEqual(agg["additive_counts"]["population"]["moe_rss"], round(pw.sum_moe([3.0] * 12), 1))
        self.assertAlmostEqual(agg["renter_share"], 0.25)
        self.assertEqual(agg["tract_median_spread"]["median_hh_income"]["min"], 50000.0)
        self.assertEqual(agg["tract_median_spread"]["median_home_value"]["tracts_with_value"], 0)
        self.assertEqual(agg["tracts_missing_in_vintage"], 0)

    def test_public_guard_blocks_small_sets(self):
        with self.assertRaises(SystemExit):
            pw.public_guard(pw.MIN_TRACTS_PUBLIC - 1)
        pw.public_guard(pw.MIN_TRACTS_PUBLIC)

    def test_offline_run_writes_aggregate_without_ids(self):
        f = self.paths.repo / "acs.csv"
        synthetic_acs_csv(f, self.geoids)
        res, out = quiet(s3.run, "2024", 3.0, None, str(f), None, "06037", self.paths, None, False, {})
        self.assertEqual(res["aggregate"]["tracts_found"], 14)
        pub = next(self.paths.out.glob("public_aggregate_2024_ring3.json")).read_text()
        for g in self.geoids:
            self.assertNotIn(g, pub)
        for bad_key in ('"lat"', '"lon"', "GEOID"):
            self.assertNotIn(bad_key, pub)
        self.assertNotIn("06037100", out)

    def test_ring_too_small_for_public(self):
        with self.assertRaises(SystemExit):
            quiet(s3.run, "2024", 1.0, None, str(self.paths.repo / "none.csv"), None, "06037", self.paths, None, False, {})

    def test_missing_key_is_refused_and_key_never_leaks(self):
        with self.assertRaises(SystemExit):
            quiet(s3.run, "2024", 3.0, None, None, None, "06037", self.paths, lambda u: {}, False, {})
        sentinel = "KEY-SENTINEL-0001"
        urls = []
        head = ["NAME"] + [f"{s}{k}" for s, *_ in s3.VARS for k in ("E", "M")] + ["state", "county", "tract"]
        rows = [head] + [["x"] + ["10", "2"] * 6 + ["06", "037", g[5:]] for g in self.geoids]

        def fetch(url):
            urls.append(url)
            return rows
        res, out = quiet(s3.run, "2024", 3.0, None, None, None, "06037", self.paths, fetch, False, {"CENSUS_API_KEY": sentinel})
        self.assertEqual(len(urls), 1)
        self.assertIn("for=tract:*", urls[0])
        self.assertIn("in=county:037", urls[0])
        self.assertNotIn(f"{LAT:.2f}", urls[0])
        self.assertNotIn(sentinel, out)
        for f in self.paths.out.iterdir():
            self.assertNotIn(sentinel, f.read_text())

    def test_consistency_message(self):
        a = {g: {} for g in self.geoids}
        b = {g: {} for g in self.geoids[:-2]}
        c = s3.consistency(self.geoids, a, b)
        self.assertEqual(c["only_in_first"], 2)
        self.assertIn("differs", c["message"])
        self.assertIn("matches", s3.consistency(self.geoids, a, a)["message"])


class Step4(unittest.TestCase):
    def test_blank_checklist(self):
        paths = make_repo()
        put_location(paths)
        quiet(s4.run, paths)
        text = (paths.out / "hazard_checklist.md").read_text()
        self.assertIn("Result", text)
        self.assertIn("msc.fema.gov", text)
        self.assertNotIn(f"{LAT:.2f}", text)
        rows = [ln for ln in text.splitlines() if ln.startswith("| ") and "---" not in ln][1:]
        for ln in rows:
            self.assertTrue(ln.rstrip().endswith("|  |  |  |"), "result cells must start blank")


class Hygiene(unittest.TestCase):
    def test_repo_gitignore_lists_private(self):
        gi = (pw.REPO_ROOT / ".gitignore").read_text()
        self.assertRegex(gi, r"(?m)^/?private/?\s*$")

    def test_no_unexpected_network_calls_in_steps_1_and_4(self):
        for name in ("step1_trade_area_tracts.py", "step4_hazard_checklist.py", "pw_common.py"):
            src = (HERE / name).read_text()
            for bad in ("urllib", "requests", "socket", "http.client"):
                self.assertNotIn(bad, src, f"{name} must not use the network ({bad})")


def main():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    for d in TMP:
        shutil.rmtree(d, ignore_errors=True)
    print("SELFTEST " + ("PASSED" if res.wasSuccessful() else "FAILED") + f" ({res.testsRun} tests)")
    return 0 if res.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
