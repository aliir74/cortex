#!/usr/bin/env bash
# archive-plan.sh <plan-path>
# Flips Status to `done` and moves the plan to <parent>/done/. Prints new absolute path.

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

# Flip Status line
python3 - "$PLAN" <<'PY'
import sys, pathlib, re
p = pathlib.Path(sys.argv[1])
text = p.read_text()
new = re.sub(
    r"^\*\*Status:\*\*\s*(planning|in_progress)\b",
    "**Status:** done",
    text,
    count=1,
    flags=re.MULTILINE,
)
p.write_text(new)
PY

PARENT="$(dirname "$PLAN")"
DONE_DIR="$PARENT/done"
mkdir -p "$DONE_DIR"

BASE="$(basename "$PLAN")"
DEST="$DONE_DIR/$BASE"
mv "$PLAN" "$DEST"

# absolute path
cd "$DONE_DIR"
echo "$(pwd)/$BASE"
