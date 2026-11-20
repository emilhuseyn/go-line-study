"""Row 45, step 7: build/refs.bib from research/references_crossref.json (Crossref records) plus the web sources
recorded in research/references_verified.md. Page ranges use a single hyphen.

    py scripts/07_bib.py
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "research", "references_crossref.json"), encoding="utf-8"))

TEX = {"&": r"\&", "%": r"\%", "_": r"\_", "#": r"\#"}


def esc(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = s.replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", ", ").replace("\u2019", "'").replace("\u2018", "'")
    return "".join(TEX.get(c, c) for c in s)


def authors(lst):
    out = []
    for a in lst:
        a = a.strip()
        parts = a.split()
        if len(parts) >= 2:
            out.append("%s, %s" % (parts[-1], " ".join(parts[:-1])))
        else:
            out.append(a)
    return " and ".join(esc(x) for x in out)


entries = []
for key, r in R.items():
    if r is None:
        continue
    journal = r["type"] == "journal-article"
    f = {"author": authors(r["authors"]), "title": "{" + esc(r["title"]) + "}", "year": str(r["year"]),
         "doi": r["doi"]}
    if journal:
        f["journal"] = esc(r["venue"])
        if r.get("volume"):
            f["volume"] = r["volume"]
        if r.get("issue"):
            f["number"] = r["issue"]
    else:
        f["booktitle"] = esc(r["venue"])
    if r.get("pages"):
        f["pages"] = r["pages"].replace("--", "-").replace("\u2013", "-")
    if journal and not r.get("volume") and f.get("pages"):
        # an article in press has an article number but no volume; the style would glue it to the DOI
        f["journal"] = f["journal"] + ", Article " + f.pop("pages") + ", in press"
    kind = "article" if journal else "inproceedings"
    entries.append("@%s{%s,\n%s\n}" % (kind, key, ",\n".join("  %s = {%s}" % (k, v) for k, v in f.items())))

WEB = [
    ("sun2026clash", "misc", {"author": "Sun, Weijie and Wang, Ying and Wang, Huiyan and Xu, Chang and Cheung, Shing-Chi",
                              "title": "{The Unresolved Clash: Systemic Issues in Golang's Dual Dependency Management Regimes}",
                              "year": "2026",
                              "howpublished": "ACM Transactions on Software Engineering and Methodology, to appear; author's accepted version at \\url{https://cs.nju.edu.cn/changxu/1_publications/26/TOSEM26_01.pdf}"}),
    ("gotoolchain", "misc", {"author": "{The Go Authors}", "title": "{Go Toolchains}", "year": "2026",
                             "howpublished": "\\url{https://go.dev/doc/toolchain}", "note": "Accessed 20 November 2026"}),
    ("gomodref", "misc", {"author": "{The Go Authors}", "title": "{Go Modules Reference}", "year": "2026",
                          "howpublished": "\\url{https://go.dev/ref/mod}", "note": "Accessed 20 November 2026"}),
    ("gorelease", "misc", {"author": "{The Go Authors}", "title": "{Release History}", "year": "2026",
                           "howpublished": "\\url{https://go.dev/doc/devel/release}", "note": "Accessed 20 November 2026"}),
    ("cox2023toolchain", "misc", {"author": "Cox, Russ", "title": "{Forward Compatibility and Toolchain Management in Go 1.21}",
                                  "year": "2023", "howpublished": "The Go Blog, 14 August 2023, \\url{https://go.dev/blog/toolchain}"}),
    ("cox2018mvs", "misc", {"author": "Cox, Russ", "title": "{Minimal Version Selection (Go \\& Versioning, Part 4)}",
                            "year": "2018", "howpublished": "\\url{https://research.swtch.com/vgo-mvs}"}),
    ("proposal57001", "misc", {"author": "Cox, Russ", "title": "{Proposal: Extended Forwards Compatibility in Go}",
                               "year": "2023", "howpublished": "Go design document 57001, \\url{https://go.googlesource.com/proposal/+/master/design/57001-gotoolchain.md}"}),
    ("ecosystems", "misc", {"author": "{Ecosyste.ms}", "title": "{Packages: proxy.golang.org registry}", "year": "2026",
                            "howpublished": "\\url{https://packages.ecosyste.ms}", "note": "Accessed 20 November 2026"}),
    ("goproxy", "misc", {"author": "{The Go Authors}", "title": "{Go Module Mirror, Index, and Checksum Database}",
                         "year": "2026", "howpublished": "\\url{https://proxy.golang.org}", "note": "Accessed 20 November 2026"}),
]
for key, kind, f in WEB:
    entries.append("@%s{%s,\n%s\n}" % (kind, key, ",\n".join("  %s = {%s}" % (k, v) for k, v in f.items())))
open(os.path.join(ROOT, "build", "refs.bib"), "w", encoding="utf-8").write("\n\n".join(entries) + "\n")
print("entries:", len(entries))
bad = [e for e in entries if re.search("[\u2010-\u2015\u2212]", e)]
print("entries with a dash character:", len(bad))
