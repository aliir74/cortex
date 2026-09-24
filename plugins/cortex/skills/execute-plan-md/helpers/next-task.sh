#!/usr/bin/env bash
# next-task.sh <plan-path>
# Prints the next unchecked step with its enclosing task heading and Files block.
# Exit 0 if a step was printed, exit 1 if plan has no unchecked steps (complete).

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <plan-path>" >&2
  exit 2
fi

PLAN="$1"
if [[ ! -f "$PLAN" ]]; then
  echo "error: plan not found: $PLAN" >&2
  exit 2
fi

python3 - "$PLAN" <<'PY'
import sys, re, pathlib

plan = pathlib.Path(sys.argv[1]).read_text()
lines = plan.split("\n")

task_heading = None
files_block = []
in_files = False

for i, line in enumerate(lines):
    h = re.match(r"^###\s+Task\s+", line)
    if h:
        task_heading = line.strip()
        files_block = []
        in_files = False
        continue
    if line.strip().startswith("**Files:**"):
        in_files = True
        files_block = [line.rstrip()]
        continue
    if in_files:
        if line.startswith("- ") and not re.match(r"^\s*-\s\[", line):
            files_block.append(line.rstrip())
        else:
            in_files = False
    if re.match(r"^\s*-\s\[\s\]", line):
        print("TASK:", task_heading or "(unknown)")
        print("FILES:")
        for f in files_block:
            print(" ", f)
        print("STEP:", line.strip())
        sys.exit(0)

# no unchecked
sys.exit(1)
PY
