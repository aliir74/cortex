---
name: create-plan
description: Use when the user wants a structured implementation plan written to disk for a multi-file or multi-session task. Triggers on "create plan", "write plan", "plan this", "draft a plan", "visual plan", "/create-plan". SKIP for single-sentence diffs, exploratory questions, or work under about 5 tool calls (use TodoWrite), and when the user explicitly wants plain markdown (use /create-plan-md).
argument-hint: <goal or task description>
---

# Create-Plan

Writes a persistent, hand-editable implementation plan to disk as a self-contained interactive HTML document (progress ring, per-phase bars, collapsible task cards, clickable checkboxes). Hand-off target: `/execute-plan`. Plain-markdown sibling: `/create-plan-md`.

**Model split:** intent gathering runs in the session. Drafting (Step 4) runs in ONE sub-agent on the strongest model (`draft_model`, default `opus`). Validation (Step 5) runs in a separate, independent `opus` sub-agent. Execution is handed to `/execute-plan`, which runs the settled plan on `sonnet`.

Before rendering or hand-editing the HTML, load the `how-to-html` skill if it hasn't been loaded this session. The template already follows its conventions (dark mode, accessibility floor, inline SVG only).

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/create-plan/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `plans_dir`: `docs/plans/` if it exists in the repo, else `plans/` (resolved by the helper in Step 2)
   - `open_after_create`: `true`
   - `default_tdd`: ask
   - `draft_model`: `opus`

## When to use

- Multi-file change where scope isn't obvious, or multi-session work that must survive `/clear`
- The user wants visual progress across sessions, or wants to share/screenshot the plan

Use `/create-plan-md` instead when the user wants markdown (diffable in a repo, or a short plan where the visual layer is overkill).

## Workflow

### Step 1: Gather intent via AskUserQuestion

Ask in sequence (AskUserQuestion, not chat). Skip any question the triggering message already answered. Mark the recommended option in each label.

1. **Scope clarity** — `clear (I know what to build)` / `unclear (need to brainstorm first)`. If unclear, brainstorm with the user first (open questions until the scope is concrete; use a brainstorming skill if one is installed), then continue.
2. **Needs current external data?** — `no (working from known context)` / `yes (fresh docs, API, library or best-practice research)`. If yes, run `deep-research` first, then continue. Recommend yes only when the task touches recent libraries or APIs.
3. **Goal** — "What's the one-sentence goal?" (free text).
4. **Complexity** — `1 phase (<5 tasks)` / `2-3 phases (standard)` / `exhaustive (4+ phases)`.
5. **TDD?** — `yes (code with tests)` / `no (ops/docs/config)`. Skip when `default_tdd` is set.

### Step 2: Resolve the plan directory

```bash
PLAN_DIR_RESOLVED="$(bash "${CLAUDE_PLUGIN_ROOT}/skills/create-plan/helpers/resolve-plan-dir.sh" "${CLAUDE_PLUGIN_DATA}/preferences/create-plan.md")"
```

Priority: `$PLAN_DIR` env var → `plans_dir` preference → `<repo>/docs/plans/` if it exists → `<repo>/plans/` (or `$PWD/plans/` outside git). The helper creates the directory and prints its absolute path.

### Step 3: Slug and filename

- Slug: lowercase the goal, replace non-alphanumerics with `-`, strip leading/trailing `-`, keep it short.
- Filename: `YYYY-MM-DD-<slug>.html` (date from `date +%Y-%m-%d`). If it exists, append `-v2`, `-v3`, and so on.

### Step 4: Draft with one sub-agent, then render

Spawn ONE Agent (`model: <draft_model>`). Its brief carries, verbatim:

1. The Step 1 answers (goal, scope, complexity, TDD, any brainstorm/research output paths).
2. The repo root it may read, and the instruction to open the real files and grep the real symbols before decomposing. Tickets and descriptions go stale; the code at HEAD does not.
3. The complete JSON contract below, the verification rules, and the diagram criteria.
4. A temp path to write the JSON to: `/tmp/plan-draft-<slug>.json`. The sub-agent writes only that file: no plan-dir writes, no rendering, no opening, no commits, no user questions.

When it returns, check the file parses (`python3 -c "import json;json.load(open('/tmp/plan-draft-<slug>.json'))"`) and has the required fields, then render:

```bash
PLAN_PATH="$PLAN_DIR_RESOLVED/<YYYY-MM-DD-slug>.html"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/create-plan/helpers/render-plan.py" < /tmp/plan-draft-<slug>.json > "$PLAN_PATH"
```

**The JSON is the source of truth until execution starts.** To change the plan, edit the JSON and re-render. Hand-edits to the HTML are lost on re-render, and once `/execute-plan` has marked steps done, never re-render (the marks live only in the HTML); edit the HTML directly instead.

#### JSON contract

```json
{
  "feature_name": "string",
  "date": "YYYY-MM-DD",
  "slug": "YYYY-MM-DD-kebab-slug",
  "architecture": "2-3 sentences: what changes, where, and why",
  "architecture_diagram": { "svg": "<svg viewBox=\"0 0 800 240\" ...>...</svg>" },
  "tdd": true,
  "phases": [
    {
      "name": "Phase name",
      "tasks": [
        {
          "id": "1.1",
          "name": "Task name",
          "files": ["Create: path/to/foo.py", "Modify: path/to/bar.py"],
          "steps": ["Step text (`backticks` render as code)", "Verify: `pytest tests/test_foo.py -q` passes", "Commit: feat(foo): ..."],
          "notes": {
            "rationale": "One sentence on why this task exists.",
            "risks": ["Specific thing that could break"],
            "links": ["docs/design.md", "https://docs.example.com"]
          },
          "compare": { "before": "current code (plain text)", "after": "proposed code", "file": "path:lines", "lang": "Python" }
        }
      ]
    }
  ],
  "diagrams": [ { "caption": "What X does", "svg": "<svg viewBox=\"0 0 800 240\" ...>...</svg>" } ]
}
```

