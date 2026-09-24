#!/bin/bash
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

# Exit silently for non-gemini commands
if ! echo "$CMD_SCAN" | grep -q '^gemini\b'; then
  exit 0
fi

# Allow safe flags: --version, --help, --list-extensions, --list-sessions
if echo "$CMD_SCAN" | grep -qE '^gemini\s+(--version|-v|--help|-h|--list-extensions|-l|--list-sessions)(\s|$)'; then
  exit 0
fi

# Allow read-only subcommands: mcp list, extensions list, skills list, gemma status, gemma logs
if echo "$CMD_SCAN" | grep -qE '^gemini\s+(mcp|extensions|skills)\s+list\b' \
  || echo "$CMD_SCAN" | grep -qE '^gemini\s+gemma\s+(status|logs)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gemini read-only operation"
    }
  }'
  exit 0
fi

# Gate yolo/auto-approve mode first (auto-approves all file writes and shell commands from Gemini)
if echo "$CMD_SCAN" | grep -qE '\s(-y|--yolo)\b' || echo "$CMD_SCAN" | grep -qE -e '--approval-mode\s+yolo\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "gemini yolo mode auto-approves all file writes and shell commands — confirm before proceeding"
    }
  }'
  exit 0
fi

# Gate --skip-trust (bypasses workspace trust confirmation)
if echo "$CMD_SCAN" | grep -qE '\s--skip-trust\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "gemini --skip-trust bypasses the workspace trust prompt — confirm before proceeding"
    }
  }'
  exit 0
fi

# Gate gemma write commands explicitly (setup downloads model, start/stop manage local server)
if echo "$CMD_SCAN" | grep -qE '^gemini\s+gemma\s+(setup|start|stop)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: "gemini gemma write operation (local model setup/server lifecycle) — confirm before proceeding"
    }
  }'
  exit 0
fi

# Allow headless prompt calls (no yolo flag): -p / --prompt
if echo "$CMD_SCAN" | grep -qE '(^|\s)-p\s|--prompt(\s|=)'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gemini headless prompt call"
    }
  }'
  exit 0
fi

# Gate all other operations (mcp add/remove, extensions install/uninstall, skills install, hooks migrate, etc.)
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: "gemini write operation — confirm before proceeding"
  }
}'
