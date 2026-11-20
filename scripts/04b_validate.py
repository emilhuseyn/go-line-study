"""Row 45, step 4b: the instrument against the Go toolchain itself.

1. parse() against `go mod edit -json` on a random sample of 1,000 go.mod files (seed 45) plus every file with a
   toolchain line or a patch-level go line in the sample frame, up to 300 more.
2. gokey() ordering against go/version.Compare on every distinct go-line value in the data.
3. A corrupted-copy check: the comparison must fail when the parser is given altered text.

    py scripts/04b_validate.py      writes results/validation.json; exits 1 on any disagreement
"""
import glob
import json
import os
import random
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from gomod import parse, gokey  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GO = "go"

mods = []
for path in sorted(glob.glob(os.path.join(ROOT, "data", "modules", "*.json"))):
    rec = json.load(open(path, encoding="utf-8"))
    for v in rec["versions"]:
        if v["mod_status"] == 200 and v["mod"]:
            mods.append((rec["module"], v["version"], v["mod"]))
rng = random.Random(45)
sample = rng.sample(mods, 1000)
extra = [m for m in mods if ("toolchain" in m[2] or any(l.strip().startswith("go 1.") and l.strip().count(".") == 2
                                                         for l in m[2].splitlines()))]
sample += rng.sample(extra, min(300, len(extra)))


def official(text):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "go.mod")
        open(p, "w", encoding="utf-8").write(text)
        r = subprocess.run([GO, "mod", "edit", "-json", p], capture_output=True, text=True, cwd=td,
                           env={**os.environ, "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod"})
        if r.returncode != 0:
            return None, r.stderr.replace(p, "go.mod").strip()[:200]  # no local temp path in the output
        return json.loads(r.stdout), None


def compare(text):
    o, err = official(text)
    mine = parse(text)
    if o is None:
        return "official_error", err
    oreq = sorted((q["Path"], q["Version"], bool(q.get("Indirect"))) for q in (o.get("Require") or []))
    mreq = sorted(mine["requires"])
    same = ((o.get("Module") or {}).get("Path") == mine["module"] and (o.get("Go") or None) == mine["go"]
            and (o.get("Toolchain") or None) == mine["toolchain"] and oreq == mreq)
    return ("agree" if same else "disagree"), None if same else {"official": [(o.get("Module") or {}).get("Path"),
                                                                             o.get("Go"), o.get("Toolchain"), len(oreq)],
                                                                "mine": [mine["module"], mine["go"], mine["toolchain"], len(mreq)]}


res = {"agree": 0, "disagree": 0, "official_error": 0, "examples": []}
for mod, ver, text in sample:
    k, info = compare(text)
    res[k] += 1
    if k != "agree" and len(res["examples"]) < 10:
        res["examples"].append([mod, ver, info])
res["sample"] = len(sample)

# corrupted copies must disagree: drop the go line / alter one requirement version
bad = 0
for mod, ver, text in sample[:50]:
    alt = text.replace("\ngo 1.", "\ngo 1.9", 1) if "\ngo 1." in text else text + "\nrequire x.example/y v1.0.0\n"
    o, err = official(alt)
    m = parse(alt)
    if o is None or (o.get("Go") or None) != m["go"]:
        continue
    # compare the corrupted text's parse with the ORIGINAL official parse: must differ
    o0, _ = official(text)
    if o0 is not None and ((o0.get("Go") or None) != m["go"] or len(o0.get("Require") or []) != len(m["requires"])):
        bad += 1
res["corruption_detected"] = bad

# ordering against go/version.Compare
vals = set()
for mod, ver, text in mods:
    g = parse(text)["go"]
    if g:
        vals.add(g)
vals = sorted(v for v in vals if gokey(v) is not None)
src = ('package main\nimport ("bufio";"fmt";"go/version";"os";"sort")\nfunc main(){s:=bufio.NewScanner(os.Stdin);'
       'var v []string;for s.Scan(){v=append(v,s.Text())};sort.SliceStable(v,func(i,j int)bool{return '
       'version.Compare("go"+v[i],"go"+v[j])<0});for _,x:=range v{fmt.Println(x)}}\n')
with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "main.go"), "w").write(src)
    open(os.path.join(td, "go.mod"), "w").write("module sortcheck\n\ngo 1.22\n")
    r = subprocess.run([GO, "run", "."], input="\n".join(vals), capture_output=True, text=True, cwd=td,
                       env={**os.environ, "GOTOOLCHAIN": "local"})
go_order = r.stdout.split()
mine_order = sorted(vals, key=gokey)
res["ordering"] = {"values": len(vals), "same_order": go_order == mine_order,
                   "go_stderr": r.stderr.strip()[:200]}
if go_order != mine_order:
    res["ordering"]["first_difference"] = next(((a, b) for a, b in zip(go_order, mine_order) if a != b), None)

json.dump(res, open(os.path.join(ROOT, "results", "validation.json"), "w", encoding="utf-8"), indent=1)
print(json.dumps(res, indent=1)[:3000])
# A file the official parser refuses (e.g. a requirement written as a bare commit hash, which today's go command
# rejects) cannot be compared; it is reported, not counted as agreement.
ok = res["disagree"] == 0 and res["ordering"]["same_order"] and bad > 0
sys.exit(0 if ok else 1)
