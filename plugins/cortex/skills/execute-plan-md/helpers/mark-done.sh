#!/usr/bin/env bash
# mark-done.sh <plan-path> "<unique-substring>"
# Flips the matching `- [ ]` line to `- [x]`. Errors on 0 or multiple matches.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <plan-path> <unique-substring>" >&2
  exit 2
fi

PLAN="$1"
NEEDLE="$2"

python3 - "$PLAN" "$NEEDLE" <<'PY'
import sys, pathlib, re

plan_path = pathlib.Path(sys.argv[1])
needle = sys.argv[2]
text = plan_path.read_text()
lines = text.split("\n")

needle_norm = needle.replace("`", "")
matches = [i for i, l in enumerate(lines)
           if re.match(r"^\s*-\s\[\s\]", l) and needle_norm in l.replace("`", "")]

if not matches:
    print(f"error: no unchecked step matches {needle!r}", file=sys.stderr)
    sys.exit(1)
if len(matches) > 1:
    print(f"error: {len(matches)} unchecked steps match {needle!r}; be more specific", file=sys.stderr)
    for i in matches:
        print(f"  line {i+1}: {lines[i]}", file=sys.stderr)
    sys.exit(1)

i = matches[0]
lines[i] = lines[i].replace("- [ ]", "- [x]", 1)
plan_path.write_text("\n".join(lines))
print(f"marked: {lines[i].strip()}")
PY
