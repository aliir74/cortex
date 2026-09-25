#!/bin/bash
# Stripe permission hook.
# HARD-BLOCKS any live/production mode command (exit 2 — cannot be overridden).
# Read-only test-mode commands are auto-allowed.
# Write test-mode commands prompt for confirmation.

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

# Only intercept stripe invocations. Match only when `stripe` follows a real shell
# command boundary (start-of-command, ;, &, |) — NOT plain whitespace, which would
# false-trigger on the word "stripe" appearing inside quoted prompt/arg text.
if ! echo "$CMD_SCAN" | grep -qE '(^|[;&|])[[:space:]]*stripe([[:space:]]|$)'; then
  exit 0
fi

# ============================================================
# PRODUCTION SAFETY — HARD BLOCK (exit 2, no override)
# ============================================================

# Block --live flag
if echo "$CMD_SCAN" | grep -qE '(^|\s)--live(\s|$)'; then
  echo "BLOCKED: Stripe --live flag detected. Live/production mode is not permitted via Claude Code. Use the Stripe dashboard for live operations." >&2
  exit 2
fi

# Block live API keys via --api-key flag (matches both `--api-key X` and `--api-key=X`)
if echo "$CMD_SCAN" | grep -qE '\-\-api-key[[:space:]=]+(sk_live_|rk_live_|pk_live_)'; then
  echo "BLOCKED: Live Stripe API key (sk_live_/rk_live_/pk_live_) detected in command. Only test keys (sk_test_*, rk_test_*) are permitted." >&2
  exit 2
fi

# Block any live-key string anywhere in the command (catches inline env vars, scripts, etc.)
if echo "$CMD_SCAN" | grep -qE '(sk_live_|rk_live_|pk_live_)[A-Za-z0-9]'; then
  echo "BLOCKED: Live Stripe key prefix (sk_live_/rk_live_/pk_live_) detected in command string. Only test keys are permitted." >&2
  exit 2
fi

# Block if STRIPE_API_KEY env var is a live key
STRIPE_KEY="${STRIPE_API_KEY:-}"
if echo "$STRIPE_KEY" | grep -qE '^(sk_live_|rk_live_|pk_live_)'; then
  echo "BLOCKED: STRIPE_API_KEY env var is a live key. Unset it or set it to a test key before running Stripe CLI commands." >&2
  exit 2
fi

# ============================================================
# Allow safe / read-only commands (test mode confirmed)
# ============================================================

# Help, version, completion, whoami, --map (read-only — v1.41+)
if echo "$CMD_SCAN" | grep -qE 'stripe\s+(--help|-h|--version|-V|version|completion|whoami)\b' || \
   echo "$CMD_SCAN" | grep -qE '\s(--help|-h)\s*$' || \
   echo "$CMD_SCAN" | grep -qE 'stripe(\s+\S+)*\s+--map(=\S+)?(\s|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: help/version/whoami/--map (read-only, no API call)"}}'
  exit 0
fi

# Login / logout / config read
if echo "$CMD_SCAN" | grep -qE 'stripe\s+(login|logout)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: auth command"}}'
  exit 0
fi

if echo "$CMD_SCAN" | grep -qE 'stripe\s+config\s+--list\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: config list (read-only, test mode)"}}'
  exit 0
fi

# Generic GET (read-only by default, test mode). Note: `stripe get` is read; `stripe post`/`stripe delete` are explicit writes (added v1.41+) and intentionally NOT matched here.
if echo "$CMD_SCAN" | grep -qE 'stripe\s+get\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: get (read-only, test mode)"}}'
  exit 0
fi

# Logs tail
if echo "$CMD_SCAN" | grep -qE 'stripe\s+logs\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: logs (read-only, test mode)"}}'
  exit 0
fi

# Listen (webhook listener — read-only, test mode)
if echo "$CMD_SCAN" | grep -qE 'stripe\s+listen\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: listen (test mode webhook listener)"}}'
  exit 0
fi

# Resource discovery + docs (read-only, no API mutation; v1.41+)
if echo "$CMD_SCAN" | grep -qE 'stripe\s+(resources|docs|help)(\s|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: resources/docs/help (read-only discovery)"}}'
  exit 0
fi

# Resource read-only: list, retrieve, search (v1 — two-word path: `stripe <resource> <op>`)
if echo "$CMD_SCAN" | grep -qE 'stripe\s+\w+\s+(list|retrieve|search)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: read-only resource operation (test mode)"}}'
  exit 0
fi

# v2 resource read-only: list, retrieve (v2 — four-word path: `stripe v2 <namespace> <resource> <op>`, v1.41+)
if echo "$CMD_SCAN" | grep -qE 'stripe\s+v2\s+\w+\s+\w+\s+(list|retrieve)\b'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "Stripe: v2 read-only resource operation (test mode)"}}'
  exit 0
fi

# ============================================================
# Write / modify operations — ask (test mode, but confirm)
# Catches: create, update, delete, cancel, capture, confirm, pay,
# send_invoice, void_invoice, mark_uncollectible, finalize_invoice,
# trigger, fixtures, refunds create, reject, verify,
# activate/deactivate/reactivate/archive, expire, void_grant,
# close, enable, disable, ping (v2 core event_destinations),
# stripe post / stripe delete (raw HTTP write — v1.41+),
# stripe apps / projects / generate (plugin scaffolding — v1.41+).
# ============================================================
jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: "Stripe: write/modify operation in test mode — confirm before proceeding"}}'
exit 0
