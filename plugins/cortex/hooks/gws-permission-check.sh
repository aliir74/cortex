#!/bin/bash
# Dynamic gws permission hook.
# Auto-allows read-only Gmail and Calendar commands, asks for modifications.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Only intercept gws commands (with or without account prefix)
if ! echo "$COMMAND" | grep -qE '(^gws\b|^GOOGLE_WORKSPACE_CLI_ACCOUNT=\S+\s+gws\b)'; then
  exit 0
fi

# Allow auth and help commands
if echo "$COMMAND" | grep -qE 'gws\s+(auth|--help|--version|schema)\b' || echo "$COMMAND" | grep -qE '\s--help(\s|$)'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws auth/help command"
    }
  }'
  exit 0
fi

# Gmail read-only helpers
if echo "$COMMAND" | grep -qE 'gws\s+gmail\s+\+(triage|watch)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws gmail read-only helper"
    }
  }'
  exit 0
fi

# Gmail read-only: list, get
if echo "$COMMAND" | grep -qE 'gws\s+gmail\s+(users\s+)?(messages|threads|labels|drafts|history)\s+(list|get)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws gmail read-only operation"
    }
  }'
  exit 0
fi

# Gmail profile
if echo "$COMMAND" | grep -qE 'gws\s+gmail\s+(users\s+)?getProfile\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws gmail read-only operation"
    }
  }'
  exit 0
fi

# Calendar read-only helper
if echo "$COMMAND" | grep -qE 'gws\s+calendar\s+\+agenda\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws calendar read-only helper"
    }
  }'
  exit 0
fi

# Calendar read-only: list, get
if echo "$COMMAND" | grep -qE 'gws\s+calendar\s+(events|calendarList|calendars)\s+(list|get|instances)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws calendar read-only operation"
    }
  }'
  exit 0
fi

# Drive read-only
if echo "$COMMAND" | grep -qE 'gws\s+drive\s+(files|permissions|revisions|comments|replies|drives|about|changes)\s+(list|get|export|watch|copy)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "gws drive read-only operation"
    }
  }'
  exit 0
fi

# Gmail archive (batchModify removing labels only)
if echo "$COMMAND" | grep -qE 'gws\s+gmail\s+(users\s+)?messages\s+batchModify\b'; then
  if echo "$COMMAND" | grep -q 'removeLabelIds' && ! echo "$COMMAND" | grep -q 'addLabelIds'; then
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        permissionDecisionReason: "gws gmail archive (remove labels only)"
      }
    }'
    exit 0
  fi
fi

# Everything else — ask
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: "gws write/modify operation — confirm before proceeding"
  }
}'
