"""Row 45, step 2: one row per tagged version and one row per pair of consecutive releases.

    py scripts/02_build.py      reads data/modules/*.json, writes data/releases.csv, data/pairs.csv, results/build_counts.json

A release is a tagged, non-prerelease, non-+incompatible version whose .info and .mod were fetched. Every exclusion
is counted.
"""
import csv
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from gomod import parse, gokey, semkey, is_prerelease, step  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RES = os.path.join(ROOT, "data"), os.path.join(ROOT, "results")
os.makedirs(RES, exist_ok=True)

counts = {"modules_in_frame": 0, "module_files": 0, "list_failed": 0, "modules_without_versions": 0,
          "versions_listed": 0, "not_semver": 0, "incompatible": 0, "prerelease": 0, "info_failed": 0,
          "mod_failed": 0, "module_line_mismatch": 0, "go_line_absent": 0, "go_line_unparseable": 0,
          "go_line_multiple": 0, "releases": 0, "modules_with_releases": 0, "pairs": 0}
counts["modules_in_frame"] = len(json.load(open(os.path.join(DATA, "frame.json"), encoding="utf-8"))["modules"])

rel_rows, pair_rows = [], []
for path in sorted(glob.glob(os.path.join(DATA, "modules", "*.json"))):
    rec = json.load(open(path, encoding="utf-8"))
    counts["module_files"] += 1
    if rec["list_status"] != 200:
        counts["list_failed"] += 1
        continue
    if not rec["versions"]:
        counts["modules_without_versions"] += 1
        continue
    mod_rels = []
    for v in rec["versions"]:
        counts["versions_listed"] += 1
        ver = v["version"]
        if semkey(ver) is None:
            counts["not_semver"] += 1
            continue
        if "+incompatible" in ver:
            counts["incompatible"] += 1
            continue
        if is_prerelease(ver):
            counts["prerelease"] += 1
            continue
        if v["info_status"] != 200 or not v["time"]:
            counts["info_failed"] += 1
            continue
        if v["mod_status"] != 200:
            counts["mod_failed"] += 1
            continue
        p = parse(v["mod"])
        if p["module"] and p["module"] != rec["module"]:
            # the tag carries another module's go.mod; the go command refuses such a version
            counts["module_line_mismatch"] += 1
            continue
        if p["go_lines"] > 1:
            counts["go_line_multiple"] += 1
        if p["go"] is None:
            counts["go_line_absent"] += 1
        elif gokey(p["go"]) is None:
            counts["go_line_unparseable"] += 1
        k = gokey(p["go"])
        mod_rels.append({"rank": rec["rank"], "module": rec["module"], "version": ver, "time": v["time"],
                         "go": p["go"] or "", "go_minor": k[0] if k else "", "go_patch": k[1] if k else "",
                         "go_rc": k[2] if k else "", "toolchain": p["toolchain"] or "",
                         "n_requires": len(p["requires"]),
                         "requires": json.dumps([[a, b] for a, b, _ in p["requires"]])})
    mod_rels.sort(key=lambda r: semkey(r["version"]))
    if mod_rels:
        counts["modules_with_releases"] += 1
    rel_rows += mod_rels
    for a, b in zip(mod_rels, mod_rels[1:]):
        pair_rows.append({"rank": b["rank"], "module": b["module"], "prev": a["version"], "version": b["version"],
                          "time": b["time"], "step": step(a["version"], b["version"]),
                          "go_prev": a["go"], "go": b["go"],
                          "minor_prev": a["go_minor"], "minor": b["go_minor"],
                          "patch_prev": a["go_patch"], "patch": b["go_patch"]})

counts["releases"], counts["pairs"] = len(rel_rows), len(pair_rows)
for name, rows in (("releases.csv", rel_rows), ("pairs.csv", pair_rows)):
    with open(os.path.join(DATA, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
json.dump(counts, open(os.path.join(RES, "build_counts.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(counts, indent=1))
