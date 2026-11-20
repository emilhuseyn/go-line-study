"""Row 45, step 4: every number the manuscript uses, into results/numbers.json (and CSV tables).

    py scripts/04_analyse.py

Definitions follow plan/analysis_plan.md (including the logged clarifications).
"""
import csv
import json
import math
import os
import sys
from collections import defaultdict
from datetime import date, datetime

from scipy.stats import fisher_exact

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RES = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
csv.field_size_limit(10 ** 9)
CUT = date(2023, 8, 8)          # Go 1.21.0
START = date(2019, 1, 1)
Z = 1.959963984540054


def d(s):
    return datetime.strptime(s[:10], "%Y-%m-%d").date()


def wilson(k, n):
    if n == 0:
        return {"k": k, "n": n, "p": None, "lo": None, "hi": None}
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return {"k": k, "n": n, "p": p, "lo": max(0.0, c - h), "hi": min(1.0, c + h)}


def newcombe(a, b):
    """Difference a.p - b.p with Newcombe's hybrid score interval, and Fisher's exact test."""
    if not a["n"] or not b["n"]:
        return None
    diff = a["p"] - b["p"]
    lo = diff - math.sqrt((a["p"] - a["lo"]) ** 2 + (b["hi"] - b["p"]) ** 2)
    hi = diff + math.sqrt((a["hi"] - a["p"]) ** 2 + (b["p"] - b["lo"]) ** 2)
    _, pv = fisher_exact([[a["k"], a["n"] - a["k"]], [b["k"], b["n"] - b["k"]]])
    return {"diff": diff, "lo": lo, "hi": hi, "fisher_p": pv}


def module_mean(rows, flag):
    """Each module weighted equally: mean of per-module shares, with a percentile bootstrap interval."""
    per = defaultdict(list)
    for r in rows:
        per[r["module"]].append(1 if flag(r) else 0)
    shares = [sum(v) / len(v) for v in per.values()]
    if not shares:
        return {"modules": 0, "mean": None, "lo": None, "hi": None}
    import random
    rng = random.Random(45)
    boots = sorted(sum(rng.choice(shares) for _ in shares) / len(shares) for _ in range(2000))
    return {"modules": len(shares), "mean": sum(shares) / len(shares), "lo": boots[49], "hi": boots[1949]}


rels = list(csv.DictReader(open(os.path.join(DATA, "releases.csv"), encoding="utf-8")))
pairs = list(csv.DictReader(open(os.path.join(DATA, "pairs.csv"), encoding="utf-8")))
depmax = list(csv.DictReader(open(os.path.join(DATA, "depmax.csv"), encoding="utf-8")))
gor = json.load(open(os.path.join(DATA, "go_releases.json"), encoding="utf-8"))["releases"]
frame = json.load(open(os.path.join(DATA, "frame.json"), encoding="utf-8"))
build = json.load(open(os.path.join(RES, "build_counts.json"), encoding="utf-8"))

minor_date = {}
for k, v in gor.items():
    parts = k.split(".")
    if len(parts) == 2 or (len(parts) == 3 and parts[2] == "0"):
        m = int(parts[1])
        minor_date[m] = min(minor_date.get(m, d(v)), d(v))
MINORS = sorted(minor_date)


def newest_minor(t):
    return max(m for m in MINORS if minor_date[m] <= t)


N = {"snapshot": {"frame_fetched": frame["fetched_at"], "releases_fetched": gor and "go.dev/doc/devel/release"},
     "build": build, "go_minor_dates": {"1.%d" % m: str(minor_date[m]) for m in MINORS if m >= 11}}

# ---------- RQ1 ----------
win = [r for r in rels if START <= d(r["time"])]
for r in win:
    r["_t"] = d(r["time"])
    r["_after"] = r["_t"] >= CUT
    r["_has"] = r["go_minor"] != ""
    if r["_has"]:
        nm = newest_minor(r["_t"])
        r["_age"] = nm - int(r["go_minor"])
        r["_newest"] = nm
        r["_excl"] = int(r["go_minor"]) >= nm   # newer than the oldest supported (N-1)
with_go = [r for r in win if r["_has"]]
N["rq1"] = {"releases_in_window": len(win), "modules_in_window": len({r["module"] for r in win}),
            "no_go_line": wilson(sum(1 for r in win if not r["_has"]), len(win)),
            "with_go_line": len(with_go)}
