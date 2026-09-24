---
name: update-permissions
description: Use when user wants to add, remove, or modify Claude Code permission rules - triggers on "allow this", "add permission", "update permissions", "always allow", "block this", "deny permission", or any request to change what commands are auto-approved or prompted
---

# Update Permissions

Claude Code permission decisions can come from several independent layers. When more than one layer covers a command, update them together or permissions become inconsistent.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/update-permissions.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/update-permissions/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/update-permissions.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/update-permissions.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `default_scope` → ask each time whether a rule belongs in user settings (`~/.claude/settings.json`), project settings (`.claude/settings.json`, committed), or local settings (`.claude/settings.local.json`, not committed)
   - `permissions_toml_path` → empty, meaning the user has no regex-rules permissions file; skip that layer everywhere below

## The Layers

### 1. `permissions` rules in settings files

Built-in Claude Code permissions, in `permissions.allow[]`, `permissions.ask[]`, and `permissions.deny[]` of:
- `~/.claude/settings.json` (user, every project)
- `<project>/.claude/settings.json` (project, shared via git)
- `<project>/.claude/settings.local.json` (local, personal, gitignored)

```json
"Bash(command-prefix:*)"
"Bash(command *)"
"WebFetch(domain:example.com)"
```

- Glob-style patterns; `deny` beats `ask` beats `allow`.
- The local file also accumulates one-off approvals from interactive "always allow" clicks.

### 2. PreToolUse hook scripts

Registered under `hooks.PreToolUse[]` in any of the settings files above (or a plugin's `hooks/hooks.json`). They run arbitrary scripts that can inspect the command and runtime state and return a dynamic decision.

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "bash ~/.claude/hooks/my-hook.sh" }]
    }
  ]
}
```

**How hook scripts work:**
- Receive tool call JSON on stdin: `{"tool_input": {"command": "kubectl get pods"}}`
- Parse with `jq`: `COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""')`
- Return a JSON decision on stdout, or exit silently (no output) to fall through

**Decision format:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Human-readable reason shown to user"
  }
}
```

- `"allow"` — auto-approve
- `"deny"` — block with reason
- `"ask"` — prompt user with reason as context
- No output — fall through to the other layers

To see which hooks exist, read the `hooks.PreToolUse` entries of every settings file in scope and open each registered script. Do not assume a fixed inventory.

### 3. Regex-rules permissions TOML (optional)

Only if `permissions_toml_path` is set. Some setups run a PreToolUse hook that evaluates regex rules from a TOML file (the same file `create-permission-hook` can append to):

```toml
[[allow]]
tool = "Bash"
command_regex = "^command(\\s|$)"
command_exclude_regex = "&&|;|\\||`|\\$\\("
```

- `command_regex`: anchored match (`^`) for the command
- `command_exclude_regex`: rejects dangerous patterns even if the regex matches
- **Standard exclusions for simple commands:** `&&|;|\\||` `` ` `` `|\\$\\(`
- Unmatched commands fall through to the other layers

> **Do not pair a gating hook with a blanket allow rule.** A broad rule like `^TOOL\s+` (TOML) or `Bash(TOOL:*)` (settings) matches writes too, and can return `allow` before the tool's hook gets to return `ask`. Precedence between multiple hooks returning allow vs ask is not something to rely on. A read/write gating hook already returns `allow` for reads, so the broad rule is redundant at best. If a rule is needed at all, scope it to read verbs only.

**When to use hook scripts vs static rules:**
- Use **static rules** (settings globs, or TOML regex) for fixed command patterns.
- Use **hook scripts** for decisions that depend on runtime state (current k8s context, git branch, env vars, file contents) or on argument structure a glob can't express. Create them with `create-permission-hook`.

**Hook script conventions:**
- Make executable (`chmod +x`)
- Always `INPUT=$(cat)` first to consume stdin
- Exit early with no output for irrelevant commands
- Use `jq -n` with `--arg` to generate decision JSON

## Workflow

### Step 1: Read All Permission Files

Always read these before making changes:
- `~/.claude/settings.json`
- The current project's `.claude/settings.json` and `.claude/settings.local.json` (if present)
- The permissions TOML, if `permissions_toml_path` is set
- Any hook scripts registered in `hooks.PreToolUse` that match the command in question

### Step 2: Determine the Change

| Action | Settings `permissions` | Permissions TOML (if used) | Hook scripts |
|--------|-------------|------------------|--------------|
| **Allow new command** | Add `"Bash(command:*)"` to `allow` | Add `[[allow]]` block with regex + exclusions | N/A unless dynamic |
| **Allow chained commands** | Add matching pattern to `allow` | Add rule WITHOUT `&&` in exclude_regex | N/A |
| **Remove permission** | Remove entry from `allow` | Delete the `[[allow]]` block | Remove from script |
| **Block command** | Add to `deny` | Add `[[deny]]` block | Return `"deny"` decision |
| **Conditional permission** (e.g., allow if non-prod) | Leave the command unlisted (or in `ask`) | No broad allow | Script checks runtime state and returns `allow`/`ask`/`deny` |

If a hook already gates the command, change the hook rather than adding a static rule that could bypass its dynamic check.

### Step 3: Apply Changes

**For the settings files**, use the matching glob pattern and the scope from `default_scope` (or ask).

