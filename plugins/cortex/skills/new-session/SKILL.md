---
name: new-session
description: Spins up a fresh Claude Code session in a target folder, seeded with either a small fresh task brief or a continuation brief carrying in-flight context, and launches it in the background. Use for 'new session for X', 'start a session in <folder>', 'spin up a session to do Y', 'kick off Z over there'. For a handoff document only (no launch), use session-handoff.
argument-hint: <optional target folder path>
disable-model-invocation: true
---

# New Session

Launch a fresh Claude Code session in a target folder, seeded with context from this conversation, so it can pick up a task (or in-flight work) with everything it needs to start.

**How this differs from `session-handoff`:** `session-handoff` produces a document for a human or another agent to read. `new-session` writes a brief and actually **starts a new Claude Code session** on it, in another folder, via the Claude Code CLI.

Most of the time the input is light: a bit of context plus "go do X over there." Sometimes it's a genuine handoff of substantial in-flight work. Pick the flavor that matches what you actually have to carry; don't force a heavy retrospective onto a light task.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/new-session.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/new-session/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/new-session.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/new-session.md`, edit anytime to customize."
2. Read it. Fields and defaults:
   - `dispatch_mode`: `background` (default, launch with `claude --bg`) or `print` (print the command for the user to run in a terminal and watch).
   - `default_model`: empty (default) means pass `--model` with the **alias family of this session's own model** (`opus` / `sonnet` / `haiku`), so the child doesn't silently drop to the account default. Set a value (an alias or full model name) to always use that.
   - `default_effort`: empty (default) means omit `--effort`. Set `low` / `medium` / `high` / `xhigh` / `max` to pass it.
   - `use_worktree`: `false` (default). `true` adds `--worktree` so the new session works on an isolated git worktree (only when the target folder is a git repo).
   - `brief_dir`: where brief files are written. Default `/tmp`.

## Two Flavors

Pick the flavor before drafting; it decides the template and one phrase of the launch prompt.

- **Fresh task brief** (the common case): the new session does a *small, self-contained task* seeded with a bit of context. There is no meaningful "what was tried" history; this conversation is just the launchpad. Use the [Fresh Task Template](#fresh-task-template).
- **Continuation brief**: the new session *continues substantial in-flight work* from this conversation. There is real history to carry: what was tried, what worked, current state, open items. Use the [Continuation Template](#continuation-template).

**How to decide:** if you'd be writing real content into "What Was Tried" and "Current State", it's a continuation. If those sections would be empty, "N/A", or invented, it's a fresh task brief. Phrasing like "spin up a session to do X" or "start a session in <folder>" signals a fresh task; "carry on with this over there" signals a continuation. When on the fence, default to the fresh task brief: under-carrying a little context is cheaper than fabricating a fake history. Ask in one line only if you truly can't tell.

## Process

1. **Pick the flavor** (see above).
2. **Review the conversation** for what the template needs. Fresh task: the task, the target folder, pointers, constraints, key files. Continuation: objectives, approaches tried, outcomes, decisions, file changes, open items.
3. **Write the brief** with the matching template.
4. **Resolve the target folder**, the project root where the new session should run. Order: (a) the argument, if provided; (b) a path the user named in the current turn; (c) the obvious project root from conversation context (a repo just cloned or discussed). Only fall back to `AskUserQuestion` if still ambiguous. Confirm the folder exists; resolve it to an absolute path.
5. **Pick a session name** (see [Session Name](#session-name)).
6. **Launch** (see [Launch](#launch)). Do not ask for approval first; the brief file and the launch report are the user's review surface.

## Brief Templates

The **first line of every brief file**, both flavors, is the session intent header:

```
intent: <verb> <object> — <expected end-state>
```

It sits above the title so a human or agent scanning the file re-orients in seconds, e.g. `intent: add rate-limit headers to /search — endpoint returns X-RateLimit-* headers in staging`. The launch prompt tells the new session to echo it as its first message.

### Fresh Task Template

```markdown
intent: <verb> <object> — <expected end-state>

# Task: [Brief title]

## Task
[What the new session should do, 1-3 sentences, concrete and self-contained.]

## Context
- **Repo/Project:** [where this runs, branch if relevant]
- **Why now:** [one line on what prompted this, only if it helps]

## Pointers
- [Constraints, conventions, key files, commands, or gotchas the session needs to start]
- `path/to/file` — [why it matters]
```

Keep it short. Drop `## Context` or `## Pointers` entirely if empty.

### Continuation Template

Use the handoff template from the `session-handoff` skill (`${CLAUDE_PLUGIN_ROOT}/skills/session-handoff/SKILL.md`, section "Handoff Template": Objective, Context, What Was Tried, What Worked, Current State, Open Items, Key Files) and follow its Rules (be specific, include the why, flag gotchas, omit empty sections). Prepend the `intent:` line above its title. If that file is unavailable, use those same section headings.

