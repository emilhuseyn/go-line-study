# The go line in go.mod before and after Go 1.21: replication package

Data and code for the paper "When a Language Version Became a Requirement: The go Line in go.mod Before and After
Go 1.21" (Journal of Computer Languages, submitted).

## Reproduce the numbers from the shipped data

    gunzip -k data/*.gz          # releases.csv, pairs.csv, depmax.csv, depmods.jsonl
    python scripts/04_analyse.py # writes results/numbers.json
    python scripts/06_tables.py  # LaTeX macros and tables (expects a build/ folder next to scripts/)

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
