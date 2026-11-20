"""Row 45, step 3: the go lines of the module versions a release requires (for RQ3 and RQ4).

    py scripts/03_deps.py       writes data/depmods.jsonl (cache, resumable) and data/depmax.csv

Releases covered: every release that raised the go line (minor level) over the previous release, and the latest
release of every module. For each, dep_max = the highest go line among all modules its go.mod requires.
"""
import concurrent.futures as cf
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from gomod import parse, gokey, semkey  # noqa: E402

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("c1", os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_collect.py"))
c1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
csv.field_size_limit(10 ** 9)

rels = list(csv.DictReader(open(os.path.join(DATA, "releases.csv"), encoding="utf-8")))
pairs = list(csv.DictReader(open(os.path.join(DATA, "pairs.csv"), encoding="utf-8")))
by_key = {(r["module"], r["version"]): r for r in rels}

targets = {}
for p in pairs:
    if p["minor"] != "" and p["minor_prev"] != "" and int(p["minor"]) > int(p["minor_prev"]):
        targets[(p["module"], p["version"])] = "raise"
latest = {}
for r in rels:
    if r["module"] not in latest or semkey(r["version"]) > semkey(latest[r["module"]]["version"]):
        latest[r["module"]] = r
for m, r in latest.items():
    targets.setdefault((m, r["version"]), "latest")
    if targets[(m, r["version"])] == "raise":
        targets[(m, r["version"])] = "raise+latest"

need = set()
for key in targets:
    for path, ver in json.loads(by_key[key]["requires"]):
        need.add((path, ver))

cache_path = os.path.join(DATA, "depmods.jsonl")
cache = {}
if os.path.exists(cache_path):
    for line in open(cache_path, encoding="utf-8"):
        d = json.loads(line)
        cache[(d["module"], d["version"])] = d
# a network error (-1) or a server error is fetched again; 404/410 are genuine answers and stay
todo = sorted(k for k in need if k not in cache or cache[k]["status"] not in (200, 404, 410))
print("targets:", len(targets), "required module@versions:", len(need), "to fetch:", len(todo), flush=True)


def fetch(mv):
    mod, ver = mv
    st, body = c1.get("https://proxy.golang.org/%s/@v/%s.mod" % (c1.esc(mod), c1.esc(ver)))
    return {"module": mod, "version": ver, "status": st, "go": parse(body)["go"] if st == 200 else None}


with open(cache_path, "a", encoding="utf-8") as out, cf.ThreadPoolExecutor(16) as ex:
    for i, d in enumerate(ex.map(fetch, todo), 1):
        cache[(d["module"], d["version"])] = d
        out.write(json.dumps(d) + "\n")
        if i % 2000 == 0:
            out.flush()
            print("fetched %d/%d" % (i, len(todo)), flush=True)

rows = []
for (mod, ver), kind in sorted(targets.items()):
    r = by_key[(mod, ver)]
    reqs = json.loads(r["requires"])
    keys, failed, no_go = [], 0, 0
    for path, v in reqs:
        d = cache.get((path, v))
        if not d or d["status"] != 200:
            failed += 1
            continue
        k = gokey(d["go"])
        if k is None:
            no_go += 1
            continue
        keys.append((k, d["go"]))
    top = max(keys)[1] if keys else ""
    tk = gokey(top) if top else None
    rows.append({"module": mod, "version": ver, "time": r["time"], "kind": kind, "go": r["go"],
                 "n_requires": len(reqs), "req_fetch_failed": failed, "req_no_go_line": no_go,
                 "dep_max": top, "dep_max_minor": tk[0] if tk else "", "dep_max_patch": tk[1] if tk else ""})
with open(os.path.join(DATA, "depmax.csv"), "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("depmax rows:", len(rows), "with any requirement:", sum(1 for r in rows if r["n_requires"]),
      "requirement fetch failures:", sum(r["req_fetch_failed"] for r in rows))
