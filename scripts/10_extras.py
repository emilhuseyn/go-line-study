"""Row 45, step 10: highlights (3-5 bullets, at most 85 characters each, numbers from numbers.json), vitae (at most
100 words) and the cover letter source. Writes build/submission/.

    py scripts/10_extras.py
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = json.load(open(os.path.join(ROOT, "results", "numbers.json"), encoding="utf-8"))
OUT = os.path.join(ROOT, "build", "submission")
os.makedirs(OUT, exist_ok=True)


def pc(x):
    return "%.1f%%" % (100 * x)


b = N["build"]
r1, r2, r3 = N["rq1"], N["rq2"], N["rq3"]
H = [
    "Go 1.21 made the go line in go.mod a binding, inherited minimum requirement",
    "%s releases of the %s most depended-upon Go modules, before and after Go 1.21"
    % ("{:,}".format(b["releases"]), "{:,}".format(b["modules_in_frame"])),
    "After Go 1.21, %s of raises equal the highest requirement line (%s before)"
    % (pc(r3["after"]["inherit"]["p"]), pc(r3["before"]["inherit"]["p"])),
    "%s of go-line raises come in non-major releases, %s in patch releases"
    % (pc(r2["after"]["raises_nonmajor"]["p"]), pc(r2["after"]["raises_patch"]["p"])),
    "Releases excluding the oldest supported Go fell from %s to %s"
    % (pc(r1["before"]["excludes_oldest_supported"]["p"]), pc(r1["after"]["excludes_oldest_supported"]["p"])),
]
for h in H:
    assert len(h) <= 85, (len(h), h)
open(os.path.join(OUT, "highlights.txt"), "w", encoding="utf-8").write("\n".join("- " + h for h in H) + "\n")

VITAE = ("Emil Huseynov is a staff member of the Center for Information Technologies at Baku State University, "
         "Azerbaijan, and holds a BSc in Computer Science. The research interests of Emil Huseynov are software "
         "ecosystems, mining software repositories and the gap between what a declaration in a software artefact "
         "promises and what it guarantees in practice.")
assert len(VITAE.split()) <= 100
open(os.path.join(OUT, "vitae.txt"), "w", encoding="utf-8").write(VITAE + "\n")

COVER = r"""\documentclass[11pt]{letter}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=2.5cm]{geometry}
\usepackage{xurl}
\signature{Mr. Emil Huseynov\\Center for Information Technologies, Baku State University\\Academic Zahid Khalilov Street 23, Baku AZ1148, Azerbaijan\\emil.huseynov.zabil@bsu.edu.az, ORCID 0009-0007-7142-060X}
\address{}
\date{20 November 2026}
\begin{document}
\begin{letter}{Editors\\Journal of Computer Languages}
\opening{Dear Editors,}

I submit the research article ``When a Language Version Became a Requirement: The go Line in go.mod Before and
After Go 1.21'' for consideration in the Journal of Computer Languages.

Go 1.21 turned the language version declared in every \texttt{go.mod} file from advice into a requirement that the
toolchain enforces and that dependent modules inherit. The paper measures what this change in the language's own
versioning did to the %(frame)s Go modules with the most dependents, %(rel)s releases in all, under an analysis plan
committed before the data were collected. After Go 1.21, %(inh)s of the raises of the line set it exactly to the
highest line among the module's requirements (%(inhb)s before), and nearly all raises arrive in releases that are
not new major versions. The paper fits the journal's areas of language evolution and of libraries, run-time
environments and language ecosystems, and continues the ecosystem studies the journal has published, such as the
study of the Stackage repository.

The data and the scripts that produce every number are publicly available, and the paper states how the generative
AI system Claude was used: it designed the study, wrote and ran the code and drafted the text; I chose the journal
and the topic, read the complete manuscript and contributed the parts the declaration names. The manuscript has not
been published and is not under consideration elsewhere. I declare no competing interests.

\closing{Yours sincerely,}
\end{letter}
\end{document}
""" % {"frame": "{:,}".format(b["modules_in_frame"]), "rel": "{:,}".format(b["releases"]),
       "inh": pc(r3["after"]["inherit"]["p"]).replace("%", "\\%"), "inhb": pc(r3["before"]["inherit"]["p"]).replace("%", "\\%")}
open(os.path.join(OUT, "cover_letter.tex"), "w", encoding="utf-8", newline="\n").write(COVER)
print("\n".join(H))
print("vitae words:", len(VITAE.split()))
