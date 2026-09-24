---
name: create-plan-and-execute-md
description: Use when the user wants to plan and execute a task in one go using the plain markdown format. Triggers on "plan and execute markdown", "/create-plan-and-execute-md". SKIP for small diffs, when only a draft is wanted (/create-plan-md), or when the default HTML format is wanted (/create-plan-and-execute).
argument-hint: <goal or task description>
---

# Create-Plan-and-Execute-MD

Runs `create-plan-md` to write a markdown plan, then immediately hands the path to `execute-plan-md`. HTML sibling: `/create-plan-and-execute`.

## User Preferences

No preferences file of its own. `create-plan-md` loads `${CLAUDE_PLUGIN_DATA}/preferences/create-plan-md.md` (plan directory, TDD default, drafting model) as usual; `open_after_create` is ignored here because this skill always suppresses the open step.

## When NOT to use

- Under about 5 tool calls → TodoWrite
- The user wants to review or edit the plan before it runs → `/create-plan-md` alone
- The user wants the visual HTML format → `/create-plan-and-execute`

## Workflow

### Step 1: Run create-plan-md with PLAN_NO_OPEN

Invoke the `create-plan-md` skill and run its full workflow (intent questions, drafting, writing) with `PLAN_NO_OPEN=1` so its open step is skipped: no editor popup, since execution starts immediately. Its validation step (the independent sub-agent check against the real code) still runs; do not skip it because execution follows. Capture the absolute plan path.

### Step 2: Run execute-plan-md immediately

Invoke the `execute-plan-md` skill with that path. No confirmation pause. Tell the user in one sentence ("Plan written to <path>. Executing now.") and proceed.

## Red flags

- Planning inline instead of invoking `create-plan-md`.
- Opening the plan between the two steps.
- Pausing to ask "run it now?": this skill is no-confirm by design.
- Editing files without going through `execute-plan-md`.
