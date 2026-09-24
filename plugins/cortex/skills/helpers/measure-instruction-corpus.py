#!/usr/bin/env python3
"""Measure the always-loaded Claude Code instruction corpus.

Reports three things: file sizes for every instruction file, the skill-listing
character aggregate (an always-paid item), and violations of the documented caps.
Stdlib only.

Caps this checks against:
  CLAUDE.md   under 200 lines   (code.claude.com/docs/en/memory)
  SKILL.md    under 500 lines   (code.claude.com/docs/en/skills)
  listing     per-entry 1536 chars (name + description + when_to_use)

What it reads:
  ~/.claude/CLAUDE.md, plus any file it @-imports from ~/.claude/
  ~/.claude/rules/*.md (reported, not counted as always-loaded)
  every CLAUDE.md under --project-root (default: the current directory);
    the root one counts as always-loaded, subfolder ones load on demand
  every SKILL.md under each --skills-dir (default: ~/.claude/skills)

Usage:
  measure-instruction-corpus.py                       human-readable tables
  measure-instruction-corpus.py --json                machine-diffable snapshot
  measure-instruction-corpus.py --skills-dir DIR ...  measure other skill dirs (repeatable)
  measure-instruction-corpus.py --project-root DIR    walk a different project

Token estimates are ESTIMATES. Dense instruction prose with backticks, paths and
table pipes tokenises far worse than ordinary English: about 2.5 chars/token for
instruction files and about 2.7 for description prose, versus the naive 4.
Always prefer the /context readings when you have them.
"""

import argparse
import json
import os
import re
import sys

CHARS_PER_TOKEN_MEMORY = 2.5
CHARS_PER_TOKEN_LISTING = 2.7

HOME = os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")

CLAUDE_MD_LINE_CAP = 200
SKILL_LINE_CAP = 500
LISTING_ENTRY_CAP = 1536

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".trash", ".venv", "venv", "dist", "build"}


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def stats(path):
    body = read(path)
    if body is None:
        return None
    return {
        "path": path,
        "bytes": len(body.encode("utf-8")),
        "lines": body.count("\n") + 1 if body else 0,
        "words": len(body.split()),
    }


def frontmatter_field(body, field):
    """Return a top-level single-line frontmatter scalar, or None."""
    if not body.startswith("---"):
        return None
    end = body.find("\n---", 3)
    if end == -1:
        return None
    for line in body[3:end].splitlines():
        if line.startswith(field + ":"):
            return line[len(field) + 1:].strip()
    return None


def walk(root, name):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if name in filenames:
            yield os.path.join(dirpath, name)


def imports(path):
    """@-imports in a CLAUDE.md that resolve to existing files."""
    body = read(path) or ""
    base = os.path.dirname(path)
    out = []
    for m in re.finditer(r"(?m)^\s*@(\S+)\s*$", body):
        target = os.path.expanduser(m.group(1))
        if not os.path.isabs(target):
            target = os.path.join(base, target)
        if os.path.isfile(target):
            out.append(target)
    return out


def collect(skills_dirs, project_root):
    out = {"global": [], "user_rules": [], "project_claude_md": [], "skills": []}

    user_md = os.path.join(CLAUDE, "CLAUDE.md")
    if os.path.isfile(user_md):
        for p in [user_md] + imports(user_md):
            s = stats(p)
            if s:
                out["global"].append(s)

    rules = os.path.join(CLAUDE, "rules")
    if os.path.isdir(rules):
        for f in sorted(os.listdir(rules)):
            if f.endswith(".md"):
                s = stats(os.path.join(rules, f))
                if s:
                    s["paths_scoped"] = frontmatter_field(read(s["path"]), "paths") is not None
                    out["user_rules"].append(s)

    if project_root and os.path.isdir(project_root) and os.path.realpath(project_root) != os.path.realpath(HOME):
        for p in sorted(walk(project_root, "CLAUDE.md")):
            s = stats(p)
            if not s:
                continue
            s["is_root"] = os.path.dirname(os.path.realpath(p)) == os.path.realpath(project_root)
            out["project_claude_md"].append(s)

    seen = set()
    for root in skills_dirs:
        if not os.path.isdir(root):
            continue
        for p in sorted(walk(root, "SKILL.md")):
            rp = os.path.realpath(p)
            if rp in seen:
                continue
            seen.add(rp)
            body = read(p)
            if body is None:
                continue
            name = os.path.basename(os.path.dirname(p))
            desc = frontmatter_field(body, "description") or ""
            when = frontmatter_field(body, "when_to_use") or ""
            refs = 0
            for dp, dn, fn in os.walk(os.path.dirname(p)):
                dn[:] = [d for d in dn if d not in SKIP_DIRS]
                refs += sum(1 for f in fn if f.endswith((".md", ".txt")) and f != "SKILL.md")
            out["skills"].append({
                "name": name,
                "path": p,
                "bytes": len(body.encode("utf-8")),
                "lines": body.count("\n") + 1,
                "desc_chars": len(desc),
                "when_chars": len(when),
                "listing_chars": len(name) + len(desc) + len(when),
                "reference_files": refs,
            })
    return out


