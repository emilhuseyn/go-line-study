"""go.mod parsing and Go version / semver ordering shared by every step of row 45."""
import re

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$")
GOVER = re.compile(r"^1\.(\d+)(?:\.(\d+))?(?:(rc|beta)(\d+))?$")


def strip_comment(line):
    i = line.find("//")
    return (line[:i] if i >= 0 else line).strip(), (line[i + 2:].strip() if i >= 0 else "")


def parse(text):
    """Return dict: module, go (raw or None), toolchain (raw or None), requires [(path, version, indirect)]."""
    out = {"module": None, "go": None, "toolchain": None, "requires": [], "go_lines": 0}
    if text is None:
        return out
    block = None
    for raw in text.splitlines():
        code, comment = strip_comment(raw)
        if not code:
            continue
        if block:
            if code == ")":
                block = None
                continue
            if block == "require":
                parts = code.split()
                if len(parts) >= 2:
                    out["requires"].append((parts[0].strip('"'), parts[1], "indirect" in comment))
            continue
        parts = code.split()
        kw = parts[0]
        if len(parts) >= 2 and parts[1] == "(":
            block = kw
            continue
        if kw == "module" and len(parts) >= 2:
            out["module"] = parts[1].strip('"')
        elif kw == "go" and len(parts) >= 2:
            out["go"] = parts[1]
            out["go_lines"] += 1
        elif kw == "toolchain" and len(parts) >= 2:
            out["toolchain"] = parts[1]
        elif kw == "require" and len(parts) >= 3:
            out["requires"].append((parts[1].strip('"'), parts[2], "indirect" in comment))
    return out


def gokey(v):
    """Comparable key for a go line value, in the go command's order: 1.21 < 1.21rc1 < 1.21.0 < 1.21.1.
    Returns (minor, patch, rc) with 1.21 -> (21, -2, 0), 1.21rcN -> (21, -1, N), 1.21.P -> (21, P, 0).
    None if unparseable."""
    if v is None:
        return None
    m = GOVER.match(v)
    if not m:
        return None
    minor = int(m.group(1))
    if m.group(3) is not None:
        return (minor, -1, int(m.group(4)))
    if m.group(2) is None:
        return (minor, -2, 0)
    return (minor, int(m.group(2)), 0)


def semkey(v):
    m = SEMVER.match(v)
    if not m:
        return None
    pre = m.group(4)
    pre_key = (1,) if pre is None else (0,) + tuple((0, int(p)) if p.isdigit() else (1, p) for p in pre.split("."))
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), pre_key)


def is_prerelease(v):
    m = SEMVER.match(v)
    return bool(m and m.group(4))


def step(prev, cur):
    """Semantic-version step from prev to cur: major / minor / patch / v0-minor / other."""
    a, b = SEMVER.match(prev), SEMVER.match(cur)
    if not (a and b):
        return "other"
    pa, pb = tuple(int(x) for x in a.groups()[:3]), tuple(int(x) for x in b.groups()[:3])
    if pb[0] != pa[0]:
        return "major"
    if pb[1] != pa[1]:
        return "v0-minor" if pb[0] == 0 else "minor"
    if pb[2] != pa[2]:
        return "patch"
    return "other"
