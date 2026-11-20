"""Row 45, step 11: the inheritance rule, demonstrated with the Go toolchain itself.

A module declaring `go 1.22` requires golang.org/x/net v0.36.0 (whose go.mod says `go 1.23.0`). After
`go mod tidy` with GOTOOLCHAIN=local, its own line reads `go 1.23.0`. `go list -m` then shows the go version of each
module whose go.mod was loaded, which is how a maintainer can see what forced the line.

    py scripts/11_tidy_demo.py      writes research/tidy_demo.txt
"""
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = {**os.environ, "GOTOOLCHAIN": "local", "GOFLAGS": "-mod=mod"}
out = []
with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "go.mod"), "w").write("module example.com/check\n\ngo 1.22\n\nrequire golang.org/x/net v0.36.0\n")
    open(os.path.join(td, "main.go"), "w").write('package main\n\nimport _ "golang.org/x/net/html"\n\nfunc main() {}\n')
    out.append("$ go version\n" + subprocess.run(["go", "version"], capture_output=True, text=True, env=ENV).stdout)
    out.append("go.mod before:\n" + open(os.path.join(td, "go.mod")).read())
    r = subprocess.run(["go", "mod", "tidy"], cwd=td, capture_output=True, text=True, env=ENV)
    out.append("$ go mod tidy  (exit %d)\n" % r.returncode)
    after = open(os.path.join(td, "go.mod")).read()
    out.append("go.mod after:\n" + after)
    r = subprocess.run(["go", "list", "-m", "-f", "{{.Path}} {{.GoVersion}}", "all"], cwd=td, capture_output=True,
                       text=True, env=ENV)
    out.append("$ go list -m -f '{{.Path}} {{.GoVersion}}' all\n" + r.stdout)
text = "\n".join(out).replace(tempfile.gettempdir(), "<tmp>")
open(os.path.join(ROOT, "research", "tidy_demo.txt"), "w", encoding="utf-8").write(text)
print(text)
ok = "\ngo 1.23.0\n" in after
print("DEMO:", "line inherited (go 1.22 -> go 1.23.0)" if ok else "NOT REPRODUCED")
sys.exit(0 if ok else 1)
