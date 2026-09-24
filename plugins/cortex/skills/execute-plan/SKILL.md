---
name: execute-plan
description: Use when an HTML plan file written by /create-plan needs executing task-by-task. Triggers on "execute plan", "run plan", "run the plan", "work through plan", "/execute-plan <path>". SKIP for plans with under 3 tasks (just do them) or for markdown .md plans (use /execute-plan-md).
argument-hint: <plan-path>
---

# Execute-Plan

Runs an HTML plan written by `/create-plan` top to bottom: step by step, commit by commit, finishing by archiving it to `done/`. Markdown sibling: `/execute-plan-md`.

**Model:** executing a settled plan is mechanical work gated by the plan's own tests, so run it on `sonnet`: either delegate to an Agent with `model: "sonnet"`, or switch the session with `/model sonnet`. If a task's build or tests fail twice and you can't get them green, or you start looping on the same edit, escalate that task to `opus`.

## User Preferences

This skill has no preferences file of its own. For the "list recent plans" fallback in Step 1 it reads `plans_dir` from `${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md` (seeded by `/create-plan`); if that file or field is absent, it uses the same default (`docs/plans/` if it exists in the repo, else `plans/`).

## When NOT to use

- The plan is `.md` → `/execute-plan-md`
- Fewer than 3 tasks → just do them
- The plan still has placeholders → tell the user to fix it first

## Workflow

### Step 1: Resolve the plan path

Use the argument if given. Otherwise list recent `*.html` plans in the resolved plans directory:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/create-plan/helpers/resolve-plan-dir.sh" "${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md"
```

and ask via AskUserQuestion which to run.

### Step 2: Read and critically review

- Read the full plan.
- Look for an empty Architecture (`<em>(fill in before execution)</em>`), placeholder step text (`TBD`, `(fill in)`), tasks with no `<li class="step">` children.
- If any are found, STOP and tell the user. Do not execute.
- Otherwise announce: "Plan looks good. N tasks across M phases. Starting."

### Step 3: Status

The hero starts as `<header class="hero" data-status="planning">`. `mark-done-html.py` bumps it to `in_progress` on the first marked step and to `done` when nothing is pending, so no manual flip is needed.

### Step 4: TodoWrite

Enumerate tasks with `next-task-html.py` (or by reading the HTML) and create one TodoWrite entry per `<article data-task-id="X">`, not per step.

### Step 5: Work each task

**Branch check before the first commit:** in a git repo, never commit implementation work to `main`/`master`. If you're on one, create a feature branch now (`git checkout -b <plan-slug>`, or whatever branch naming the repo's CLAUDE.md prescribes).

For each task, top to bottom:

1. Mark its TodoWrite entry `in_progress`.
2. For each `<li class="step" data-status="pending">`: do the work, run the verification the step names, then mark it done:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/execute-plan/helpers/mark-done-html.py" "<plan-path>" "<unique substring of the step text>"
   ```
3. Run the task's commit step. First task of the run: `git add <plan-path> <code-paths>`, so the plan lands in its first real commit. Later tasks: include the plan file too, since the helper edited it.
4. Mark the TodoWrite entry `completed`.
5. If any verification fails, STOP and surface the error. Do not guess.

### Step 6: Archive on completion

When `next-task-html.py` exits 1 (nothing pending):

1. `python3 "${CLAUDE_PLUGIN_ROOT}/skills/execute-plan/helpers/archive-plan-html.py" "<plan-path>"` sets the hero to `done`, moves the file into `<plan-dir>/done/`, and prints the new path.
2. Commit the archive: `git commit -m "chore(plans): archive <slug>"`.
3. Report: "Done. N tasks completed, plan archived to `<new-path>`, K commits."

## Helper scripts

In `${CLAUDE_PLUGIN_ROOT}/skills/execute-plan/helpers/`:

- **`next-task-html.py <plan-path>`** — prints the next pending step with its task heading and files (`TASK:` / `FILES:` / `STEP:`). Exit 0 if printed, 1 when the plan is complete.
- **`mark-done-html.py <plan-path> "<needle>"`** — flips the one pending step whose text contains the needle (case-insensitive, backticks ignored): sets `data-status="done"`, adds `checked`, recomputes the task's `data-task-status` and the hero status. Errors on zero or multiple matches.
  - **Fallback is immediate:** if it fails once (emoji, HTML entity, angle brackets in the step text), edit the `<li>` directly: flip `data-status`, add `checked`, recompute the parent `<article data-task-status>`. Never re-render the plan to fix a mark; the marks exist only in the HTML.
- **`archive-plan-html.py <plan-path>`** — sets the hero status to `done`, moves the file to `<dir>/done/`, prints the new absolute path.

## Failure modes

- **Verification fails** → stop, report, ask.
- **Ambiguous step** → stop, quote it, ask the user to clarify in the file.
- **Session interrupted** → rerun `/execute-plan <same-path>`; `next-task-html.py` resumes at the first pending step.
- **User changes the plan mid-run** → pause, let them edit, re-read, resume at the next pending step.
- **Not a git repo** → skip commit steps, do the file work, tell the user commits were skipped.

## Anti-patterns

- **Marking a phase checkpoint (`N.V`) row because the phase mostly passed.** Each row is a literal criterion. Mark it only when its own sentence is true; leave failing rows pending so the plan shows the real state.
- **Leaving a verify step done after learning it passed on a wrong precondition** (stale build, wrong assumption). Flip it back to pending and rewrite the check. A green plan that lies is worse than a red one.
- **Marking a "fix X" / "update X" step after adding new text near X.** Re-read X and confirm X itself changed; otherwise the file now contradicts itself.
- Executing a plan with placeholders, or guessing when a step is unclear.
- Skipping archival: finished plans should leave the plans root.
- Parsing the HTML with ad-hoc regex inline instead of using the helpers.
