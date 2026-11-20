# Analysis plan, row 45 (frozen before data collection, 20.11.2026)

Topic chosen by Emil from three AI-proposed candidates (`_shared/B_TOPIC_CANDIDATES_COLA_2026-11-20.md`).
Target: Journal of Computer Languages (Elsevier, Scimago 2025 Q3 Software, Q2 Computer Networks), subscription
route (no fee). Single-anonymized review.
Working method B (`_shared/STRATEGY_2026-11-19.md`), as Emil chose it on 20.11 ("hansında az iş görəcəmsə"): the AI
system collects data, runs the analysis and drafts the whole text; Emil reads all of it and edits it himself.
Elsevier requires the author to edit and adapt all AI output thoroughly; the AI statement will say exactly what
he did and nothing more.

Any change to this file after the first data file exists is logged at the bottom with its date and reason.

## Background the study rests on

Before Go 1.21 (released 2023-08-08) the `go` line in go.mod was advisory: an older toolchain tried to build the
module anyway. Since Go 1.21 it is a mandatory minimum: a toolchain older than the line refuses the module
(or, with GOTOOLCHAIN=auto, downloads a newer toolchain), and the go command keeps the main module's line at
least as high as the line of every module in its build list, so `go get` / `go mod tidy` raise it when a
dependency's line is higher. Go 1.21 also added the `toolchain` line and patch-level `go` lines (`go 1.21.0`).
Source: go.dev/doc/toolchain, go.dev/ref/mod, proposal 57001. The study measures what this language-governance
change did to the declarations of the ecosystem's most depended-upon modules.

## Population and snapshot

1. The 2,000 Go modules with the most dependent packages on ecosyste.ms (registry proxy.golang.org,
   `sort=dependent_packages_count`), fetched once; the fetch date and the counts are saved.
2. For each module: its tagged versions from `proxy.golang.org/<module>/@v/list` (pseudo-versions are not
   listed there and are excluded), each version's `.info` (publication time) and `.mod` (the go.mod file).
   Module paths are case-encoded as the proxy requires.
3. For RQ3 only, the `.mod` of every module version that those go.mod files require (cached by module@version).
4. Go release dates from go.dev/doc/devel/release, saved.
5. Everything is auth-free. The User-Agent names no person. No GitHub API.

Units: a *release* is one tagged non-prerelease version of one module. Consecutive releases are ordered by
semantic version within a module path. Analysis window: releases published 2019-01-01 to the snapshot;
"before" = published before 2023-08-08, "after" = on or after.

## Research questions and measures

**RQ1. What do modules declare, and how new is it?** For each release: the `go` line (none / X.Y / X.Y.Z /
other), the `toolchain` line (present, value). *Requirement age*: how many Go minor releases the declared version
is behind the newest Go release at the module's publication time (0 = requires the newest). *Support-window
measure*: whether the declared version is newer than the oldest Go release still supported at that time (Go
supports the two newest minor releases), i.e. whether a user on a supported but older Go is excluded.
Reported per year and before/after Go 1.21; latest release per module reported separately.

**RQ2. How often is the line raised without a major version?** For each pair of consecutive releases: whether the
`go` line increased, by how many minor versions, and the semantic-version step of the release that raised it
(patch, minor, or a v0 minor step, reported apart because v0 promises no compatibility). Primary measure: share
of raises that occur in patch or v1+ minor releases, with Wilson 95% intervals, before and after Go 1.21.

**RQ3. Is the line chosen or inherited?** For each release after a raise: `dep_max` = the highest `go` line among
the module versions its go.mod requires (all `require` lines, direct and `// indirect`). A raise is *consistent
with inheritance* when the new line equals `dep_max` and `dep_max` is above the previous line; otherwise
*chosen*. Also counted: releases whose line is below `dep_max` (a 1.21+ go command would rewrite them).
Confirmatory comparison (the natural experiment): the share of raises consistent with inheritance before vs
after Go 1.21. Before 1.21 the go command did not propagate the line, so the "before" share estimates how often
equality happens without the rule. Risk difference with a 95% interval (Newcombe) and Fisher's exact test.

**RQ4. Precision beyond what is needed.** Share of lines with a patch component greater than zero (e.g.
`go 1.22.5`), which exclude users of earlier patch releases of a supported Go version; share with a `toolchain`
line; how often a release's go line has a patch component that no requirement in its build list imposes
(i.e. greater than `dep_max` and set without a new minor version).

## Hypotheses (directional, stated before data)

- H1: After Go 1.21 a larger share of releases declare a version newer than the oldest supported Go release than
  before (RQ1).
- H2: Most go-line raises after Go 1.21 occur in releases that are not major versions (RQ2).
- H3: The share of raises consistent with inheritance is higher after Go 1.21 than before (RQ3).
Each is reported as supported or not supported, with the interval, whatever the result.

## Reporting rules

- Every number in the manuscript is printed by a script into `results/`; no number is typed by hand.
- Proportions with Wilson 95% intervals; no p-value without an effect size.
- Modules without versions, versions whose .mod or .info cannot be fetched, unparseable go lines, and
  requirements whose .mod cannot be fetched are each counted and reported, never silently dropped.
- Threats named in advance: the top-2,000 frame over-represents widely used modules; equality with `dep_max` is
  consistent with inheritance but does not prove it (a maintainer may raise both); the support-window rule is
  the Go team's stated policy, applied mechanically; ecosyste.ms dependent counts are its own measurement.

## Changes after data collection

**20.11.2026, during collection, before any analysis was run** (only a pipeline test on the first ~65 modules,
which printed exclusion counts, not results):
1. Versions whose go.mod declares a different module path (tags carrying another module's go.mod, e.g. in
   prometheus/common) are excluded and counted: the go command refuses such a version.
2. "Raised" in RQ2 and RQ3 means the minor version of the go line increased (1.20 -> 1.21). A patch-only change
   (1.21 -> 1.21.0 -> 1.22.3 within a minor) is not a raise; it is reported under RQ4.
3. RQ3's `dep_max` and RQ4's "patch not imposed by any requirement" are computed for every raising release and
   for the latest release of every module (not for every release), to keep the requirement fetches bounded.
   The "below dep_max" count is reported for those releases.
4. Added sensitivity, because a few modules publish thousands of releases (e.g. cloud SDKs): every release-level
   proportion in RQ1 and RQ2 is also reported with each module weighted equally (the mean of per-module shares),
   and H1 to H3 are also checked on that basis. The release-level results stay primary.
