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
