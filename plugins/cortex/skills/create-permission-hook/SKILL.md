---
name: create-permission-hook
description: Use when creating a dynamic permission hook for a CLI tool to gate dangerous commands, separate read-only from write operations, or protect production environments. Triggers on "create hook", "permission hook", "gate production", "protect CLI"
---

# Create Permission Hook

Dynamic PreToolUse hooks that intercept Bash commands and return allow/ask/deny decisions based on command analysis or runtime state.

## When to Use

**Pattern A — Read/Write Gating:** The CLI sends messages, modifies external state, or has destructive commands. Gate writes, allow reads.
- Examples: Slack CLI, Google Workspace CLI, ClickUp CLI

**Pattern B — Context-Based Gating:** The CLI has environment/auth contexts where the same command is safe in dev but dangerous in production.
- Examples: kubectl (k8s context), doctl (auth context)

## Workflow

### 1. Explore the CLI

Run `<tool> --help` and recurse into each subcommand group. Build a command taxonomy:

| Category | Description | Examples |
|----------|-------------|---------|
| **Always safe** | Auth, help, version, config reads | `auth`, `--help`, `version` |
| **Read-only** | List, get, show, describe, logs | `list`, `get`, `show`, `logs`, `status` |
| **Modify** | Create, delete, update, send, deploy | `create`, `delete`, `update`, `send` |

**Use a whitelist approach** for read-only verbs. Unknown verbs default to "modify" so new commands added in future CLI versions are caught.

### 2. Write the Hook Script

Both patterns share this skeleton:

```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Exit silently for non-matching commands (CRITICAL — prevents hijacking other tools' permissions)
if ! echo "$COMMAND" | grep -q '^TOOL_NAME\b'; then
  exit 0
fi

# Whitelist safe commands...

# Gate everything else...
```

**Decision JSON format:**
```bash
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "allow",  # or "ask" or "deny"
    permissionDecisionReason: "Human-readable reason"
  }
}'
```

**Pattern A template** (read/write gating):
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Exit silently for non-matching commands
if ! echo "$COMMAND" | grep -q '^TOOL\b'; then
  exit 0
fi

# Allow help/auth
if echo "$COMMAND" | grep -qE 'TOOL\s+(auth|--help|version)\b'; then
  exit 0  # Fall through to other permission rules
fi

# Allow read-only subcommands
if echo "$COMMAND" | grep -qE 'TOOL\s+RESOURCE\s+(list|get|show)\b'; then
  jq -n '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: "TOOL read-only operation"
    }
  }'
  exit 0
fi

# Everything else — ask
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: "TOOL write operation — confirm before proceeding"
  }
}'
```

**Pattern B template** (context-based gating):
```bash
#!/bin/bash
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')

# Exit silently for non-matching commands
if ! echo "$COMMAND" | grep -q '^TOOL\b'; then
  exit 0
fi

# Always allow safe top-level commands
if echo "$COMMAND" | grep -qE '^TOOL\s+(auth|version|help)\b'; then
  exit 0
fi

# Always allow read-only verbs (whitelist — unknown verbs get gated)
if echo "$COMMAND" | grep -qE '\b(list|get|show|logs|status|describe)\b'; then
  exit 0
fi

# Check for explicit context flag override
if echo "$COMMAND" | grep -qE -- '--context\s+\S*production'; then
  CONTEXT="production (explicit flag)"
  IS_PROD=true
else
  CONTEXT=$(TOOL_SPECIFIC_CONTEXT_COMMAND)
  IS_PROD=$(echo "$CONTEXT" | grep -qi 'production' && echo true || echo false)
fi

if [ "$IS_PROD" = true ]; then
  jq -n --arg ctx "$CONTEXT" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "ask",
      permissionDecisionReason: ("PRODUCTION context: " + $ctx + " — confirm before modify")
    }
  }'
else
  jq -n --arg ctx "$CONTEXT" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "allow",
      permissionDecisionReason: ("Non-production context: " + $ctx)
    }
  }'
fi
```

Make executable: `chmod +x <hook-script>.sh`

### 3. Register in Settings

All registration points must be updated or permissions become inconsistent:

**a) TOML allow rule** (`~/.config/claude-permissions.toml`):
```toml
# --- Tool Name (hook gates dynamically) ---
[[allow]]
tool = "Bash"
command_regex = "^TOOL\\s+"
command_exclude_regex = "&&|;|`|\\$\\("
```

**b) Hook in settings** (`~/.claude/settings.json` -> `hooks.PreToolUse[]`):
```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "bash /path/to/hooks/tool-hook.sh"
  }]
}
```

For plugin-based hooks, register in the plugin's `hooks.json` instead:
```json
{
  "hooks": [
    {
      "type": "PreToolUse",
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "bash hooks/tool-hook.sh"
      }]
    }
  ]
}
```

### 4. Validate

```bash
# Validate TOML
python3 -c "import tomllib; tomllib.load(open('~/.config/claude-permissions.toml'.replace('~', __import__('os').path.expanduser('~')), 'rb')); print('TOML valid')"

# Validate JSON
python3 -c "import json; json.load(open('~/.claude/settings.json'.replace('~', __import__('os').path.expanduser('~')))); print('JSON valid')"
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not exiting silently for non-matching commands | A hook that returns a decision for all Bash commands overrides every other permission rule |
| Missing `INPUT=$(cat)` | Without consuming stdin the hook hangs |
| Forgetting registration files | TOML allows the command through but hook isn't registered, or hook is registered but TOML blocks it |
| Not checking for inline context flags (Pattern B) | `kubectl --context production` bypasses the current auth context |
| Blocklist instead of whitelist for read-only | New CLI versions add modify commands that slip through a blocklist |
| Using `jq -n` without `--arg` for dynamic values | Shell injection risk in reason strings |
