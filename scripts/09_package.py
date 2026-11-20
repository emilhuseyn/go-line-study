"""Row 45, step 9: the replication package (build/replication_package/ and build/replication_package.zip).

Contents: README, the frozen analysis plan, every script, the derived data (gzipped CSV/JSONL) and the results.
The raw go.mod texts are not redistributed; the module mirror serves released versions immutably, so
01_collect.py fetches the same files again. The package must regenerate results/numbers.json byte for byte from
its own data; this script checks that before writing the zip.

    py scripts/09_package.py
"""
import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "replication_package")
# The folder is also the git working tree of github.com/emilhuseyn/go-line-study (public since 20.11.2026, Emil's
# word): keep .git and LICENSE, rebuild everything else.
for d in ("scripts", "plan", "data", "results", "research"):
    if os.path.exists(os.path.join(OUT, d)):
        shutil.rmtree(os.path.join(OUT, d))
    os.makedirs(os.path.join(OUT, d))
for f in sorted(os.listdir(os.path.join(ROOT, "scripts"))):
    if f.endswith(".py") and f != "08_gate.py":  # the manuscript gate is about our own build, not the data
        shutil.copy2(os.path.join(ROOT, "scripts", f), os.path.join(OUT, "scripts", f))
shutil.copy2(os.path.join(ROOT, "plan", "analysis_plan.md"), os.path.join(OUT, "plan"))
for f in ("references_crossref.json", "references_verified.md", "tidy_demo.txt"):
    shutil.copy2(os.path.join(ROOT, "research", f), os.path.join(OUT, "research", f))
for f in ("numbers.json", "build_counts.json", "validation.json"):
    shutil.copy2(os.path.join(ROOT, "results", f), os.path.join(OUT, "results", f))
for f in ("frame.json", "go_releases.json"):
    shutil.copy2(os.path.join(ROOT, "data", f), os.path.join(OUT, "data", f))
for f in ("releases.csv", "pairs.csv", "depmax.csv", "depmods.jsonl"):
    # mtime=0 and no file name in the header: the same data gives the same bytes, so git sees no false change
    with open(os.path.join(ROOT, "data", f), "rb") as src, open(os.path.join(OUT, "data", f + ".gz"), "wb") as raw, \
            gzip.GzipFile(filename="", mode="wb", compresslevel=9, fileobj=raw, mtime=0) as dst:
        shutil.copyfileobj(src, dst)

README = """# The go line in go.mod before and after Go 1.21: replication package

Data and code for the paper "When a Language Version Became a Requirement: The go Line in go.mod Before and After
Go 1.21" (Journal of Computer Languages, submitted).

## Reproduce the numbers from the shipped data

    gunzip -k data/*.gz            # releases.csv, pairs.csv, depmax.csv, depmods.jsonl
    python scripts/04_analyse.py   # planned analyses and the year-by-year shares -> results/numbers.json
    python scripts/04c_explore.py  # exploratory: who sets inherited lines (adds "explore" to numbers.json)
    python scripts/06_tables.py    # LaTeX macros and tables (expects a build/ folder next to scripts/)
    python scripts/06b_figure.py   # Figure 1 (needs matplotlib)
    python scripts/11_tidy_demo.py # the inheritance rule shown with a Go toolchain (output: research/tidy_demo.txt)

Requires Python 3.11+ and SciPy. `results/numbers.json` in this package was produced this way.

## Collect the data again

    python scripts/01_collect.py frame       # top 2,000 Go modules by dependent packages (ecosyste.ms)
    python scripts/01_collect.py releases    # Go release dates (go.dev/doc/devel/release)
    python scripts/01_collect.py mods        # .info and .mod of every tagged version (proxy.golang.org)
    python scripts/01b_retry.py              # retry network errors
    python scripts/02_build.py               # releases.csv, pairs.csv
    python scripts/03_deps.py                # go lines of required module versions, depmax.csv
    python scripts/04b_validate.py           # parser against `go mod edit -json` (needs a Go toolchain)

All requests are anonymous. The module mirror serves released versions immutably, so the go.mod files are the same;
the ecosyste.ms ranking and the set of published versions change over time.

## Files

- `plan/analysis_plan.md`: the analysis plan, committed before data collection, with the clarifications logged
  before analysis.
- `data/frame.json`: the 2,000 modules and their dependent counts at the snapshot.
- `data/releases.csv.gz`: one row per release (module, version, publication time, go line, toolchain line,
  requirements).
- `data/pairs.csv.gz`: consecutive releases with their semantic-version step and go lines.
- `data/depmods.jsonl.gz`: the go line of every required module version that was read.
- `data/depmax.csv.gz`: for raising and latest releases, the highest go line among their requirements.
- `results/`: numbers.json (every number in the paper), build_counts.json (exclusions), validation.json.
- `research/`: bibliographic records of the references and the quoted Go documentation.

Code: written and run by the AI system Claude (Anthropic, Claude Opus 5.5) through Claude Code, as stated in the
paper. License: MIT for the code, CC BY 4.0 for the derived data.
"""
open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write(README)

# the package must regenerate numbers.json from its own data
with __import__("tempfile").TemporaryDirectory() as td:
    pk = os.path.join(td, "pk")
    shutil.copytree(OUT, pk)
    for f in os.listdir(os.path.join(pk, "data")):
        if f.endswith(".gz"):
            with gzip.open(os.path.join(pk, "data", f), "rb") as src, open(os.path.join(pk, "data", f[:-3]), "wb") as dst:
                shutil.copyfileobj(src, dst)
    os.remove(os.path.join(pk, "results", "numbers.json"))
    for step in ("04_analyse.py", "04c_explore.py"):
        r = subprocess.run([sys.executable, os.path.join(pk, "scripts", step)], capture_output=True, text=True,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode:
            raise SystemExit("STOP: %s failed in the package: %s" % (step, r.stderr[-400:]))
    a = hashlib.sha256(open(os.path.join(pk, "results", "numbers.json"), "rb").read()).hexdigest()
    b = hashlib.sha256(open(os.path.join(ROOT, "results", "numbers.json"), "rb").read()).hexdigest()
    print("regenerated numbers.json identical:", a == b, a[:12], b[:12], r.returncode)
    if a != b:
        raise SystemExit("STOP: the package does not reproduce numbers.json")

zp = os.path.join(ROOT, "build", "replication_package.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for base, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(base, f)
            if ".git" not in os.path.relpath(p, OUT).split(os.sep):
                z.write(p, os.path.relpath(p, OUT))
print("package:", zp, os.path.getsize(zp) // 1024, "KB")
