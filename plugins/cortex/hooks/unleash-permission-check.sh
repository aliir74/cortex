#!/bin/bash
# Unleash CLI permission hook — Pattern A (read/write gating).
# Matches the cortex unleash-cli wrapper on PATH or invoked by (optionally quoted) path.
# Reads pass through; anything that can change flag state asks first.
#
# Why this is gated tightly: the configured instance is often production, so a
# toggle or rollout can be a live change affecting real users.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# grep is line-based; strip heredoc bodies so a payload line that documents a
# tool invocation is not read as a real one.
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$HOOK_DIR/lib/strip-heredocs.awk" ]; then
  CMD_SCAN=$(printf '%s\n' "$COMMAND" | awk -f "$HOOK_DIR/lib/strip-heredocs.awk")
else
  CMD_SCAN="$COMMAND"
fi

# Only intercept invocations of the unleash wrapper itself, not the word used as an
# argument elsewhere (e.g. `grep unleash file.txt`, `npm view unleash-client`).
if ! echo "$CMD_SCAN" | grep -qE '(^|&&|\|\||;|\|)[[:space:]]*[^[:space:];&|]*unleash["'"'"']?([[:space:]]|$)'; then
  exit 0
fi

# Drop a closing quote right after the binary name ("<path>/unleash-cli/unleash" flags list)
# so the verb patterns below see `unleash <verb>`.
CMD_SCAN=$(printf '%s\n' "$CMD_SCAN" | sed -E "s/unleash[\"']([[:space:]]|$)/unleash\1/g")

allow() {
  jq -n --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: $r}}'
  exit 0
}

ask() {
  jq -n --arg r "$1" '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: $r}}'
  exit 0
}

# Always safe: help / version flags anywhere in the command.
if echo "$CMD_SCAN" | grep -qE '(^|[[:space:]])(--help|-h|--version|-V)([[:space:]]|$)'; then
  allow "unleash: help/version"
fi

# The raw API escape hatch is judged by HTTP method, checked before the read verbs
# below so that `unleash api POST ...` cannot slip through.
if echo "$CMD_SCAN" | grep -qE 'unleash([[:space:]]+--?[a-zA-Z-]+([[:space:]]+[^[:space:]]+)?)*[[:space:]]+api([[:space:]]|$)'; then
  if echo "$CMD_SCAN" | grep -qiE '[[:space:]]api[[:space:]]+(GET|HEAD)([[:space:]]|$)'; then
    allow "unleash api read-only (GET/HEAD)"
  fi
  ask "unleash raw API call with a mutating method — confirm before proceeding"
fi

# Read-only verbs. Global flags (--profile, --base-url, --json) may appear before the
# subcommand, so allow an optional run of flags between `unleash` and the verb.
FLAGS='([[:space:]]+--?[a-zA-Z-]+([[:space:]]+[^[:space:]-][^[:space:]]*)?)*'
if echo "$CMD_SCAN" | grep -qE "unleash${FLAGS}[[:space:]]+(whoami|events)([[:space:]]|\$)"; then
  allow "unleash read-only (whoami/events)"
fi
if echo "$CMD_SCAN" | grep -qE "unleash${FLAGS}[[:space:]]+(projects|envs|strategies|flags)[[:space:]]+list([[:space:]]|\$)"; then
  allow "unleash read-only (list)"
fi
if echo "$CMD_SCAN" | grep -qE "unleash${FLAGS}[[:space:]]+flag[[:space:]]+(get|strategies)([[:space:]]|\$)"; then
  allow "unleash read-only (flag get/strategies)"
fi

# Everything else — flag create/toggle/rollout/archive, and anything unrecognised — is
# treated as a write against live Unleash.
ask "unleash write operation (flag create/toggle/rollout/archive) — this changes live feature flag state, confirm before proceeding"
