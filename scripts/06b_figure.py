"""Row 45, step 6b: Figure 1 (year-by-year shares) and the table of inheriting raises with and without a
golang.org/x setter. Reads results/numbers.json only.

    py scripts/06b_figure.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = json.load(open(os.path.join(ROOT, "results", "numbers.json"), encoding="utf-8"))
ex, by = N["exploratory"], N["rq1"]["by_year"]
xy = N["explore"]["inherit_by_year_x"]
years = [y for y in sorted(by) if y in xy]
excl = [100 * by[y]["excl"]["p"] for y in years]
raise_ = [100 * ex["raise_share"][y]["p"] for y in years]
inh = [100 * xy[y]["inherit"] / xy[y]["eligible"] for y in years]
inh_x = [100 * xy[y]["inherit_x"] / xy[y]["eligible"] for y in years]
yi = [int(y) for y in years]

plt.rcParams.update({"font.size": 9, "font.family": "serif"})
fig, ax = plt.subplots(figsize=(6.0, 3.4))
ax.plot(yi, inh, marker="o", color="black", label="raises consistent with inheritance")
ax.plot(yi, inh_x, marker="s", color="black", linestyle=":", label="... with a golang.org/x setter")
ax.plot(yi, excl, marker="^", color="0.45", label="releases excluding the oldest supported Go")
ax.plot(yi, raise_, marker="v", color="0.45", linestyle="--", label="consecutive releases that raise the line")
ax.axvline(2023 + 7 / 12, color="0.6", linewidth=0.8)
ax.text(2023 + 7 / 12 + 0.08, 93, "Go 1.21", fontsize=8, color="0.3")
ax.set_ylabel("share (%)")
ax.set_ylim(0, 100)
ax.set_xticks(yi)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, fontsize=7.5, loc="upper left", bbox_to_anchor=(0.06, 1.02), ncol=1)
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "build", "fig_years.pdf"))

rows = []
for y in years:
    v = xy[y]
    rows.append("%s & %s & %.1f & %.1f & %.1f \\\\" % (y, "{:,}".format(v["eligible"]), 100 * v["inherit"] / v["eligible"],
                                                      100 * v["inherit_x"] / v["eligible"],
                                                      100 * v["inherit_nox"] / v["eligible"]))
open(os.path.join(ROOT, "build", "tables", "inherit_x_years.tex"), "w", encoding="utf-8").write("\n".join(rows) + "\n")
print("figure and table written for", years)
