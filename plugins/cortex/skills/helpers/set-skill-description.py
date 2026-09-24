#!/usr/bin/env python3
"""Replace a skill's frontmatter `description` in place.

Rewriting these by hand is error-prone: the value is a single YAML line that
often contains colons, backticks, quotes and slashes, so a careless edit breaks
the frontmatter and Claude Code then loads the skill with empty metadata (the
skill still works via /name but stops auto-triggering).

Handles both forms:
  description: one line of text
  description: >
    a YAML block scalar continued
    across indented lines

For a block scalar the replaced span covers the whole logical value, so the
indented continuation lines cannot be orphaned, and the post-write check compares
the re-parsed value against the input.

The skill can be given as a name (looked up under --skills-dir, default
~/.claude/skills), a skill directory, or a path to its SKILL.md.

Usage:
  set-skill-description.py [--skills-dir DIR] <skill> <new-description>
  set-skill-description.py [--skills-dir DIR] --report <skill>
  set-skill-description.py --self-test

Writes only if the frontmatter parses before and after. Prints old/new lengths.
Stdlib only.
"""

import os
import sys

DEFAULT_SKILLS = os.path.expanduser("~/.claude/skills")

# A `description:` whose remainder is one of these has its value on the FOLLOWING
# indented lines, not on the header line.
BLOCK_INDICATORS = (">", "|", ">-", "|-", ">+", "|+", "")


def resolve(skill, skills_dir):
    cand = os.path.expanduser(skill)
    if os.path.isfile(cand):
        return cand
    if os.path.isdir(cand) and os.path.isfile(os.path.join(cand, "SKILL.md")):
        return os.path.join(cand, "SKILL.md")
    p = os.path.join(skills_dir, skill, "SKILL.md")
    if os.path.isfile(p):
        return p
    raise SystemExit(f"no SKILL.md for {skill!r} (looked in {skills_dir})")


def load(skill, skills_dir):
    p = resolve(skill, skills_dir)
    return p, open(p, encoding="utf-8").read()


def bounds(body):
    if not body.startswith("---"):
        raise SystemExit("file does not start with frontmatter")
    end = body.find("\n---", 3)
    if end == -1:
        raise SystemExit("unterminated frontmatter")
    return 3, end


def find_desc(body):
    """Return (start, end, value) spanning the whole description, or None.

    `end` is exclusive of the trailing newline. For a block scalar the span covers
    the `description:` line AND every indented continuation line, so a replacement
    cannot orphan them.
    """
    s, e = bounds(body)
    lines = body[s:e].splitlines(keepends=True)
    off = s
    for i, line in enumerate(lines):
        if not line.startswith("description:"):
            off += len(line)
            continue

        head = line[len("description:") :].strip()
        start = off
        end = off + len(line.rstrip("\n"))

        if head not in BLOCK_INDICATORS:
            return start, end, head.strip("\"'")

        parts = []
        cursor = off + len(line)
        for cont in lines[i + 1 :]:
            if cont.strip() and not cont.startswith((" ", "\t")):
                break
            if cont.strip():
                parts.append(cont.strip())
            cursor += len(cont)
            end = cursor - (1 if cont.endswith("\n") else 0)
        return start, end, " ".join(parts)

    return None


def replace(body, new):
    """Return the rewritten body, or raise SystemExit with the reason."""
    found = find_desc(body)
    if not found:
        raise SystemExit("no description field to replace")
    start, end, old = found

    out = body[:start] + "description: " + new + body[end:]

    bounds(out)
    check = find_desc(out)
    if check is None:
        raise SystemExit("replacement broke the frontmatter, aborted")
    if check[2] != new:
        raise SystemExit(
            "post-write value does not match input "
            "(likely orphaned continuation lines), aborted"
        )
    return out, old


SELF_TEST_CASES = [
    (
        "single line",
        "---\nname: x\ndescription: old text here\n---\n\n# Body\n",
        "old text here",
    ),
    (
        "block scalar",
        "---\ntitle: x\ndescription: >\n  first part of the value\n  second part of it\n---\n\n# Body\n",
        "first part of the value second part of it",
    ),
    (
        "block scalar with trailing key",
        "---\ndescription: |\n  only line\nname: x\n---\n\n# Body\n",
        "only line",
    ),
    (
        "quoted single line",
        '---\nname: x\ndescription: "quoted value"\n---\n\n# Body\n',
        "quoted value",
    ),
]


def self_test():
    failures = 0
    for label, body, expected in SELF_TEST_CASES:
        found = find_desc(body)
        got = found[2] if found else None
        if got != expected:
            print(f"  FAIL parse [{label}]: {got!r} != {expected!r}")
            failures += 1
            continue

        out, _ = replace(body, "NEW VALUE")
        reparsed = find_desc(out)[2]
        if reparsed != "NEW VALUE":
            print(f"  FAIL write [{label}]: re-parsed {reparsed!r}")
            failures += 1
            continue
        # No orphaned continuation lines may survive between the new value and
        # the next key or the closing fence.
        orphan = [
            ln
            for ln in out.split("\n---", 1)[0].splitlines()
            if ln.startswith((" ", "\t")) and ln.strip()
        ]
        if orphan:
            print(f"  FAIL orphan [{label}]: {orphan}")
            failures += 1
            continue
        print(f"  ok  {label}")

    print("self-test:", "all passed" if not failures else f"{failures} failed")
    return 1 if failures else 0


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    skills_dir = DEFAULT_SKILLS
    if argv[0] == "--skills-dir":
        if len(argv) < 2:
            raise SystemExit("--skills-dir needs a value")
        skills_dir = os.path.expanduser(argv[1])
        argv = argv[2:]

    if argv and argv[0] == "--self-test":
        return self_test()

    if len(argv) >= 2 and argv[0] == "--report":
        _, body = load(argv[1], skills_dir)
        found = find_desc(body)
        print(len(found[2]) if found else 0)
        return 0

    if len(argv) < 2:
        raise SystemExit(__doc__)

    skill, new = argv[0], argv[1]
    if "\n" in new:
        raise SystemExit("description must be a single line")

    p, body = load(skill, skills_dir)
    try:
        out, old = replace(body, new)
    except SystemExit as exc:
        raise SystemExit(f"{skill}: {exc}")

    open(p, "w", encoding="utf-8").write(out)
    print(f"{skill}: {len(old)} -> {len(new)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
