"""Row 45, step 4c (EXPLORATORY, added after the main results; labelled as such in the paper).

Who sets the inherited line? For every raise after Go 1.21 that is consistent with inheritance (new line n equals
the highest requirement line d), the *setters* are the required module versions whose go line equals d. We count
how often each module appears as a setter, and how long after the setter version was published the raising release
followed (only where the setter version is itself a release in our data, so its publication time is known).

    py scripts/04c_explore.py      adds "explore" to results/numbers.json and writes build/tables/setters.tex
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from gomod import gokey  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RES = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
csv.field_size_limit(10 ** 9)
CUT = "2023-08-08"

rels = list(csv.DictReader(open(os.path.join(DATA, "releases.csv"), encoding="utf-8")))
pairs = list(csv.DictReader(open(os.path.join(DATA, "pairs.csv"), encoding="utf-8")))
depmax = list(csv.DictReader(open(os.path.join(DATA, "depmax.csv"), encoding="utf-8")))
by_key = {(r["module"], r["version"]): r for r in rels}
cache = {}
for line in open(os.path.join(DATA, "depmods.jsonl"), encoding="utf-8"):
    d = json.loads(line)
    cache[(d["module"], d["version"])] = d
prev_minor = {(p["module"], p["version"]): int(p["minor_prev"]) for p in pairs
              if p["minor"] != "" and p["minor_prev"] != ""}


def t(s):
    return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")


setter_count, setter_family = Counter(), Counter()
n_inherit, with_x, lags, lag_known = 0, 0, [], 0
inheriting = []  # (module, time, new line, setter paths) for every inheriting raise after the cut
for r in depmax:
    if "raise" not in r["kind"] or r["time"] < CUT or r["dep_max_minor"] == "":
        continue
    n = int(r["go"].split(".")[1].split("rc")[0])
    dm = int(r["dep_max_minor"])
    if not (n == dm and dm > prev_minor[(r["module"], r["version"])]):
        continue
    n_inherit += 1
    top = gokey(r["dep_max"])
    setters = []
    for path, v in json.loads(by_key[(r["module"], r["version"])]["requires"]):
        d = cache.get((path, v))
        if d and d["status"] == 200 and d["go"] and gokey(d["go"]) == top:
            setters.append((path, v))
    for path in {p for p, _ in setters}:
        setter_count[path] += 1
    fam = set()
    for path, _ in setters:
        fam.add("golang.org/x" if path.startswith("golang.org/x/") else
                "google.golang.org" if path.startswith("google.golang.org/") else
                "k8s.io" if path.startswith("k8s.io/") else "other")
    for f in fam:
        setter_family[f] += 1
    if any(p.startswith("golang.org/x/") for p, _ in setters):
        with_x += 1
    inheriting.append((r["module"], t(r["time"]), r["go"], {p for p, _ in setters}))
    known = [t(by_key[s]["time"]) for s in setters if s in by_key]
    if known:
        lag_known += 1
        lags.append((t(r["time"]) - max(known)).days)

lags.sort()


def q(p):
    return lags[int(p * (len(lags) - 1))] if lags else None


ex = {"inherit_raises_after": n_inherit,
      "with_golang_x_setter": with_x,
      "setter_families": dict(setter_family),
      "top_setters": setter_count.most_common(12),
      "lag_days": {"known": lag_known, "median": q(0.5), "q1": q(0.25), "q3": q(0.75),
                   "within_30": sum(1 for x in lags if x <= 30), "within_90": sum(1 for x in lags if x <= 90)}}
N = json.load(open(os.path.join(RES, "numbers.json"), encoding="utf-8"))
N["explore"] = ex
json.dump(N, open(os.path.join(RES, "numbers.json"), "w", encoding="utf-8"), indent=1, default=str)
os.makedirs(os.path.join(ROOT, "build", "tables"), exist_ok=True)
rows = ["\\code{%s} & %s & %.1f \\\\" % (p.replace("_", "\\_"), "{:,}".format(c), 100 * c / n_inherit)
        for p, c in setter_count.most_common(10)]
open(os.path.join(ROOT, "build", "tables", "setters.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
# Year by year, all raising releases in the window (before and after the cut): share consistent with inheritance,
# split by whether a golang.org/x module is among the setters. Shows whether the after-1.21 rise is only the x policy.
by_year = defaultdict(lambda: {"eligible": 0, "inherit": 0, "inherit_x": 0, "inherit_nox": 0})
for r in depmax:
    if "raise" not in r["kind"] or r["time"] < "2019-01-01" or r["dep_max_minor"] == "":
        continue
    y = r["time"][:4]
    by_year[y]["eligible"] += 1
    n = int(r["go"].split(".")[1].split("rc")[0])
    dm = int(r["dep_max_minor"])
    if not (n == dm and dm > prev_minor[(r["module"], r["version"])]):
        continue
    by_year[y]["inherit"] += 1
    top = gokey(r["dep_max"])
    xs = False
    for path, v in json.loads(by_key[(r["module"], r["version"])]["requires"]):
        d = cache.get((path, v))
        if path.startswith("golang.org/x/") and d and d["status"] == 200 and d["go"] and gokey(d["go"]) == top:
            xs = True
    by_year[y]["inherit_x" if xs else "inherit_nox"] += 1
ex["inherit_by_year_x"] = dict(sorted(by_year.items()))

# go-line history of the two most frequent setters, against the Go release dates
gor = json.load(open(os.path.join(DATA, "go_releases.json"), encoding="utf-8"))["releases"]
hist = []
for m in ("golang.org/x/sys", "golang.org/x/net"):
    prev = None
    for r in rels:
        if r["module"] == m and r["go"] != prev:
            if prev is not None and r["time"] >= "2023-01-01":
                hist.append((m, r["version"], r["time"][:10], prev, r["go"]))
            prev = r["go"]
ex["x_history"] = hist
rows, followers = [], []
for m, v, day, a, b in hist:
    minor = b.split(".")[1]
    nxt = gor.get("1.%d.0" % (int(minor) + 1)) or gor.get("1.%d" % (int(minor) + 1)) or ""
    # distinct frame modules whose inheriting raise within 60 days copied exactly this line from this module
    t0 = t(day + "T00:00:00")
    mods = {mod for mod, when, line, setters in inheriting
            if m in setters and line == b and 0 <= (when - t0).days <= 60}
    followers.append(len(mods))
    rows.append("\\code{%s} & %s & %s & %s to %s & %s & %s \\\\" % (m, v, day, a, b, nxt,
                                                                  len(mods) if day >= CUT else "-"))
ex["x_history_followers_60d"] = followers
open(os.path.join(ROOT, "build", "tables", "xhistory.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
N["explore"] = ex
json.dump(N, open(os.path.join(RES, "numbers.json"), "w", encoding="utf-8"), indent=1, default=str)
print(json.dumps(ex, indent=1)[:1500])
