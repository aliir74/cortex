#!/usr/bin/env python3
"""skill-contracts.py: pin load-bearing sentences in the instruction corpus.

adherence-probe.py asks a model whether a rule still changes behaviour; that is the
real test, but it costs model calls. audit-skill-corpus.py checks generic shape
(frontmatter, devices). Neither notices when a specific sentence that a rule depends
on is edited out of a specific file. This script does only that: each contract names
a file, a regex that must match in it, and why. It is the static half of the probe
loop, free to run on every corpus edit, so a trim that orphans a rule is caught at
edit time instead of at the next probe.

Usage:
    python3 skill-contracts.py                 # check every contract, exit 1 on any failure
    python3 skill-contracts.py --file PATH     # use a specific contracts file
    python3 skill-contracts.py --json          # machine-readable result
    python3 skill-contracts.py --list          # print the contracts without checking
    python3 skill-contracts.py --self-test     # exercise pass, fail and missing-file paths

Default contracts file: $CLAUDE_PLUGIN_DATA/skill-contracts.json
(falling back to the Cortex dir under ~/.claude/plugins/data/, e.g. cortex-cortex/skill-contracts.json). Format, see
skill-contracts.example.json next to this script:
    [{"file": "~/.claude/CLAUDE.md", "pattern": "regex", "why": "one line",
      "flags": "s"}]            # flags optional: any of i, s, m
Add one whenever you write a rule a probe depends on, or trim one from an
always-loaded file into a skill. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
def _data_dir() -> str:
    """$CLAUDE_PLUGIN_DATA when set (it is, inside a Cortex skill run); otherwise the
    first existing Cortex plugin data dir, defaulting to the marketplace-qualified name."""
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env:
        return env
    base = os.path.expanduser("~/.claude/plugins/data")
    for name in ("cortex-cortex", "cortex"):
        if os.path.isdir(os.path.join(base, name)):
            return os.path.join(base, name)
    return os.path.join(base, "cortex-cortex")


DATA_DIR = _data_dir()
DEFAULT_CONTRACTS = os.path.join(DATA_DIR, "skill-contracts.json")
EXAMPLE_CONTRACTS = os.path.join(HERE, "skill-contracts.example.json")
_FLAGS = {"i": re.IGNORECASE, "s": re.DOTALL, "m": re.MULTILINE}


def load_contracts(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("contracts file must hold a JSON list")
    for i, c in enumerate(data):
        for key in ("file", "pattern", "why"):
            if key not in c:
                raise ValueError(f"contract {i} lacks '{key}'")
    return data


def check(contracts: list[dict]) -> list[dict]:
    results = []
    for c in contracts:
        path = os.path.expanduser(c["file"])
        flags = 0
        for ch in c.get("flags", ""):
            flags |= _FLAGS.get(ch, 0)
        entry = {"file": c["file"], "pattern": c["pattern"], "why": c["why"]}
        if not os.path.isfile(path):
            entry.update(status="missing-file")
        else:
            text = open(path, encoding="utf-8", errors="ignore").read()
            try:
                hit = re.search(c["pattern"], text, flags)
            except re.error as e:
                entry.update(status="bad-regex", detail=str(e))
                results.append(entry)
                continue
            entry.update(status="ok" if hit else "broken")
            if hit:
                entry["line"] = text.count("\n", 0, hit.start()) + 1
        results.append(entry)
    return results


def _report(results: list[dict]) -> int:
    bad = [r for r in results if r["status"] != "ok"]
    for r in results:
        mark = "OK  " if r["status"] == "ok" else "FAIL"
        where = f":{r['line']}" if r.get("line") else ""
        print(f"{mark} {r['file']}{where}  [{r['status']}]  {r['why']}")
        if r["status"] != "ok":
            print(f"       pattern: {r['pattern']}")
    print(f"\n{len(results) - len(bad)}/{len(results)} contracts hold.")
    if bad:
        print("A FAIL means a sentence some rule depends on is gone from that file. "
              "Restore it, or move the contract to the file that now carries the rule "
              "and confirm that file loads whenever the rule is needed.")
    return 1 if bad else 0


def _self_test() -> int:
    import tempfile
    rc = 0
    with tempfile.TemporaryDirectory() as d:
        good = os.path.join(d, "good.md")
        with open(good, "w", encoding="utf-8") as fh:
            fh.write("# x\nAlways run `make verify` before claiming done.\n")
        cases = [
            {"file": good, "pattern": r"make verify", "why": "present"},
            {"file": good, "pattern": r"never written here", "why": "absent"},
            {"file": os.path.join(d, "nope.md"), "pattern": r"x", "why": "missing"},
            {"file": good, "pattern": r"(", "why": "bad regex"},
        ]
        got = [r["status"] for r in check(cases)]
        want = ["ok", "broken", "missing-file", "bad-regex"]
        if got != want:
            print(f"REGRESSION: statuses {got} != {want}")
            rc = 1
    # the bundled example file must parse and every regex must compile
    try:
        example = load_contracts(EXAMPLE_CONTRACTS)
        for c in example:
            re.compile(c["pattern"])
    except Exception as e:  # noqa: BLE001
        print(f"REGRESSION: example contracts file unusable: {e}")
        rc = 1
    if rc == 0:
        print(f"self-test: pass/broken/missing/bad-regex paths behave; "
              f"{len(example)} example contracts parse.")
    return rc


def main(argv: list[str]) -> int:
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    if "--self-test" in argv:
        return _self_test()
    path = DEFAULT_CONTRACTS
    for i, a in enumerate(argv):
        if a == "--file" and i + 1 < len(argv):
            path = os.path.expanduser(argv[i + 1])
    if not os.path.isfile(path):
        print(f"no contracts file at {path}. Copy {EXAMPLE_CONTRACTS} there "
              f"(or pass --file) and edit it.", file=sys.stderr)
        return 1
    try:
        contracts = load_contracts(path)
    except (OSError, ValueError) as e:
        print(f"cannot load contracts: {e}", file=sys.stderr)
        return 1
    if "--list" in argv:
        for c in contracts:
            print(f"{c['file']}  ::  {c['pattern']}  ::  {c['why']}")
        return 0
    results = check(contracts)
    if "--json" in argv:
        print(json.dumps(results, indent=1))
        return 1 if any(r["status"] != "ok" for r in results) else 0
    return _report(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
