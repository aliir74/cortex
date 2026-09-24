#!/usr/bin/env python3
"""Density lint for a how-to-html .content.md file.

Run before rendering. Prints per-section word counts and flags
budget breaches. Exit 1 if anything is over budget.

  python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/check_density.py" <file>.content.md
"""
import re
import sys

TOTAL_BASE = 400            # whole-file floor, prose words
PER_FINDING = 60            # allowance per severity-tagged finding
SECTION_BUDGET = 180        # any one h2 section
BLOCK_BUDGET = 55           # any one paragraph
TWO_MIN_BUDGET = 120        # the two-minute version

BANNED_HEADINGS = (
    "introduction", "overview", "context", "background",
    "executive summary", "conclusion", "summary of findings",
    "closing thoughts", "final thoughts", "in summary", "recap",
    "limitations", "assumptions", "caveats", "next steps and considerations",
)

DIRECTIVE = re.compile(r"^\s*>\s*(chart|diagram|callout|compare|details)\s*:", re.I)


def words(text):
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def main(path):
    lines = open(path, encoding="utf-8").read().splitlines()

    # Strip YAML frontmatter: it is metadata for the renderer, not reader prose.
    # Counting it inflated the total and produced a spurious "(header)" block
    # warning on every content file.
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1:]
                break

    sections = []           # (heading, [lines])
    current = ("(header)", [])
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if not in_fence and re.match(r"^#{1,3}\s", line):
            sections.append(current)
            current = (re.sub(r"^#+\s*", "", line).strip(), [])
        else:
            current[1].append(line)
    sections.append(current)

    problems = []
    total = 0
    print(f"{'words':>6}  section")
    for heading, body in sections:
        # Keep blank lines: the block scan below needs them as paragraph
        # separators. Dropping them here made every multi-paragraph section
        # report as one oversized block.
        prose = [
            l for l in body
            if not l.strip()
            or (not l.strip().startswith(("|", "```", "<!--", "---"))
                and not DIRECTIVE.match(l))
        ]
        n = words("\n".join(prose))
        total += n
        print(f"{n:>6}  {heading}")

        low = heading.lower().strip(": ")
        if any(low == b or low.startswith(b) for b in BANNED_HEADINGS):
            problems.append(f"banned heading: '{heading}' (carries no information the rest of the file lacks)")
        if n > SECTION_BUDGET:
            problems.append(f"section over budget: '{heading}' {n}w > {SECTION_BUDGET}w")
        if "two-minute" in low and n > TWO_MIN_BUDGET:
            problems.append(f"two-minute version {n}w > {TWO_MIN_BUDGET}w")

        # block-level check: a bullet/numbered item is its own block, as is a
        # run of plain lines between blank lines.
        para = []
        def flush(para):
            if not para:
                return
            pn = words(" ".join(para))
            if pn > BLOCK_BUDGET:
                snippet = " ".join(para)[:60]
                problems.append(
                    f"block {pn}w > {BLOCK_BUDGET}w under '{heading}': {snippet}...")
        for l in prose + [""]:
            if re.match(r"^\s*([-*+]|\d+[.)])\s", l):
                flush(para)
                para = [l]
            elif l.strip():
                para.append(l)
            else:
                flush(para)
                para = []

    findings = len(re.findall(r"\[(blocking|important|note)\]", "\n".join(lines), re.I))
    budget = TOTAL_BASE + PER_FINDING * findings
    print(f"\n{total:>6}  TOTAL (budget {budget} = {TOTAL_BASE} + {PER_FINDING} x {findings} findings)")
    if total > budget:
        problems.append(f"file over budget: {total}w > {budget}w — cut, do not reword")

    if problems:
        print("\nOVER BUDGET:")
        for p in problems:
            print(f"  - {p}")
        print("\nCut sections and sentences. Do not shorten by rewording; delete whole blocks.")
        return 1
    print("\nwithin budget")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
