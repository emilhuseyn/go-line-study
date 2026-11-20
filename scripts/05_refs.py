"""Row 45, step 5: resolve every scholarly reference through Crossref; authors, venue, year and pages are taken
from the record, never typed from memory. Writes research/references_crossref.json and prints each match for a
by-hand check of title identity.

    py scripts/05_refs.py
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "go-line-study/1.0 (research script)"}

WANT = {
    "sun2026clash": "The Unresolved Clash: Systemic Issues in Golang's Dual Dependency Management Regimes",
    "wang2021hero": "Hero: On the Chaos When PATH Meets Modules",
    "li2023semver": "A Large-Scale Empirical Study on Semantic Versioning in Golang Ecosystem",
    "hu2024vuln": "Empirical Analysis of Vulnerabilities Life Cycle in Golang Ecosystem",
    "rustunstable": "Demystifying Rust Unstable Features at Ecosystem Scale: Evolution, Propagation, and Mitigation",
    "decan2019": "An empirical comparison of dependency network evolution in seven software packaging ecosystems",
    "kikas2017": "Structure and evolution of package dependency networks",
    "bogart2021": "When and How to Make Breaking Changes: Policies and Practices in 18 Open Source Software Ecosystems",
    "raemaekers2017": "Semantic versioning and impact of breaking changes in the Maven repository",
    "dietrich2019": "Dependency Versioning in the Wild",
    "dyer2014": "Mining billions of AST nodes to study actual and potential usage of Java language features",
    "parnin2011": "Java generics adoption",
    "malloy2017": "Quantifying the transition from Python 2 to 3: An empirical study of Python applications",
    "zerouali2019lag": "A formal framework for measuring technical lag in component repositories",
    "gonzalez2017lag": "Technical Lag in Software Compilations: Measuring How Outdated a Software Deployment Is",
    "stackage": "The Stackage repository: An exploratory study of its evolution",
    "cocktails": "Mining Programming Cocktails from GitHub",
    "wittern2016": "A look at the dynamics of the JavaScript package ecosystem",
    "decan2021semver": "What do package dependencies tell us about semantic versioning?",
    "lamothe2021": "A systematic review of API evolution literature",
}


def norm(s):
    return "".join(c for c in s.lower() if c.isalnum())


out = {}
for key, title in WANT.items():
    q = urllib.parse.urlencode({"query.title": title, "rows": 5,
                                "select": "DOI,title,author,container-title,published,page,volume,issue,type"})
    d = json.load(urllib.request.urlopen(urllib.request.Request("https://api.crossref.org/works?" + q, headers=UA), timeout=60))
    best = None
    for it in d["message"]["items"]:
        t = (it.get("title") or [""])[0]
        if norm(t) == norm(title) or norm(title) in norm(t) or norm(t) in norm(title) and len(norm(t)) > 30:
            best = it
            break
    if not best:
        print("NO EXACT MATCH:", key, "|", title)
        for it in d["message"]["items"][:3]:
            print("     candidate:", (it.get("title") or [""])[0][:100], it.get("DOI"))
        out[key] = None
        continue
    au = ["%s %s" % (a.get("given", ""), a.get("family", "")) for a in best.get("author", [])]
    y = (best.get("published") or {}).get("date-parts", [[None]])[0][0]
    out[key] = {"doi": best["DOI"], "title": (best.get("title") or [""])[0], "authors": au,
                "venue": (best.get("container-title") or [""])[0], "year": y, "volume": best.get("volume"),
                "issue": best.get("issue"), "pages": best.get("page"), "type": best.get("type")}
    print("%-16s %s | %s | %s | %s" % (key, y, out[key]["venue"][:45], out[key]["title"][:70], best["DOI"]))
    time.sleep(1)
os.makedirs(os.path.join(ROOT, "research"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "research", "references_crossref.json"), "w", encoding="utf-8"), indent=1,
          ensure_ascii=False)
