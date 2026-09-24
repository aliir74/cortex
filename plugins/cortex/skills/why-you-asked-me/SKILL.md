---
name: why-you-asked-me
description: Diagnoses why Claude prompted for permission on a command that should have been auto-allowed, then applies a minimal fix. Use for 'why did you ask me', 'why is this prompting', 'this should be auto-allowed', or a screenshot of a permission prompt.
---

# Why You Asked Me (Permission Prompt Diagnosis)

The user is annoyed that Claude asked for permission on a command they consider safe (usually read-only). They want a root-cause diagnosis and a fix, not a workaround.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/why-you-asked-me.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/why-you-asked-me/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/why-you-asked-me.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/why-you-asked-me.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `hooks_dir` → `~/.claude/hooks`
   - `permissions_toml_path` → empty, meaning the user has no regex-rules permissions file; skip that layer

## Inputs

The user provides ONE of:
- A screenshot showing the permission prompt (with the command and the hook reason)
- A pasted command + hook reason text
- A description like "it asked me to confirm `<command>`"

Extract from the input:
- **Exact command** (including flags and quoting)
- **Hook reason text** if shown (e.g., "slack write operation — confirm before proceeding"); this names the source hook
- **Tool type** (Bash, WebFetch, etc.), usually Bash

## Diagnosis Workflow

### Step 1: Identify the source

These layers can prompt. Find which one fired:

1. **PreToolUse hook script** — registered under `hooks.PreToolUse` in `~/.claude/settings.json`, a project `.claude/settings.json` / `settings.local.json`, or a plugin's `hooks/hooks.json`. The reason text is custom (e.g., "<tool> write operation — confirm before proceeding").
2. **Regex-rules permissions file** — only if `permissions_toml_path` is set: a PreToolUse hook that evaluates `[[allow]]` / `[[deny]]` regex rules from that TOML. No match falls through to the next layer.
3. **`permissions` rules in settings** — `permissions.allow[]` / `deny[]` / `ask[]` in user, project, and local settings files.
4. **Built-in Claude Code prompt** — generic "requires confirmation" with no custom reason. Means nothing above allowed it.

The reason text is the strongest clue. If it names a tool, find that tool's hook script first (grep the settings files' `hooks.PreToolUse` entries for its path). If the reason is generic, check the TOML (if any) and the `permissions` arrays.

### Step 2: Read the relevant file(s)

- Hook script: the path registered in settings (commonly `<hooks_dir>/<name>-permission-check.sh`). Find the branch the command should have matched but didn't.
- TOML (if configured): find the missing or too-narrow `[[allow]]` block.
- Settings: check `permissions.allow[]` in the user, project, and local settings files.

### Step 3: Find the gap

For hook scripts (most common case): each branch is typically `grep -qE '<regex>'`. Test whether the user's command matches each read-only allow branch. Identify the first branch that *should* have matched but didn't, and explain why (e.g., regex requires a subcommand the user didn't pass; flag order; quoting).

Common gaps:
- **Subcommand required, user used bare form** — e.g., hook expects `search messages|files|all` but the CLI also accepts `search <query>` directly. Fix: loosen the regex to `\bsearch\b` since the verb itself is read-only.
- **Argument-anchored regex misses flag variants** — e.g., `-l` vs `--limit`, `-q` vs `--query`.
- **Command runs through a launcher or wrapper** — the top-level filter matches `^tool\b` but the user invoked `bun x tool ...`, `npx tool ...`, or an absolute path.
- **TOML rule too narrow** — e.g., `^cat /etc/` but the user ran `cat ~/file`.
- **Hook returns "ask" as catch-all** — by design every unmatched verb falls through to ask. Adding the read verb to the allow list is the fix.
- **Settings glob too narrow** — `Bash(tool list:*)` exists but the user ran `tool list --json`, or the rule is in a project settings file that does not apply to the current directory.

### Step 4: Verify the verb is actually read-only

Before proposing a "loosen regex" fix, confirm the command is genuinely read-only by checking the CLI's help output or its skill file. Don't auto-allow a verb that has destructive overloads (e.g., `git checkout` is not safe to broadly allow).

If unsure, propose the narrower fix (allow the exact subcommand the user ran, not the whole verb).

### Step 5: Propose the fix

Output a short explanation in this shape:

```
The prompt fired because <ONE-SENTENCE ROOT CAUSE>.

<File>:<line> — <which branch/rule was supposed to match and why it didn't>.

Fix: <smallest change that closes the gap>
```

Then:
- If the fix is a small regex tweak in a hook script, **apply it immediately** with Edit. Editing hook scripts is the explicit, expected scope of this skill: the user invokes it to get the hook *fixed*, not just diagnosed.
- If the fix touches the permissions TOML or a `permissions.allow[]` array, hand off to the `update-permissions` skill so both systems stay consistent and the security review runs.
- If unsure whether the verb is read-only, ask before applying.

After applying, mention the user will need to retry the original command (the current prompt still needs to be answered or cancelled).

## Output Style

Keep it tight:
1. One-sentence root cause
2. The exact file:line
3. The fix (applied or proposed)

Skip preamble like "Let me investigate". Just diagnose and fix.

## Anti-patterns

- **Don't suggest workarounds as the answer.** "Use the explicit form `search messages ...`" is a workaround, not a fix. The fix is making the hook match the form the user naturally types.
- **Don't propose `--dangerously-skip-permissions` or disabling the hook.** Always fix at the regex/rule level.
- **Don't broaden hooks to allow write verbs** without checking. If unclear, narrow fix > broad fix.
- **Don't read every hook script** — the reason text names the responsible hook. Read only that one.
