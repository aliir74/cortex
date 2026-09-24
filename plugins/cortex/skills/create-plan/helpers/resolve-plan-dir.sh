#!/usr/bin/env bash
# resolve-plan-dir.sh [preferences-file]
# Resolves where a plan file should be written, creates it, prints its absolute path.
# Priority:
#   1. $PLAN_DIR env var
#   2. `plans_dir:` value in the given preferences file (absolute, ~/..., or relative to the repo root / cwd)
#   3. <repo root>/docs/plans if that directory already exists
#   4. <repo root>/plans (or $PWD/plans outside a git repo)

set -euo pipefail

PREFS="${1:-}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
BASE="${ROOT:-$(pwd)}"

PREF_DIR=""
if [[ -n "$PREFS" && -f "$PREFS" ]]; then
  PREF_DIR="$(grep -m1 -E '^plans_dir:' "$PREFS" | sed -E 's/^plans_dir:[[:space:]]*//; s/[[:space:]]+$//' || true)"
fi

if [[ -n "${PLAN_DIR:-}" ]]; then
  DEST="$PLAN_DIR"
elif [[ -n "$PREF_DIR" ]]; then
  PREF_DIR="${PREF_DIR/#\~/$HOME}"
  if [[ "$PREF_DIR" == /* ]]; then
    DEST="$PREF_DIR"
  else
    DEST="$BASE/$PREF_DIR"
  fi
elif [[ -d "$BASE/docs/plans" ]]; then
  DEST="$BASE/docs/plans"
else
  DEST="$BASE/plans"
fi

mkdir -p "$DEST"
cd "$DEST" && pwd