for per, sel in (("before", lambda r: not r["_after"]), ("after", lambda r: r["_after"])):
    rows = [r for r in with_go if sel(r)]
    ages = sorted(r["_age"] for r in rows)
    N["rq1"][per] = {"releases": len(rows), "modules": len({r["module"] for r in rows}),
                     "excludes_oldest_supported": wilson(sum(r["_excl"] for r in rows), len(rows)),
                     "age_median": ages[len(ages) // 2] if ages else None,
                     "age_le_1": wilson(sum(1 for a in ages if a <= 1), len(ages)),
                     "module_weighted_excl": module_mean(rows, lambda r: r["_excl"])}
N["rq1"]["H1"] = newcombe(N["rq1"]["after"]["excludes_oldest_supported"], N["rq1"]["before"]["excludes_oldest_supported"])
by_year = {}
for r in with_go:
    y = r["_t"].year
    b = by_year.setdefault(y, [0, 0, []])
    b[0] += r["_excl"]
    b[1] += 1
    b[2].append(r["_age"])
N["rq1"]["by_year"] = {y: {"excl": wilson(v[0], v[1]), "age_median": sorted(v[2])[len(v[2]) // 2]} for y, v in sorted(by_year.items())}
lat = {}
for r in rels:
    lat[r["module"]] = r            # releases.csv is in semver order per module
lat_rows = list(lat.values())
lat_go = [r for r in lat_rows if r["go_minor"] != ""]
dist = defaultdict(int)
for r in lat_go:
    dist["1.%s" % r["go_minor"]] += 1
N["rq1"]["latest"] = {"modules": len(lat_rows), "with_go_line": len(lat_go),
                      "no_go_line": len(lat_rows) - len(lat_go),
                      "distribution": dict(sorted(dist.items(), key=lambda kv: int(kv[0].split(".")[1]))),
                      "ge_1_21": wilson(sum(1 for r in lat_go if int(r["go_minor"]) >= 21), len(lat_go)),
                      "published_after_cut": sum(1 for r in lat_rows if d(r["time"]) >= CUT)}

# ---------- RQ2 ----------
pw = [p for p in pairs if START <= d(p["time"]) and p["minor"] != "" and p["minor_prev"] != ""]
for p in pw:
    p["_after"] = d(p["time"]) >= CUT
    p["_delta"] = int(p["minor"]) - int(p["minor_prev"])
N["rq2"] = {"pairs_in_window": len(pw)}
for per, sel in (("before", lambda p: not p["_after"]), ("after", lambda p: p["_after"])):
    rows = [p for p in pw if sel(p)]
    raises = [p for p in rows if p["_delta"] > 0]
    steps = defaultdict(int)
    for p in raises:
        steps[p["step"]] += 1
    nonmajor = sum(v for k, v in steps.items() if k != "major")
    compat = steps["patch"] + steps["minor"]
    deltas = sorted(p["_delta"] for p in raises)
    N["rq2"][per] = {"pairs": len(rows), "raises": wilson(len(raises), len(rows)),
                     "lowered": sum(1 for p in rows if p["_delta"] < 0),
                     "raise_steps": dict(steps),
                     "raises_nonmajor": wilson(nonmajor, len(raises)),
                     "raises_patch_or_v1minor": wilson(compat, len(raises)),
                     "raises_patch": wilson(steps["patch"], len(raises)),
                     "raise_size_median": deltas[len(deltas) // 2] if deltas else None,
                     "raise_size_ge_2": wilson(sum(1 for x in deltas if x >= 2), len(deltas)),
                     "modules_with_raise": len({p["module"] for p in raises}),
                     "module_weighted_raise": module_mean(rows, lambda p: p["_delta"] > 0),
                     "module_weighted_nonmajor": module_mean(raises, lambda p: p["step"] != "major")}
a = N["rq2"]["after"]["raises_nonmajor"]
N["rq2"]["H2"] = {"supported": bool(a["n"] and a["lo"] > 0.5), "after_nonmajor": a}

# ---------- RQ3 ----------
prev_minor = {(p["module"], p["version"]): int(p["minor_prev"]) for p in pairs
              if p["minor"] != "" and p["minor_prev"] != ""}
r3 = []
for r in depmax:
    if "raise" not in r["kind"] or not START <= d(r["time"]):
        continue
    if r["dep_max_minor"] == "":
        cls = "no_dep_line"
    else:
        new, dm, pm = None, int(r["dep_max_minor"]), prev_minor[(r["module"], r["version"])]
        from_go = r["go"].split(".")
        new = int(from_go[1].split("rc")[0].split("beta")[0])
        cls = "inherit" if (new == dm and dm > pm) else ("below" if new < dm else "chosen")
    r3.append({"module": r["module"], "after": d(r["time"]) >= CUT, "cls": cls})
N["rq3"] = {"raising_releases": len(r3)}
for per, flag in (("before", False), ("after", True)):
    rows = [x for x in r3 if x["after"] == flag]
    elig = [x for x in rows if x["cls"] != "no_dep_line"]
    cnt = defaultdict(int)
    for x in rows:
        cnt[x["cls"]] += 1
    N["rq3"][per] = {"raises": len(rows), "classes": dict(cnt),
                     "inherit": wilson(sum(1 for x in elig if x["cls"] == "inherit"), len(elig)),
                     "module_weighted_inherit": module_mean(elig, lambda x: x["cls"] == "inherit")}
N["rq3"]["H3"] = newcombe(N["rq3"]["after"]["inherit"], N["rq3"]["before"]["inherit"])
below = []
for r in depmax:
    if r["dep_max_minor"] == "" or r["go"] == "":
        continue
    gm = int(r["go"].split(".")[1].split("rc")[0].split("beta")[0])
    below.append((r, gm < int(r["dep_max_minor"])))
latest_below = [b for r, b in below if "latest" in r["kind"]]
N["rq3"]["latest_below_dep_max"] = wilson(sum(latest_below), len(latest_below))

# ---------- RQ4 ----------
aft = [r for r in with_go if r["_after"]]
N["rq4"] = {"after_releases": len(aft),
            "patch_gt0": wilson(sum(1 for r in aft if int(r["go_patch"]) > 0), len(aft)),
            "patch_written": wilson(sum(1 for r in aft if int(r["go_patch"]) >= 0), len(aft)),
            "toolchain_line": wilson(sum(1 for r in aft if r["toolchain"]), len(aft)),
            "module_weighted_patch_gt0": module_mean(aft, lambda r: int(r["go_patch"]) > 0)}
lat_after = [r for r in depmax if "latest" in r["kind"] and r["go"] and d(r["time"]) >= CUT]
imposed = []
for r in lat_after:
    gp = r["go"].split(".")
    if len(gp) < 3 or not gp[2].isdigit() or int(gp[2]) == 0:
        continue
    gm, gpa = int(gp[1]), int(gp[2])
    if r["dep_max_minor"] == "":
        imposed.append(False)
        continue
    dm, dpa = int(r["dep_max_minor"]), int(r["dep_max_patch"])
    imposed.append(dm > gm or (dm == gm and dpa >= gpa))
N["rq4"]["latest_after_patch_gt0"] = len(imposed)
N["rq4"]["latest_patch_not_imposed"] = wilson(sum(1 for x in imposed if not x), len(imposed))

# ---------- exploratory (not in the frozen plan; labelled as such in the manuscript) ----------
# Year by year, so that a before/after difference can be read against any trend that was already running.
ex = {"raise_share": {}, "inherit_share": {}}
for y in range(2019, 2027):
    rows = [p for p in pw if d(p["time"]).year == y]
    ex["raise_share"][y] = wilson(sum(1 for p in rows if p["_delta"] > 0), len(rows))
    rr = [x for x, r in zip(r3, [r for r in depmax if "raise" in r["kind"] and START <= d(r["time"])])
          if d(r["time"]).year == y and x["cls"] != "no_dep_line"]
    ex["inherit_share"][y] = wilson(sum(1 for x in rr if x["cls"] == "inherit"), len(rr))
N["exploratory"] = ex

json.dump(N, open(os.path.join(RES, "numbers.json"), "w", encoding="utf-8"), indent=1, default=str)
print(json.dumps({k: N[k] for k in ("rq1", "rq2", "rq3", "rq4")}, indent=1, default=str)[:6000])
