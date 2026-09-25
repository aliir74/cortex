#!/bin/bash
# imsg CLI permission hook — Pattern A (read/write gating).
# Matches `imsg` on PATH or invoked by path.
# Read verbs (chats, history, search, etc.) pass through; send/mutate verbs ask.

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

# Only intercept imsg invocations.
# Matches `imsg` as the command being run (start of line or after a shell separator),
# with an optional path prefix. Does NOT match the literal word "imsg" used as
# an argument elsewhere.
if ! echo "$CMD_SCAN" | grep -qE '(^|&&|\|\||;|\|)[[:space:]]*[^[:space:];&|]*imsg([[:space:]]|$)'; then
  exit 0
fi

# Always safe: --help / -h anywhere, or --version
if echo "$CMD_SCAN" | grep -qE '(^|[[:space:]])(--help|-h|--version)([[:space:]]|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "imsg: help/version flag"}}'
  exit 0
fi

# Always safe: top-level status / completions subcommands
if echo "$CMD_SCAN" | grep -qE 'imsg[[:space:]]+(status|completions)([[:space:]]|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "imsg: status/completions"}}'
  exit 0
fi

# Read-only verbs: chats, history, stats, group, watch, rpc, scheduled, search,
# account, whois, nickname, name-photo, chat-background
if echo "$CMD_SCAN" | grep -qE 'imsg[[:space:]]+(chats|history|stats|group|watch|rpc|scheduled|search|account|whois|nickname|name-photo|chat-background)([[:space:]]|$)'; then
  jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "allow", permissionDecisionReason: "imsg read-only operation"}}'
  exit 0
fi

# Everything else (send, send-rich, send-multipart, send-attachment, send-sticker,
# poll, react, tapback, edit, unsend, delete-message, notify-anyways, chat-create,
# chat-name, chat-photo, chat-add-member, chat-remove-member, chat-leave, chat-delete,
# chat-mark, read, typing, launch, or anything unrecognised) is a write — ask.
jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "ask", permissionDecisionReason: "imsg write/modify operation — confirm recipient and content before proceeding"}}'
exit 0