Required: `feature_name`, `date`, `slug`, `phases`. Everything else is optional; omit empty keys rather than passing `[]` or `{}`, the renderer drops absent sections.

- **Steps** are plain strings, one per checkbox, no nesting. `tdd: true` → Write failing test → Implement → Refactor → Verify → Commit. `tdd: false` → Implement → Verify → Commit.
- **Detail bar:** distinct phases, each a coherent milestone; tasks small enough that an executor on `sonnet` can do each without re-deriving context. Prefer more, smaller tasks.
- **Verification is mandatory per task and per phase.** Every task's `steps` includes a `"Verify: …"` step naming observable proof: a command and its expected output or exit code, a passing test, a file or route that exists, a log line, a UI state. Never `"Verify: confirm it works"`. The last task of every phase is a checkpoint (`id: "1.V"`, `name: "Phase 1 verification"`) whose steps are the phase's exit criteria.
- **`files`**: strings prefixed `Create:`, `Modify:` or `Reference:`.
- **`notes`**: only when non-obvious. `rationale` for a hidden constraint or deliberate trade-off; `risks` must be specific ("race between webhook and DB write"), never "make sure tests pass"; `links` are 1-3 URLs or repo paths the executor needs.
- **`compare`**: for refactors, signature changes, schema migrations, where the diff is the point. Renders as a unified diff. Skip for greenfield code.
- **`architecture_diagram`**: when the plan touches 3+ modules with non-trivial relationships, or the change is structural (data flow, call graph, state machine). Renders under the architecture callout.
- **`diagrams`**: subsystem diagrams at the bottom. Add one only when 3+ components interact, there's a state machine or branching flow, a before/after architecture helps, or the work is async/event-driven. Never fabricate one.
- The renderer HTML-escapes every string field except the SVGs. Never inject raw HTML through text fields.

#### Diagram rules (inline SVG only, never Mermaid)

- `viewBox`, no fixed `width`/`height`.
- All colours via CSS classes in a `<style>` block inside the SVG, plus a `@media (prefers-color-scheme: dark)` block overriding every fill, stroke and text colour.
- Colours carry meaning and stay consistent across the plan (for example green = safe/automatic, amber = needs attention, red = problem, indigo = entry point).
- `role="img"` and an `aria-label` sentence. One `<marker>` in `<defs>` reused for arrows.
- After rendering, run the `how-to-html` diagram verifier if it is installed: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/verify_diagrams.py" "$PLAN_PATH"`.

### Step 5: Validate with an independent sub-agent (required)

A plan never checked against the code is a draft. Spawn ONE Agent on `model: "opus"`, separate from the drafter so it doesn't repeat the drafter's blind spots. Give it `$PLAN_PATH` and the temp JSON path, and instruct it to:

1. Read the plan JSON.
2. Open every `Create:`/`Modify:`/`Reference:` path and grep for every symbol, function and config the plan assumes exists.
3. Report every **missing piece** (step, file, migration, dependency, edge case), **mistake** (wrong path, nonexistent or different API, wrong assumption about current behaviour, cross-phase contradiction, out-of-order dependency) and **unverifiable step** (vague or missing `Verify:` or checkpoint).
4. Give each issue a severity (blocker / should-fix / nit), the task id, and the concrete fix.

Apply blocker and should-fix findings to the JSON and re-render. Re-run validation once if the fixes were substantial. Record unresolved nits in the plan's Decisions Made table. Tell the user in one line what validation found and fixed.

### Step 6: Open

Skip if `$PLAN_NO_OPEN` is set (the `create-plan-and-execute` wrapper sets it) or `open_after_create` is `false`. Otherwise open with the OS default opener, which routes `.html` to the browser:

```bash
if [[ -z "${PLAN_NO_OPEN:-}" ]]; then
  if command -v open >/dev/null; then open "$PLAN_PATH"; elif command -v xdg-open >/dev/null; then xdg-open "$PLAN_PATH"; fi
fi
```

If neither opener exists, just print the path.

### Step 7: Report and hand off

- Print the absolute path.
- "Review or hand-edit it, then run `/execute-plan <path>` when ready."
- If the plan belongs to an issue, PR or tracked task, offer to link it there (see the `how-to-html` linking guidance); never invent a task to link to.

Do NOT start executing unless the user explicitly asks.

## What the rendered HTML contains

- **Hero:** title, status pill (Planning / In Progress / Done), task and step counters, progress ring.
- **Architecture callout** and optional architecture diagram.
- **Phase sections** with progress bars; **task cards** (click the header to expand) with files, checklist, an optional notes rail, and an optional unified diff.
- **Decisions Made / Errors Encountered** tables, empty at first, filled during execution.
- **Diagrams** section and a print stylesheet that expands every task.

Checkbox state lives in each step's `data-status` attribute in the file, not in localStorage. `/execute-plan` writes those attributes as the canonical record.

## Anti-patterns

- Writing the JSON inline in chat or in a bash heredoc (heredocs mangle backslashes). Write it to the temp file, then pipe it through the renderer.
- Adding per-plan CSS or swapping template fonts. Every plan uses the same template so plans scan the same way.
- Auto-committing the plan. `/execute-plan` bundles it into the first task commit.
- Skipping Step 5 because execution follows immediately.
