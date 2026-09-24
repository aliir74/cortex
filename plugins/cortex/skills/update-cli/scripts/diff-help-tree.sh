#!/usr/bin/env bash
# Capture a CLI's help tree (top-level + one level deep) into a single file.
# Strips common upgrade banners ("Update available: x → y") so diffs stay clean.
#
# Usage: diff-help-tree.sh <binary> <output-file>
# Example: diff-help-tree.sh gh /tmp/before-tree.txt
#
# Run twice (before/after upgrade), then:
#   diff /tmp/before-tree.txt /tmp/after-tree.txt
# to see new/removed commands and flag changes.

set -euo pipefail

BINARY="${1:?binary name required}"
OUTPUT="${2:?output file required}"

if ! command -v "$BINARY" >/dev/null 2>&1; then
  echo "ERROR: $BINARY not on PATH" >&2
  exit 1
fi

strip_banner() {
  grep -v '^Update available' | grep -v '^npm notice' | grep -v '^bun notice'
}

{
  echo "=== $BINARY --version ==="
  "$BINARY" --version 2>&1 | strip_banner || true
  echo
  echo "=== $BINARY --help ==="
  "$BINARY" --help 2>&1 | strip_banner

  # Extract top-level subcommands from the Commands: section.
  # Heuristic: lines starting with two spaces + a word, after the "Commands:" line.
  SUBCMDS=$("$BINARY" --help 2>&1 | strip_banner | awk '
    /^Commands:/ { in_cmds=1; next }
    in_cmds && /^[A-Z]/ { in_cmds=0 }
    in_cmds && /^  [a-z]/ { print $1 }
  ' | sort -u)

  for sub in $SUBCMDS; do
    # Skip non-command words (help, version, etc. handled separately).
    [[ "$sub" == "help" || "$sub" == "version" ]] && continue
    echo
    echo "=== $BINARY $sub --help ==="
    "$BINARY" "$sub" --help 2>&1 | strip_banner || echo "(failed to fetch help for $sub)"
  done
} > "$OUTPUT"

echo "wrote $OUTPUT" >&2
