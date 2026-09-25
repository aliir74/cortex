#!/bin/bash
# Gates Notion `ntn` CLI write operations. Read-only ops pass through; writes require confirmation.

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

# Only intercept ntn invocations (handle shell separators: space, ;, |, &, &&, etc.)
if ! echo "$CMD_SCAN" | grep -qE '(^|[[:space:]]|;|\||&)ntn([[:space:]]|$)'; then
  exit 0
fi

# ============================================================
# Always-safe metadata / health
# ============================================================
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+(--help|-h|--version|-V|help|doctor|completions|whoami)\b' || \
   echo "$CMD_SCAN" | grep -qE '\s(--help|-h)\s*$'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn: help/version/doctor"}}'
  exit 0
fi

# ============================================================
# Read-only subcommands
# ============================================================

# ntn api ls / --spec / --docs (introspection, no API mutation)
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+api[[:space:]]+ls\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn api ls (introspection)"}}'
  exit 0
fi
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+api[[:space:]].*(--spec|--docs)(\s|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn api --spec/--docs (introspection, no API call)"}}'
  exit 0
fi

# ntn api — POST-but-read endpoints (Notion API design uses POST for these reads).
#   v1/search and v1/databases/<id>/query both require POST + body but are read-only.
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+api[[:space:]]+v1/(search|databases/[^[:space:]/]+/query)(\s|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn api v1/search or db query (POST-but-read)"}}'
  exit 0
fi

# ntn api <path> — allow only when it looks like a pure GET:
#   no -d/--data, no --file, no -X with mutating method, no inline body field (key=value or key:=value).
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+api(\s|$)'; then
  if echo "$CMD_SCAN" | grep -qE '(\s|^)(-d|--data|--file)(\s|=)'; then
    : # body present → write
  elif echo "$CMD_SCAN" | grep -qE '\-X[[:space:]]+(POST|PATCH|PUT|DELETE)\b'; then
    : # explicit mutation method → write
  elif echo "$CMD_SCAN" | grep -qE '[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?:?=[^=[:space:]]'; then
    : # inline body field key=value or key:=value → write (excludes query params key==value)
  else
    jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn api (GET-style, no body)"}}'
    exit 0
  fi
fi

# ntn datasources query/resolve — read
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+datasources[[:space:]]+(query|resolve)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn datasources (read-only)"}}'
  exit 0
fi

# ntn pages get — read
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+pages[[:space:]]+get\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn pages get (read-only)"}}'
  exit 0
fi

# ntn files get/list — read
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+files[[:space:]]+(get|list)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn files (read-only)"}}'
  exit 0
fi

# ntn workers read-only verbs
if echo "$CMD_SCAN" | grep -qE 'ntn[[:space:]]+workers[[:space:]]+(list|ls|get|capabilities|usage)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "ntn workers (read-only)"}}'
  exit 0
fi

# ============================================================
# Write / modify operations — ask
# Also intentionally catches `ntn auth token` (prints the live auth token —
# a secret exposure, not a mutation, but still not auto-allowed) and every
# `ntn notion-as-code *` subcommand (alpha; several mutate workspace state).
# ============================================================
jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: "ntn: write/modify operation — confirm before proceeding"}}'
exit 0