def violations(data):
    v = []
    for s in data["global"] + data["project_claude_md"]:
        if s["lines"] > CLAUDE_MD_LINE_CAP:
            v.append(("claude_md_over_200", s["path"], s["lines"]))
    for s in data["skills"]:
        if s["lines"] > SKILL_LINE_CAP:
            v.append(("skill_over_500", s["path"], s["lines"]))
        if s["listing_chars"] > LISTING_ENTRY_CAP:
            v.append(("listing_entry_over_1536", s["name"], s["listing_chars"]))
    for s in data["user_rules"]:
        if not s["paths_scoped"]:
            v.append(("rule_not_path_scoped", s["path"], None))
    return v


def totals(data):
    always = sum(s["bytes"] for s in data["global"])
    always += sum(s["bytes"] for s in data["project_claude_md"] if s.get("is_root"))
    listing = sum(s["listing_chars"] for s in data["skills"])
    return {
        "always_loaded_bytes": always,
        "always_loaded_est_tokens": int(always / CHARS_PER_TOKEN_MEMORY),
        "skill_listing_chars": listing,
        "skill_listing_est_tokens": int(listing / CHARS_PER_TOKEN_LISTING),
        "skill_count": len(data["skills"]),
        "skills_with_reference_files": sum(1 for s in data["skills"] if s["reference_files"]),
        "combined_est_tokens": int(always / CHARS_PER_TOKEN_MEMORY)
                              + int(listing / CHARS_PER_TOKEN_LISTING),
    }


def short(path):
    return path.replace(HOME, "~", 1) if isinstance(path, str) else path


def human(data):
    t = totals(data)
    print("=" * 74)
    print("ALWAYS-LOADED BASELINE")
    print("=" * 74)
    for s in data["global"]:
        print(f"  {s['bytes']:>7}b {s['lines']:>4}L  {short(s['path'])}")
    for s in data["project_claude_md"]:
        if s.get("is_root"):
            print(f"  {s['bytes']:>7}b {s['lines']:>4}L  {short(s['path'])}  (project root)")
    print(f"\n  always-loaded files : {t['always_loaded_bytes']:>7} bytes "
          f"(~{t['always_loaded_est_tokens']:,} tok)")
    print(f"  skill listing (RAW) : {t['skill_listing_chars']:>7} chars "
          f"(~{t['skill_listing_est_tokens']:,} tok) across {t['skill_count']} skills")
    print(f"  COMBINED            : ~{t['combined_est_tokens']:,} tokens per session (estimate)")
    print("  NOTE: the listing figure is RAW: skillOverrides are NOT applied and only the")
    print("        --skills-dir directories are counted. /context is authoritative.")
    print(f"  skills w/ reference files: {t['skills_with_reference_files']}/{t['skill_count']}")

    on_demand = [s for s in data["project_claude_md"] if not s.get("is_root")]
    if on_demand or data["user_rules"]:
        print("\n" + "=" * 74)
        print("ON-DEMAND INSTRUCTION FILES")
        print("=" * 74)
        for s in on_demand + data["user_rules"]:
            print(f"  {s['bytes']:>7}b {s['lines']:>4}L  {short(s['path'])}")

    print("\n" + "=" * 74)
    print("20 LONGEST SKILL LISTING ENTRIES")
    print("=" * 74)
    top = sorted(data["skills"], key=lambda s: -s["listing_chars"])[:20]
    run = 0
    for s in top:
        run += s["listing_chars"]
        print(f"  {s['listing_chars']:>5}ch  (cum {run:>6})  {s['name']}")

    print("\n" + "=" * 74)
    print("VIOLATIONS")
    print("=" * 74)
    vs = violations(data)
    if not vs:
        print("  none")
    else:
        for kind, where, num in vs:
            print(f"  {kind:<26} {num if num is not None else '':>5}  {short(where)}")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--json", action="store_true", help="print a machine-readable snapshot")
    ap.add_argument("--skills-dir", action="append", default=None,
                    help="skills directory to measure (repeatable; default ~/.claude/skills)")
    ap.add_argument("--project-root", default=os.getcwd(),
                    help="project whose CLAUDE.md files to measure (default: cwd)")
    args = ap.parse_args()

    skills_dirs = [os.path.expanduser(d) for d in (args.skills_dir or [os.path.join(CLAUDE, "skills")])]
    data = collect(skills_dirs, os.path.expanduser(args.project_root))
    if args.json:
        json.dump({"totals": totals(data),
                   "violations": [list(v) for v in violations(data)],
                   "data": data},
                  sys.stdout, indent=2)
        print()
    else:
        human(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
