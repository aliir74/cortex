#!/usr/bin/env python3
"""audit-skill-corpus.py - mechanical health check over a directory of skills.

Answers three questions no eyeball reliably answers:

  1. INTEGRITY  - which skills have frontmatter that silently breaks auto-triggering
                  (no frontmatter at all, missing name/description, `title:` instead
                  of `name:`, trigger phrases parked in a non-standard field the
                  loader ignores).
  2. SHAPE      - which descriptions summarize the workflow instead of naming
                  triggers, the defect that makes a session follow the description
                  and skip the body.
  3. COVERAGE   - how many skills carry each anti-rationalization device, so a
                  corpus can be compared against an external skillset.

Both the local corpus and a shared external skillset are read the same way, which
is the point: the comparison is mechanical, not impressionistic.

Usage:
  audit-skill-corpus.py                          # ~/.claude/skills
  audit-skill-corpus.py --dir path/to/skills     # any skills directory
  audit-skill-corpus.py --dir A --compare B      # side-by-side coverage
  audit-skill-corpus.py --json out.json          # machine-readable

Exit 0 always (this is a report, not a gate). Stdlib only.

Sizing note: caps and token cost are NOT computed here. That is
measure-instruction-corpus.py, which carries the calibrated 2.5 chars/token
estimator. Do not re-derive token counts by hand; bytes//4 is wrong by about 1.6x
for dense instruction prose.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_DIR = os.path.expanduser("~/.claude/skills")

TRIGGER = re.compile(
    r"\bUse when\b|\bUse for\b|\bUse this (?:before|when)\b|\bTriggers? on\b|\bTriggers include\b",
    re.I,
)

# Third-person action verbs. A pile of these BEFORE any trigger phrase means the
# description is describing the workflow rather than naming when to reach for it.
ACTION = re.compile(
    r"\b(imports?|renders?|scans?|generates?|transcribes?|parks?|grades?|analyses|analyzes|"
    r"runs?|fetches|builds?|creates?|picks?|spins?|re-briefs?|diagnoses|extracts?|converts?|"
    r"stops?|changes?|writes?|saves?|reports?|fixes|produces?|tailors?|sources?|scores?|"
    r"upserts?|enriches|ingests?|moves?|flips?|lists?|posts?|sends?|reads?|opens?|edits?|"
    r"updates?|deletes?|syncs?|triages?|summari[sz]es?|captures?|records?|renames?|merges?|"
    r"commits?|dispatches|launches|installs?|configures?|measures?|checks?|returns?|prints?|"
    r"emits?|handles?|processes|parses?|filters?|dedups?|ranks?|selects?|applies|wires?|"
    r"attaches|uploads?|downloads?)\b",
    re.I,
)

DEVICES = {
    "rationalization table": re.compile(r"\|\s*Excuse\s*\|", re.I),
    "red flags list": re.compile(r"^#+.*red flag", re.I | re.M),
    "iron law": re.compile(r"iron law", re.I),
    "announce at start": re.compile(r"announce", re.I),
    "common mistakes": re.compile(r"^#+.*common (mistake|rationaliz)", re.I | re.M),
    "quick reference": re.compile(r"^#+.*quick ref", re.I | re.M),
    "flowchart": re.compile(r"digraph\s"),
    "verification step": re.compile(r"\bverif(y|ies|ication)\b", re.I),
    "explicit skip/not-for": re.compile(r"\bSKIP\b|\bNOT for\b|\bNever for\b"),
}

DESC_SOFT_CAP = 400


def split_frontmatter(text):
    """Return (frontmatter, body) or (None, text) when there is no frontmatter."""
    if not text.startswith("---\n"):
        return None, text
    try:
        end = text.index("\n---\n", 3)
    except ValueError:
        return None, text
    return text[4 : end + 1], text[end + 5 :]


def read_description(frontmatter):
    """Handle both a single-line description and a YAML block scalar."""
    m = re.search(r"^description:[ \t]*(.*)$", frontmatter, re.M)
    if not m:
        return None
    first = m.group(1).strip()
    if first not in (">", "|", ">-", "|-", ""):
        return first.strip("\"'")
    rest = frontmatter[m.end() :].split("\n")
    lines = []
    for line in rest:
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            break
        lines.append(line.strip())
    return " ".join(lines) if lines else None


def scan(directory):
    directory = os.path.expanduser(directory)
    if not os.path.isdir(directory):
        raise SystemExit(f"not a directory: {directory}")

    skills, integrity, shape = [], [], []
    coverage = {k: 0 for k in DEVICES}

    for name in sorted(os.listdir(directory)):
        path = os.path.join(directory, name, "SKILL.md")
        if not os.path.isfile(path):
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        frontmatter, body = split_frontmatter(text)
        lines = text.count("\n") + 1
        skills.append(name)

        if frontmatter is None:
            integrity.append((name, "NO FRONTMATTER: cannot auto-trigger"))
            desc = None
        else:
            desc = read_description(frontmatter)
            if not re.search(r"^name:[ \t]*\S", frontmatter, re.M):
                integrity.append((name, "missing `name:`"))
            if re.search(r"^title:[ \t]*\S", frontmatter, re.M):
                integrity.append((name, "uses `title:`; the spec field is `name:`"))
            if re.search(r"^triggers:[ \t]*\S", frontmatter, re.M):
                integrity.append(
                    (name, "trigger phrases in a `triggers:` field the loader ignores")
                )
            if not desc:
                integrity.append((name, "missing or empty `description:`"))

        if desc:
            hit = TRIGGER.search(desc)
            preamble = desc[: hit.start()] if hit else desc
            verbs = len({v.lower() for v in ACTION.findall(preamble)})
            reasons = []
            if not hit:
                reasons.append("no trigger phrase")
            if verbs >= 3:
                reasons.append(f"{verbs} action verbs before any trigger")
            if len(desc) > DESC_SOFT_CAP:
                reasons.append(f"{len(desc)} chars, over the {DESC_SOFT_CAP} soft cap")
            if reasons:
                shape.append((name, reasons, desc))

        for key, pattern in DEVICES.items():
            if pattern.search(body):
                coverage[key] += 1

    return {
        "dir": directory,
        "count": len(skills),
        "integrity": integrity,
        "shape": shape,
        "coverage": coverage,
    }


def bar(n, total, width=28):
    filled = 0 if not total else round(width * n / total)
    return "#" * filled + "." * (width - filled)


def report(result, compare=None):
    print("=" * 74)
    print(f"CORPUS: {result['dir']}  ({result['count']} skills)")
    print("=" * 74)

    print(f"\nINTEGRITY  ({len(result['integrity'])} problems)")
    if not result["integrity"]:
        print("  all skills load with a name and a description")
    else:
        for name, why in result["integrity"]:
            print(f"  {name:34s} {why}")

    print(f"\nDESCRIPTION SHAPE  ({len(result['shape'])} suspect)")
    if not result["shape"]:
        print("  every description names its triggers")
    else:
        for name, reasons, _ in result["shape"]:
            print(f"  {name:34s} {', '.join(reasons)}")

    total = result["count"]
    print(f"\nDEVICE COVERAGE  (of {total} skills)")
    for key in sorted(result["coverage"], key=lambda k: -result["coverage"][k]):
        n = result["coverage"][key]
        line = f"  {key:24s} {n:4d}  {bar(n, total)}"
        if compare:
            m = compare["coverage"].get(key, 0)
            ct = compare["count"] or 1
            line += f"   | shared: {m:3d}/{compare['count']} ({100*m//ct:3d}%)"
        print(line)

    if compare:
        print("\n" + "=" * 74)
        print(f"SHARED SKILLSET: {compare['dir']}  ({compare['count']} skills)")
        print("=" * 74)
        print("\nDevices the shared set uses far more than yours (adopt candidates):")
        gaps = []
        for key in DEVICES:
            mine = result["coverage"][key] / (result["count"] or 1)
            theirs = compare["coverage"].get(key, 0) / (compare["count"] or 1)
            if theirs - mine > 0.25:
                gaps.append((theirs - mine, key, mine, theirs))
        if not gaps:
            print("  none above the 25-point threshold")
        for delta, key, mine, theirs in sorted(gaps, reverse=True):
            print(
                f"  {key:24s} yours {100*mine:3.0f}%  theirs {100*theirs:3.0f}%"
                f"   (+{100*delta:.0f} points)"
            )
        print("\nSkill names present in both (compare content, do not assume you lack it):")
        a = {n for n in os.listdir(result["dir"]) if os.path.isdir(os.path.join(result["dir"], n))}
        b = {n for n in os.listdir(compare["dir"]) if os.path.isdir(os.path.join(compare["dir"], n))}
        both = sorted(a & b)
        print("  " + (", ".join(both) if both else "no name overlap"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=DEFAULT_DIR, help="skills directory to audit")
    ap.add_argument("--compare", help="a shared skillset directory to compare against")
    ap.add_argument("--json", dest="json_out", help="also write machine-readable results")
    args = ap.parse_args()

    result = scan(args.dir)
    compare = scan(args.compare) if args.compare else None
    report(result, compare)

    if args.json_out:
        payload = {"corpus": result, "shared": compare}
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, default=list)
        print(f"\nwrote {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