## Session Name

The name shows in the `/resume` picker, `claude agents`, and the session's prompt box and terminal title. Aim for **3 to 6 words, about 40 characters max**. Lead with the verb or noun a human would search for.

| Session is about... | Pattern | Example |
|---|---|---|
| A fresh self-contained task | `<verb> <object>` | `add rate-limit headers to /search` |
| Babysitting a PR | `babysit <repo> #<N> (<topic>)` | `babysit api #131 (varchar fix)` |
| Continuing a feature | `<feature> — <next step>` | `lead capture form — wire submit` |
| Investigation / debug | `debug <symptom>` | `debug stale worker memory` |
| Migration / one-shot | `migrate <X> → <Y>` | `migrate full_name → text` |

Avoid full sentences, bare ticket IDs, dates, the words "session" or "handoff", and filler ("Working on..."). When launching several sessions in one round, make each name distinct on its own.

## Launch

### 1. Write the brief to a file

```bash
BRIEF_FILE="<brief_dir>/new-session-$(date +%Y%m%d-%H%M%S).md"
cat << 'EOF' > "$BRIEF_FILE"
<full brief markdown>
EOF
```

Use a single-quoted heredoc so `$`, backticks and backslashes in the brief are not expanded. A file (instead of inlining the brief as the prompt) avoids shell-quoting breakage and lets the new session re-read it if its context is cleared.

### 2. Build the launch prompt

The two flavors differ in one phrase: fresh says "START the task described in this brief"; continuation says "CONTINUE the work from this handoff brief".

```
Read <BRIEF_FILE> and START the task described in this brief right away; do not wait for confirmation. The first line of that file is the session intent; open your first message with that exact line, then begin working. Proceed autonomously through all local, reversible work (reading, investigating, drafting, editing code, running tests and linters, local commits). Stop and ask only before an irreversible or outward-visible action (pushing a branch, opening or merging a PR, deploying, changing a ticket status, sending any message). When you reach such a step, draft it fully and pause for the user's OK.
```

### 3. Launch the session

Run it from the target folder so that folder's `CLAUDE.md`, settings and permissions apply. Build the flags from preferences: `--model` (this session's model alias, or `default_model`), `--effort` only if `default_effort` is set, `--worktree` only if `use_worktree` is true.

**`dispatch_mode: background`** (default):

```bash
cd "$TARGET_DIR" && claude --bg --name "$SESSION_NAME" --model "$MODEL" "$PROMPT"
```

`claude --bg` returns immediately and prints a short session id. If the command fails (e.g. an older CLI without `--bg`; check `claude --help`), report the error and fall back to print mode below.

**`dispatch_mode: print`**: don't run anything; print the command for the user to paste into a new terminal:

```bash
cd "<TARGET_DIR>" && claude --name "<SESSION_NAME>" --model <MODEL> "<PROMPT>"
```

**Permission mode:** the new session inherits the permission settings of the target folder. Don't pass `--permission-mode bypassPermissions` (or any looser mode) unless the user explicitly asked; those let an unwatched session act without approval.

### 4. Report back

```
Brief: <BRIEF_FILE>
Launched "<SESSION_NAME>" in <TARGET_DIR> (id <ID>)
Watch or answer its prompts: claude attach <ID>   |   recent output: claude logs <ID>   |   list all: claude agents
It is starting the work now and will pause for your OK before any push / PR / deploy / message.
```

For print mode, report the brief path and the command instead. For several launches in one round, list one row per session (name, id, folder, job).

## Hard Constraints and Common Mistakes

- **Wrong flavor.** Forcing the continuation template on a fresh task produces empty or invented sections and a misframed "continue" prompt. Default to the fresh task brief.
- **Always start the brief with the `intent:` line**, and tell the new session to echo it first.
- **Always pass `--name`.** Unnamed background sessions are hard to tell apart in `claude agents` and `/resume`. Distinct names when launching several.
- **Always run from the target folder** (`cd "$TARGET_DIR" && ...`). Launching from the current directory loads the wrong project's `CLAUDE.md` and settings.
- **Never inline a multi-line brief as the prompt.** Use the brief file.
- **No approval gate before launch**, and no "confirm what you'll do before making changes" gate in the prompt: the new session starts immediately and pauses only at the impact gate.
- **Resolve the target folder from context** before asking.
- **Don't loosen permission mode** unless the user asked.
- **Brief files in `/tmp` are ephemeral.** If the brief is worth keeping, tell the user to save it somewhere durable, or set `brief_dir`.
