---
name: create-plan-and-execute
description: Use when the user wants to plan and execute a task in one go using the default HTML plan format. Triggers on "plan and execute", "plan then run", "plan and ship", "draft plan and run it", "/create-plan-and-execute". SKIP for small diffs, when only a draft is wanted (/create-plan), or when the markdown format is wanted (/create-plan-and-execute-md).
argument-hint: <goal or task description>
---

# Create-Plan-and-Execute

Runs `create-plan` to write a visual HTML plan, then immediately hands the path to `execute-plan`. Markdown sibling: `/create-plan-and-execute-md`.

## User Preferences

No preferences file of its own. `create-plan` loads `${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md` (plan directory, TDD default, drafting model) as usual; `open_after_create` is ignored here because this skill always suppresses the open step.

## When NOT to use

- Under about 5 tool calls → TodoWrite
- The user wants to review or edit the plan before it runs → `/create-plan` alone
- The user wants markdown → `/create-plan-and-execute-md`

## Workflow

### Step 1: Run create-plan with PLAN_NO_OPEN

Invoke the `create-plan` skill and run its full workflow (intent questions, drafting, rendering) with `PLAN_NO_OPEN=1` so its open step is skipped: no browser popup, since execution starts immediately. Its validation step (the independent sub-agent check against the real code) still runs; do not skip it because execution follows. Capture the absolute plan path.

### Step 2: Run execute-plan immediately

Invoke the `execute-plan` skill with that path. No confirmation pause. Tell the user in one sentence ("Plan written to <path>. Executing now.") and proceed.

## Red flags

- Planning inline instead of invoking `create-plan`.
- Opening the plan between the two steps.
- Pausing to ask "run it now?": this skill is no-confirm by design.
- Editing files without going through `execute-plan`.
- Passing the `.html` plan to `execute-plan-md`: only `execute-plan` parses HTML plans.
