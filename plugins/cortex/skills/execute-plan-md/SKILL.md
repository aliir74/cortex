---
name: execute-plan-md
description: Use when a markdown .md plan file written by /create-plan-md needs executing task-by-task. Triggers on "execute markdown plan", "/execute-plan-md <path>". For HTML plans (the default) use /execute-plan. SKIP for plans with under 3 tasks.
argument-hint: <plan-path>
---

# Execute-Plan-MD

Runs a markdown plan written by `/create-plan-md` top to bottom: checkbox by checkbox, commit by commit, finishing by archiving it to `done/`. HTML sibling: `/execute-plan`.

**Model:** executing a settled plan is mechanical work gated by the plan's own tests, so run it on `sonnet`: either delegate to an Agent with `model: "sonnet"`, or switch the session with `/model sonnet`. If a task's build or tests fail twice and you can't get them green, or you start looping on the same edit, escalate that task to `opus`.

## User Preferences

This skill has no preferences file of its own. For the "list recent plans" fallback in Step 1 it reads `plans_dir` from `${CLAUDE_PLUGIN_DATA}/preferences/create-plan-md.md` (seeded by `/create-plan-md`); if that file or field is absent, it uses the same default (`docs/plans/` if it exists in the repo, else `plans/`).

## When to use

- A `.md` plan in the format `/create-plan-md` writes (Goal / Status / `## Phase N` / `### Task N.M` / `- [ ]` steps) and the user says "run it"
- 3+ tasks worth the ceremony

## When NOT to use

- Fewer than 3 tasks → just do them
- Placeholders ("TBD", "similar to X", "handle edge cases") → tell the user to fix the plan first

## Workflow

### Step 1: Resolve the plan path

Use the argument if given. Otherwise list recent `*.md` plans in the resolved plans directory:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/create-plan-md/helpers/resolve-plan-dir.sh" "${CLAUDE_PLUGIN_DATA}/preferences/create-plan-md.md"
```

and ask via AskUserQuestion which to run.

### Step 2: Read and critically review

- Read the full plan.
- Look for placeholders (`TBD`, `_(fill in)_`), missing `**Files:**` blocks, vague task wording.
- If any are found, STOP and tell the user what's missing. Do not execute.
- Otherwise announce: "Plan looks good. N tasks across M phases. Starting."

### Step 3: Flip Status

Edit `**Status:** planning` → `**Status:** in_progress`.

### Step 4: TodoWrite

Use `next-task.sh` (or read the plan) and create one TodoWrite entry per `### Task N.M`, not per checkbox.

### Step 5: Work each task

**Branch check before the first commit:** in a git repo, never commit implementation work to `main`/`master`. If you're on one, create a feature branch now (`git checkout -b <plan-slug>`, or whatever branch naming the repo's CLAUDE.md prescribes). Branching after the fact causes divergent state and rebase conflicts.

For each task, top to bottom:

1. Mark its TodoWrite entry `in_progress`.
2. For each `- [ ]` step: do the work, run the verification the step names, then flip it:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/skills/execute-plan-md/helpers/mark-done.sh" "<plan-path>" "<unique substring of the step line>"
   ```
3. Run the task's commit step. First task of the run: `git add <plan-path> <code-paths>`, so the plan lands in its first real commit. Later tasks: include the plan file too, since its checkboxes changed.
4. Mark the TodoWrite entry `completed`.
5. If any verification fails or hits a blocker, STOP and surface the error. Do not guess.

### Step 6: Archive on completion

When `next-task.sh` exits 1 (every `- [ ]` is now `- [x]`):

1. `bash "${CLAUDE_PLUGIN_ROOT}/skills/execute-plan-md/helpers/archive-plan.sh" "<plan-path>"` flips Status to `done`, moves the file into `<plan-dir>/done/`, and prints the new path.
2. Commit the archive: `git commit -m "chore(plans): archive <slug>"`.
3. Report: "Done. N tasks completed, plan archived to `<new-path>`, K commits."

## Helper scripts

In `${CLAUDE_PLUGIN_ROOT}/skills/execute-plan-md/helpers/`:

- **`next-task.sh <plan-path>`** — prints the next unchecked step with its task heading and Files block. Exit 1 when the plan is complete.
- **`mark-done.sh <plan-path> "<needle>"`** — flips the one `- [ ]` line containing the needle to `- [x]`. Errors on zero or multiple matches.
  - Pick a needle that appears verbatim on the `- [ ]` line itself, never from a code block or sub-bullet below it. Backticks are fine.
  - **Fallback is immediate:** if it fails once (apostrophes, angle brackets, special characters), flip the checkbox with the Edit tool. Don't retry with other needles.
- **`archive-plan.sh <plan-path>`** — flips Status to `done` and moves the plan to `<dir>/done/`. Prints the new absolute path.

## Failure modes

- **Test fails** → stop, report, ask.
- **Ambiguous step** → stop, quote it, ask the user to clarify in the file.
- **Session interrupted** → rerun `/execute-plan-md <same-path>`; `next-task.sh` resumes at the first `- [ ]`.
- **User changes the plan mid-run** → pause, let them edit, re-read, resume at the next `- [ ]`.
- **Not a git repo** → skip commit steps, do the file work, tell the user commits were skipped.

## Anti-patterns

- Ticking a phase `### Verification` item because the phase mostly passed. Each item is a literal criterion.
- Ticking a "fix X" / "update X" step after adding new text near X instead of changing X.
- Executing a plan with placeholders, or guessing when a step is unclear.
- Skipping archival: finished plans should leave the plans root.
