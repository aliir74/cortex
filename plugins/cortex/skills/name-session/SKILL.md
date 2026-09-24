---
name: name-session
description: Use when a Claude Code session needs a structured name derived from its conversation context. Triggers on "/name-session", "name this session", "suggest a session name".
argument-hint: "[optional-override]"
disable-model-invocation: true
---

# Name This Session

Generate a concise, descriptive session name for `/rename` based on what happened in this conversation.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/name-session.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/name-session/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/name-session.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/name-session.md`, edit anytime to customize."
2. Read it. `recurring_commands` lists slash commands whose sessions recur on a date cadence (default: empty, rely on judgment). `copy_to_clipboard` controls whether the `/rename` command is copied (default: `true`).

## How to Run

Name generation is cheap, mechanical work; delegate it to a Haiku subagent rather than spending a larger model's tokens on it.

1. **Gather context yourself** (you have the conversation history; the subagent doesn't):
   - **Git branch**: !`git branch --show-current 2>/dev/null || true`
   - **Recent commits** (if any were made this session): !`git log --oneline -3 2>/dev/null || true`
   - **Working directory**: !`pwd 2>/dev/null || true`
   - **Conversation summary**: 2 to 4 sentences describing the primary goal, task, or topic
   - **$ARGUMENTS**: if the user passed an override, include it verbatim
   - **Today's date** (only if the session is a recurring routine, see Rules): `date +%Y-%m-%d`

2. **Dispatch a subagent** via the Agent tool with `subagent_type: "general-purpose"` and `model: "haiku"`. Pass it:
   - The gathered context above
   - The Naming Format, Examples, and Rules sections below (copy them into the prompt; the subagent doesn't see this file)
   - Instruction: return ONLY the suggested name on a single line (no preamble, no quotes, no `/rename` prefix)

3. **Receive the name**, then handle Output (below) yourself.

## Naming Format

```
[context] goal-description
```

- **context**: The most relevant identifier: git branch name, project name, ticket ID, or topic area. Pick whichever best distinguishes this session from others.
- **goal-description**: A short phrase (2 to 5 words) describing what the session achieved or worked on, in kebab-case.

## Examples

- `[feat/signup-flow] fix-validation-errors`
- `[payments-api] add-webhook-retry-logic`
- `[main] setup-ci-pipeline`
- `[research] terminal-emulator-config`
- `[k8s-deployment] debug-staging-pods`
- `[hotfix/auth] patch-token-expiry`
- `[notes] triage-reading-list`
- `[notes] weekly-review-YYYY-MM-DD` (recurring routine, date appended)

## Rules

- Keep the total name under 60 characters
- If a branch name is long, abbreviate it but keep it recognizable
- If there is no git branch (non-code context), use the project folder name or topic area as context
- If the user provides $ARGUMENTS, use that as the goal-description instead of inferring
- Prefer specificity over generic names. "fix-bug" is bad, "fix-login-redirect-loop" is good
- **Recurring routine sessions**: if the session was driven by a command listed in `recurring_commands`, or is otherwise clearly a routine re-run on a cadence that would produce a same-named session each time (daily review, weekly triage, inbox sync), append today's date (`YYYY-MM-DD`) to the goal-description
- For all other sessions, do NOT include dates in the name

## Output

After the subagent returns the name:

1. Show the suggested name
2. If `copy_to_clipboard` is true and `pbcopy` (macOS), `wl-copy` or `xclip -selection clipboard` is available, copy `/rename <suggested-name>` to the clipboard via a heredoc (`cat << 'EOF' | pbcopy`) and say: "Copied to clipboard. Paste to apply."
3. Otherwise print the `/rename <suggested-name>` line for the user to copy.