**For the permissions TOML**, always include an appropriate `command_exclude_regex`:
- Simple commands: `&&|;|\\||` `` ` `` `|\\$\\(` (blocks all chaining)
- Commands that need pipes: omit `\\|` from exclusion
- Commands that need chaining: omit `&&` but keep other exclusions

### Step 4: Validate

```bash
python3 -c "import json, sys; [json.load(open(p)) for p in sys.argv[1:]]; print('JSON valid')" <each settings file you edited>
python3 -c "import tomllib, sys; tomllib.load(open(sys.argv[1], 'rb')); print('TOML valid')" <permissions_toml_path>   # only if edited
```

### Step 5: Pattern Consolidation (EVERY RUN)

**Mandatory on every invocation.** After making the requested change, scan the permission files for abstraction opportunities. The goal is to keep permissions lean and general, not accumulate one-offs.

#### 5a. Static rules — merge redundant ones

| Pattern | Action |
|---------|--------|
| Narrow rule already matched by a broader rule | Delete the narrow rule |
| Multiple `cd + X` rules with the same exclude pattern | Merge into one `cd + (X\|Y\|Z)` rule |
| Command in both "no chaining" and "with chaining" rules | Keep only the broader one if exclusions are safe |
| Path-specific rule for a command already allowed broadly | Delete the path-specific rule |

**How to check:** for each rule, ask: "Is there another rule that already matches every command this one would match?" If yes, delete it.

#### 5b. Settings — prune one-offs

Scan `permissions.allow[]` for entries that should be removed or generalized:

| Pattern | Example | Action |
|---------|---------|--------|
| **Full command with args** (not a prefix pattern) | `Bash(summarize "https://youtube.com/...")` | Delete — stale one-off |
| **Heredoc fragments / message text** | `Bash(echo Failed:*)` | Delete — junk from interactive approval |
| **Already covered by a hook or broader rule** | `Bash(cat *)` when another layer allows `cat` | Delete |
| **Overly specific variant** of a broad entry | `Bash(ps aux \| grep foo:*)` when `Bash(ps:*)` exists | Delete the specific one |
| **Duplicate WebFetch domains** | Same domain listed twice | Delete duplicate |
| **Same command in two syntaxes** | `Bash(tail:*)` when `Bash(tail *)` exists | Delete one |

#### 5c. Abstract WebFetch domains

When 5+ domains share a pattern (e.g., all documentation sites), consider whether a wildcard like `WebFetch(domain:*.github.io)` is appropriate. **Only suggest this — don't apply without user confirmation**, since WebFetch wildcards have data exfiltration implications.

#### 5d. Apply and report

1. **Auto-apply safe removals** (duplicates, entries covered by other rules, stale one-offs)
2. **Propose but don't apply** risky abstractions (WebFetch wildcards, merging rules with different exclude patterns)
3. Include a consolidation summary in the final report.

### Step 6: Security Review

**Mandatory after every permission change.** Scan every permission file in scope entirely (not just the new change) and report all findings.

## Security Review Checklist

### Critical — must fix before completing

- No plaintext credentials or tokens in permission entries (OAuth secrets, API keys, access tokens)
- No sandbox bypasses auto-allowed: `bash:*`, `sh:*`, `python:*`, `perl:*`, `ruby:*`, `osascript:*` (arbitrary code execution)
- No unrestricted `rm *` or `rm:*` in auto-allow
- No auto-allowed `sudo` commands

### High — should fix

- No unrestricted `curl:*` / `wget:*` auto-allow (data exfiltration risk)
- No `chmod *` auto-allow
- No `pkill:*` / `killall:*` auto-allow
- Regex exclude patterns cover all chaining operators: `&&`, `;`, `|`, `` ` ``, `$(`
- No `eval` or `exec` in allowed patterns
- No broad static allow that pre-empts a gating hook for the same tool

### Medium — flag for review

- No stale one-off entries (heredoc fragments, message text, junk from interactive approvals)
- Loop rules exclude `rm\s` broadly (not just `rm -rf`)
- Pipe rules don't allow dangerous right-side commands (rm, curl, wget)
- New rule doesn't conflict with or make existing rules redundant
- Hook scripts consume stdin (`INPUT=$(cat)`) — missing this causes hangs
- Hook scripts exit silently for irrelevant commands — returning a decision for every Bash call overrides all other permission rules
- Hook script `ask` reasons are clear and actionable (the user sees them at the prompt)

### Report to User

After the review, print a combined summary:

```
## Permission Update Report

**Changes made:**
- [what was added/removed/modified in each file]

**Consolidation:**
- Auto-applied: [removals, merges — or "none needed"]
- Proposed: [abstractions needing confirmation — or "none"]

**Security scan:** X critical, X high, X medium issues
[List any issues found with severity and recommendation]

**Status:** Clean / Needs attention
```

Always report even if no issues were found — "0 critical, 0 high, 0 medium — Clean" confirms the review ran.

## Common Mistakes

- Updating only one layer while another still prompts or blocks
- Forgetting `command_exclude_regex` in TOML rules — allows command-chaining bypasses
- Not anchoring TOML regex with `^` — matches commands mid-string
- Accumulating stale one-off entries from clicking "always allow" — audit periodically
- Adding a chained-command allow in one layer while the other only has the simple form — both need to match
- Adding narrow path-specific rules when a broad command-level rule is better — for read-only commands like `cat`, `head`, `tail`, prefer allowing the command broadly
- Forgetting to check existing hook scripts for a tool — the hook may already handle the case dynamically
- Adding a static allow for something a hook gates — this can bypass the hook's dynamic check
- Creating a hook with `matcher: "Bash"` that returns a decision for ALL commands — it must exit silently for irrelevant ones
