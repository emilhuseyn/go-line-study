# Web sources read 20.11.2026 (quotes copied from the fetched pages)

- go.dev/doc/toolchain (Go Toolchains):
  - "A module's go line must declare a version greater than or equal to the go version declared by each of the modules listed in require statements."
  - "A workspace's go line must declare a version greater than or equal to the go version declared by each of the modules listed in use statements."
  - "The Go toolchain refuses to load a module or workspace that declares a minimum required Go version greater than the toolchain's own version."
  - "The choice of Go toolchain being used depends on the GOTOOLCHAIN environment setting and the go and toolchain lines in the main module's go."
  - "In the standard configuration, the go command uses its own bundled toolchain when that toolchain is at least as new as the go or toolchain lines in the main module or workspace."
  - "env file sets the default GOTOOLCHAIN=auto , but repackaged Go toolchains may change this value."
  - "GOTOOLCHAIN=auto is shorthand for GOTOOLCHAIN=local+auto ; similarly, GOTOOLCHAIN=path is shorthand for GOTOOLCHAIN=local+path ."
- go.dev/blog/toolchain: Russ Cox, 14 August 2023, "Forward Compatibility and Toolchain Management in Go 1.21": "Starting in Go 1.21, Go toolchains will treat the go line in go.mod not as a guideline but as a rule".
- go.dev/doc/devel/release: "Each major Go release is supported until there are two newer major releases." (phrase found: "supported until there are two newer major releases").
- research.swtch.com/vgo-mvs: Russ Cox, "Minimal Version Selection (Go & Versioning, Part 4)", 2018.
- TOSEM 2026 Sun et al.: author version https://cs.nju.edu.cn/changxu/1_publications/26/TOSEM26_01.pdf, not in Crossref on 20.11.2026; covers GOPATH vs modules, replace, module path, GOPROXY immutability; 14 mentions of toolchain, none about the go line.
- doc.rust-lang.org/cargo/reference/rust-version.html: "When your package is compiled on an unsupported toolchain, Cargo will report that as an error to the user." / "A user can opt-in to an unsupported build of a package with the --ignore-rust-version flag." / "The resolver may take Rust version into account when picking dependencies."
- packaging.python.org core metadata, Requires-Python: "This field specifies the Python version(s) that the distribution is compatible with. Installation tools may look at this when picking which version of a project to install."
- docs.npmjs.com package.json, engines: "Unless the user has set the engine-strict config flag, this field is advisory only and will only produce warnings when your package is installed as a dependency."
- go.googlesource.com/proposal/+/HEAD/design/69095-x-repo-continuous-go.md: Author Dmitri Shuralyov, last updated 2024-08-27. "The value of the go directive in golang.org/x repositories is automatically maintained to be at least 1.(N-1).0, where Go 1.N is the most recent major Go release, and Go 1.(N-1) is the previous major Go release." / "Picking N-1 makes this a no-op for golang.org/x module users who are using a supported Go release." (Found 20.11 after a draft sentence wrongly said no policy was published; the sentence was replaced.)
