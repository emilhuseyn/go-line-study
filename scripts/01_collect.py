"""Row 45, step 1: the frame and every tagged version's go.mod and publication time.

    py scripts/01_collect.py frame      top 2,000 Go modules by dependent packages (ecosyste.ms)
    py scripts/01_collect.py releases   Go release dates (go.dev/doc/devel/release)
    py scripts/01_collect.py mods       @v/list, .info and .mod for every tagged version (resumable)

Everything is auth-free. Outputs go to data/ (gitignored); counts of every failure are printed and saved.
"""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = {"User-Agent": "go-line-study/1.0 (research script)"}
N_TOP = 2000


def get(url, tries=4):
    for a in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, ""
            if a == tries - 1:
                return e.code, ""
        except Exception:
            if a == tries - 1:
                return -1, ""
        time.sleep(2 * (a + 1))
    return -1, ""


def esc(s):
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), s)


def frame():
    out, page = [], 1
    while len(out) < N_TOP:
        st, body = get("https://packages.ecosyste.ms/api/v1/registries/proxy.golang.org/packages?"
                       "sort=dependent_packages_count&order=desc&per_page=100&page=%d" % page)
        if st != 200:
            raise SystemExit("STOP: ecosyste.ms page %d returned %s" % (page, st))
        rows = json.loads(body)
        if not rows:
            break
        for p in rows:
            out.append({"name": p["name"], "dependent_packages_count": p.get("dependent_packages_count"),
                        "dependent_repos_count": p.get("dependent_repos_count"),
                        "versions_count": p.get("versions_count"), "repository_url": p.get("repository_url")})
        page += 1
        time.sleep(0.5)
    out = out[:N_TOP]
    json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "source": "packages.ecosyste.ms proxy.golang.org "
               "sort=dependent_packages_count desc", "modules": out},
              open(os.path.join(DATA, "frame.json"), "w", encoding="utf-8"), indent=1)
    print("frame:", len(out), "modules; last count", out[-1]["dependent_packages_count"])


def releases():
    st, body = get("https://go.dev/doc/devel/release")
    if st != 200:
        raise SystemExit("STOP: release page %s" % st)
    rel = {}
    for m in re.finditer(r"go(1\.\d+(?:\.\d+)?)\s*\(released\s+(\d{4}-\d{2}-\d{2})\)", body):
        rel.setdefault(m.group(1), m.group(2))
    json.dump({"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "releases": rel},
              open(os.path.join(DATA, "go_releases.json"), "w", encoding="utf-8"), indent=1)
    minors = sorted((k for k in rel if k.count(".") == 1), key=lambda v: int(v.split(".")[1]))
    print("go releases:", len(rel), "minor:", minors[0], "...", minors[-1], rel[minors[-1]])


def one_version(mod, ver):
    base = "https://proxy.golang.org/%s/@v/%s" % (esc(mod), esc(ver))
    si, info = get(base + ".info")
    sm, gomod = get(base + ".mod")
    t = None
    if si == 200:
        try:
            t = json.loads(info).get("Time")
        except ValueError:
            si = -2
    return {"version": ver, "info_status": si, "time": t, "mod_status": sm, "mod": gomod if sm == 200 else None}


def one_module(i, mod, outdir):
    path = os.path.join(outdir, "%04d.json" % i)
    if os.path.exists(path):
        return "cached"
    sl, body = get("https://proxy.golang.org/%s/@v/list" % esc(mod))
    rec = {"rank": i + 1, "module": mod, "list_status": sl, "versions": []}
    if sl == 200:
        vers = [v for v in body.split() if v.strip()]
        with cf.ThreadPoolExecutor(16) as ex:
            rec["versions"] = list(ex.map(lambda v: one_version(mod, v), vers))
    tmp = path + ".tmp"
    json.dump(rec, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, path)
    return "ok" if sl == 200 else "list %s" % sl


def mods():
    fr = json.load(open(os.path.join(DATA, "frame.json"), encoding="utf-8"))["modules"]
    outdir = os.path.join(DATA, "modules")
    os.makedirs(outdir, exist_ok=True)
    t0, stats = time.time(), {}
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(one_module, i, m["name"], outdir): i for i, m in enumerate(fr)}
        for k, f in enumerate(cf.as_completed(futs), 1):
            r = f.result()
            stats[r.split()[0]] = stats.get(r.split()[0], 0) + 1
            if k % 100 == 0:
                print("%d/%d modules, %.0fs, %s" % (k, len(fr), time.time() - t0, stats), flush=True)
    print("done:", stats)


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    {"frame": frame, "releases": releases, "mods": mods}[sys.argv[1]]()
