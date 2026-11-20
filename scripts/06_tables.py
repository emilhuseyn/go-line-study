"""Row 45, step 6: numbers.json -> build/numbers.tex (macros) and build/tables/*.tex. No number is typed by hand.

    py scripts/06_tables.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = json.load(open(os.path.join(ROOT, "results", "numbers.json"), encoding="utf-8"))
V = json.load(open(os.path.join(ROOT, "results", "validation.json"), encoding="utf-8"))
B = N["build"]
os.makedirs(os.path.join(ROOT, "build", "tables"), exist_ok=True)


def pc(x, nd=1):
    return ("%." + str(nd) + "f") % (100 * x)


def num(n):
    return "{:,}".format(n)


def ci(w):
    return "%s\\%% (95\\%% CI %s-%s)" % (pc(w["p"]), pc(w["lo"]), pc(w["hi"]))


def pp(x):
    return "%.1f" % (100 * x)


M = {}


def m(name, val):
    assert name.isalpha(), name
    M[name] = val


r1, r2, r3, r4 = N["rq1"], N["rq2"], N["rq3"], N["rq4"]
m("NFrame", num(B["modules_in_frame"]))
m("NVersionsListed", num(B["versions_listed"]))
m("NReleases", num(B["releases"]))
m("NModulesWithReleases", num(B["modules_with_releases"]))
m("NPairs", num(B["pairs"]))
m("NNoVersions", num(B["modules_without_versions"]))
m("NListFailed", num(B["list_failed"]))
m("NIncompatible", num(B["incompatible"]))
m("NPrerelease", num(B["prerelease"]))
m("NInfoFailed", num(B["info_failed"]))
m("NModFailed", num(B["mod_failed"]))
m("NMismatch", num(B["module_line_mismatch"]))
m("NGoAbsent", num(B["go_line_absent"]))
m("NGoUnparseable", num(B["go_line_unparseable"]))
m("FrameDate", N["snapshot"]["frame_fetched"][:10])

m("NWindowReleases", num(r1["releases_in_window"]))
m("NWindowModules", num(r1["modules_in_window"]))
m("NoGoLineShare", ci(r1["no_go_line"]))
for per, P in (("before", "Before"), ("after", "After")):
    q = r1[per]
    m("NRel" + P, num(q["releases"]))
    m("NMod" + P, num(q["modules"]))
    m("Excl" + P, ci(q["excludes_oldest_supported"]))
    m("ExclPct" + P, pc(q["excludes_oldest_supported"]["p"]))
    m("ExclModW" + P, pc(q["module_weighted_excl"]["mean"]))
    m("ExclModWCI" + P, "%s-%s" % (pc(q["module_weighted_excl"]["lo"]), pc(q["module_weighted_excl"]["hi"])))
    m("AgeMedian" + P, str(q["age_median"]))
    m("AgeLeOne" + P, ci(q["age_le_1"]))
h1 = r1["H1"]
m("HOneDiff", pp(h1["diff"]))
m("HOneCI", "%s to %s" % (pp(h1["lo"]), pp(h1["hi"])))
lat = r1["latest"]
m("NLatest", num(lat["modules"]))
m("NLatestGo", num(lat["with_go_line"]))
m("NLatestNoGo", num(lat["no_go_line"]))
m("LatestGeTwentyOne", ci(lat["ge_1_21"]))
m("NLatestAfterCut", num(lat["published_after_cut"]))
top = max(lat["distribution"].items(), key=lambda kv: kv[1])
m("LatestModeVersion", top[0])
m("LatestModeCount", num(top[1]))

m("NPairsWindow", num(r2["pairs_in_window"]))
for per, P in (("before", "Before"), ("after", "After")):
    q = r2[per]
    m("NPairs" + P, num(q["pairs"]))
    m("Raise" + P, ci(q["raises"]))
    m("RaisePct" + P, pc(q["raises"]["p"]))
    m("NRaises" + P, num(q["raises"]["k"]))
    m("Lowered" + P, num(q["lowered"]))
    m("NonMajor" + P, ci(q["raises_nonmajor"]))
    m("NonMajorPct" + P, pc(q["raises_nonmajor"]["p"]))
    m("Compat" + P, ci(q["raises_patch_or_v1minor"]))
    m("PatchShare" + P, ci(q["raises_patch"]))
    m("RaiseGeTwo" + P, ci(q["raise_size_ge_2"]))
    m("ModsWithRaise" + P, num(q["modules_with_raise"]))
    m("RaiseModW" + P, pc(q["module_weighted_raise"]["mean"]))
    m("RaiseModWCI" + P, "%s-%s" % (pc(q["module_weighted_raise"]["lo"]), pc(q["module_weighted_raise"]["hi"])))
    for s in ("patch", "minor", "v0-minor", "major"):
        m("Step" + s.replace("v0-", "vzero").replace("-", "").capitalize().replace("Vzerominor", "VzeroMinor") + P,
          num(q["raise_steps"].get(s, 0)))

for per, P in (("before", "Before"), ("after", "After")):
    q = r3[per]
    m("NRaiseDep" + P, num(q["raises"]))
    m("Inherit" + P, ci(q["inherit"]))
    m("InheritPct" + P, pc(q["inherit"]["p"]))
    m("InheritModW" + P, pc(q["module_weighted_inherit"]["mean"]))
    m("InheritModWCI" + P, "%s-%s" % (pc(q["module_weighted_inherit"]["lo"]), pc(q["module_weighted_inherit"]["hi"])))
    for c in ("inherit", "chosen", "below", "no_dep_line"):
        m("Cls" + c.replace("_", "").capitalize() + P, num(q["classes"].get(c, 0)))
h3 = r3["H3"]
m("HThreeDiff", pp(h3["diff"]))
m("HThreeCI", "%s to %s" % (pp(h3["lo"]), pp(h3["hi"])))
m("HThreeP", "$p < 0.001$" if h3["fisher_p"] < 0.001 else "$p = %.3f$" % h3["fisher_p"])
m("LatestBelow", ci(r3["latest_below_dep_max"]))
m("NLatestBelow", num(r3["latest_below_dep_max"]["k"]))
m("NLatestDep", num(r3["latest_below_dep_max"]["n"]))

m("NAfterRel", num(r4["after_releases"]))
m("PatchGtZero", ci(r4["patch_gt0"]))
m("PatchWritten", ci(r4["patch_written"]))
m("ToolchainLine", ci(r4["toolchain_line"]))
m("NLatestPatch", num(r4["latest_after_patch_gt0"]))
m("NotImposed", ci(r4["latest_patch_not_imposed"]))
m("NNotImposed", num(r4["latest_patch_not_imposed"]["k"]))

m("ValSample", num(V["sample"]))
m("ValAgree", num(V["agree"]))
m("ValOfficialError", num(V["official_error"]))
m("ValValues", num(V["ordering"]["values"]))
m("ValCorrupt", num(V["corruption_detected"]))

ih = N["exploratory"]["inherit_share"]
early = [ih[str(y)]["p"] for y in range(2019, 2024)]
m("InheritEarlyMin", "%.0f" % (100 * min(early)))
m("InheritEarlyMax", "%.0f" % (100 * max(early)))
m("InheritTwentyFour", "%.0f" % (100 * ih["2024"]["p"]))
m("InheritTwentyFive", "%.0f" % (100 * ih["2025"]["p"]))
m("InheritTwentySix", "%.0f" % (100 * ih["2026"]["p"]))
a25, a26 = "%.0f" % (100 * ih["2025"]["p"]), "%.0f" % (100 * ih["2026"]["p"])
m("InheritLate", ("%s\\%% in both 2025 and 2026" % a25) if a25 == a26 else ("%s\\%% in 2025 and %s\\%% in 2026" % (a25, a26)))
rs = N["exploratory"]["raise_share"]
m("RaiseYearFirst", pc(rs["2019"]["p"]))
m("RaiseYearMax", pc(max(v["p"] for v in rs.values())))

with open(os.path.join(ROOT, "build", "numbers.tex"), "w", encoding="utf-8") as f:
    f.write("% generated by scripts/06_tables.py from results/numbers.json; do not edit\n")
    for k, v in M.items():
        f.write("\\newcommand{\\%s}{%s}\n" % (k, v))

# Table: RQ1 by year
rows = []
ex = N["exploratory"]
for y, v in r1["by_year"].items():
    rs, ih = ex["raise_share"][y], ex["inherit_share"][y]
    rows.append("%s & %s & %s & %s & %s & %s & %s (%s) \\\\" % (
        y, num(v["excl"]["n"]), pc(v["excl"]["p"]), v["age_median"], num(rs["n"]), pc(rs["p"]),
        pc(ih["p"]) if ih["n"] else "-", num(ih["n"])))
open(os.path.join(ROOT, "build", "tables", "rq1_by_year.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")

# Table: latest go line distribution (grouped)
dist = lat["distribution"]
groups = [("1.2 to 1.10", range(2, 11)), ("1.11 to 1.15", range(11, 16)), ("1.16 to 1.20", range(16, 21))]
rows = []
for name, rg in groups:
    k = sum(dist.get("1.%d" % i, 0) for i in rg)
    rows.append("%s & %s & %s \\\\" % (name, num(k), pc(k / lat["with_go_line"])))
for i in range(21, 40):
    k = dist.get("1.%d" % i)
    if k:
        rows.append("1.%d & %s & %s \\\\" % (i, num(k), pc(k / lat["with_go_line"])))
open(os.path.join(ROOT, "build", "tables", "latest_dist.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
print("macros:", len(M))
