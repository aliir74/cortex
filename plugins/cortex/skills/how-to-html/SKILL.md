---
name: how-to-html
description: Use whenever generating or substantially editing an HTML file: plans, reports, dashboards, custom-editor UIs, slides, anything written to a `.html` file. SKIP for trivial fragments under about 5KB or files inside node_modules, dist, build or .git.
---

# How to HTML

Meta-skill for every HTML artifact Claude writes (`/create-plan`, `/make-slides`, plus ad-hoc generation), after [thariqs' "The Unreasonable Effectiveness of HTML"](https://thariqs.github.io/html-effectiveness/). HTML is the right format when information has spatial structure (diffs, call graphs, timelines, before/after, dashboards, draggable cards), which markdown flattens into prose. The other half is the round-trip: Claude generates a UI, the user manipulates it, and the result comes back as JSON.

This file is the **dispatcher**: it decides whether HTML is right, how the content is written, and what happens after the file exists. The craft (design, mobile floor, charts, verification) is in **`references/render.md`**, read by whoever writes the markup.

**If you are a render sub-agent: read `references/render.md` now, then the reference files it names.** Nothing else in this file is for you except "The content file is authoritative".

## When to reach for HTML

| Reach for HTML | Stay in markdown |
|---|---|
| Implementation plans with phases + progress | Single-task plans, quick notes |
| Reports with charts, status pills, timelines | Status updates that grep well |
| Dashboards (cost, audit, PR status) | Logs, journals, anything searched later |
| Custom editors (triage, prioritize, build) | Decisions captured once and filed |
| Side-by-side comparisons (before/after, diff annotations) | Two paragraphs of prose |
| Slide decks | README-style docs |
| Diagrams + explanations together | Plain explanations |

Default to markdown. Reach for HTML when the information is *spatial* (positions relative to each other matter), *interactive* (the user needs to click/drag/toggle), or *dimensional* (multiple parallel attributes per item that compare visually). If the output will be grepped, journaled, or linked from notes later, markdown wins regardless.

## Direct is the default

**Write the HTML yourself, in this thread.** A dispatched renderer costs several times more tokens and requests than an inline build and produces a smaller artifact.

`references/dispatch.md` holds the sub-agent flow for the rare case the main thread genuinely cannot hold the work. Using it is a deliberate exception you state a reason for, not a default.

| Situation | Path |
|---|---|
| Any artifact Claude authors (report, analysis, brainstorm result, prep doc, research synthesis, ad-hoc editor) | Write it here |
| A skill that renders a template by script (`/create-plan`, `/make-slides`) | Follow that skill |
| Editing an existing `.html` | Targeted `Edit` in place |
| A fragment under about 5 KB | Just write it, no content file |

### Step 1: write the content file

Write `<target>.content.md` next to the target path (same slug, so `docs/plans/foo.html` gets `docs/plans/foo.content.md`). It is the whole deliverable in markdown; the render step lays it out and adds nothing.

The content file IS:

1. **A header block**: `purpose:` (report / analysis / brainstorm / prep / dashboard / editor), `audience:` (who reads it; assume phone-first), `middle:` (one of investigation / verdict / options / research / audit, for reports), `collapse:` (`collapsed`, the default, or `expanded` for an artifact genuinely read in one pass such as a deck or a one-screen dashboard).
2. **The spine, as markdown headings in order**: orientation line, the answer, two-minute version, actions (already done / only you can do / needs approval), the middle, detail. Reports only; plans, decks and editors keep their own shapes.
3. **Every finding, in final wording, with its severity tier** (`[blocking]`, `[important]`, `[note]`).
4. **Visual directives inline**, because "table or diagram" is an editorial call the analysis owns: `> chart: horizontal bars, cost by service, sorted desc, values in USD`, `> diagram: flow, 6 nodes, accent on Ingest and Store`, `> callout:`, `> compare: before | after`, `> details:` for reasoning that belongs collapsed. A section with no directive renders as prose or a table at the renderer's judgement.
5. **For an editor**: the decision space (cards, columns, what a decision is), the JSON shape keyed by identifiers the user knows, and what Reset restores.

Write it at the density the artifact should have. The render step does not tighten prose; a padded content file is a padded page, so **every word of padding in the finished artifact was written here, in this step**. The density rules in `references/render.md` forbid rewriting your wording; they cannot save a padded content file. This is the only step where density is decided.

#### Density budget (numbers, not adjectives)

| Unit | Cap |
|---|---|
| Whole content file, prose words | 400 + 60 per severity-tagged finding |
| Any one `##` section | 180 |
| Any one paragraph | 55 words (about two sentences) |
| Two-minute version | 120 |
| One finding | 40 words, then `> details:` for the rest |
| Orientation | 1 line |

Banned as section headings outright: Introduction, Overview, Context, Background, Executive summary, Conclusion, Recap, Limitations, Assumptions, Caveats. The spine sections (orientation, the answer, two-minute version, actions) are required and exempt. A caveat that changes a decision goes as one line inside the section it changes, never as its own section.

**Longer reasoning is not deleted, it is moved.** `> details:` takes it out of the main scroll. Over budget means cut or move whole blocks; never reword to squeeze under.

**Run the lint before rendering, and fix what it flags:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/check_density.py" <abs path>.content.md
```

Exit 1 means over budget. Do not render a content file that fails it, and do not raise the budget instead of cutting.

#### When the artifact rests on research, the evidence comes first

For a `middle: research` artifact, or any page whose recommendation is only credible because of what the literature says, the reading order is **evidence, then recommendation**, not the reverse.

1. **State what the research actually found, in plain English, with a visual.** Effect sizes, sample sizes and study names belong here, but the section has to be readable by someone who will not click through to a single paper. One chart or diagram carrying the finding is not decoration here, it is the section.
2. **Then give the recommendation, explicitly derived from step 1**, and say which parts are the research talking and which parts are you adapting it to the user's actual constraints (schedule, commitments, what they have already told you).
3. **Then ask for whatever you still need from them** to finish the tailoring.

Leading with the recommendation and burying the evidence underneath, or interleaving the two, produces a page that reads as assertion.

### Step 2: load only the craft this artifact needs

`references/render.md` is always the entry point. Everything else is conditional, because each file you open stays in context for the rest of the session:

| File | Load when |
|---|---|
| `references/render.md` | always |
| `references/narrative.md` | the artifact is a report (has the orientation/answer/actions spine) |
| `references/charts.md` | the content file asks for a chart or a diagram |
| `references/scaffolds.md` | the page has an interactive block (editor, draggable cards, JSON round-trip) |

A report with no chart and no interaction needs render.md and narrative.md only. Opening all four is almost never right.

### Step 3: write, then verify in this order

1. Write the HTML from the content file.
2. `verify_diagrams.py <path-to.html>`: viewBox geometry only.
3. The class-coverage check (`references/render.md`): the counterpart that catches what the verifier cannot see. A verifier pass is never "it renders correctly".
4. `install_collapse_layer.py` (`--collapsible` matched to this artifact's own section and card classes, `--default` from the content header), then `install_report_nav.py` for reports.

All scripts live in `${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/` and are stdlib-only Python 3.

**Artifacts ship with no annotation or comment layer.** No Copy-comments bar, no Send-to-Claude button. Feedback on the page comes back in chat.

Do NOT open the artifact in a browser for a visual review: no screenshots, no viewport checks. The deterministic checks are the check.

### Step 4: after the file exists

Open it and, if it belongs to a tracked task, link it. **Read `references/operations.md`** for both. The one rule that must not wait: the only reason to skip opening is `$HTML_NO_OPEN` being set.

### The content file is authoritative

The HTML carries the content file's text, headings and directives, plus page chrome. A renderer that "improves" the wording has broken the contract, because the drift check greps for the content file's sentences. A main thread that leaves the wording to a renderer has broken it too, because the renderer never saw the analysis.

## Where to save output

| Caller | Default location |
|---|---|
| Ad-hoc generation (no specific skill) | `/tmp/<slug>.html` |
| `/create-plan` | `docs/plans/<YYYY-MM-DD-slug>.html` (repo), or the skill's own location |
| `/make-slides` | Skill-specified |

Default for ad-hoc: ephemeral. If the user wants to keep it, they will say so. Do not litter a repo or notes folder with one-shot HTML files. Specialised skills override this with their own conventions. Never reuse bare `triage.html` / `plan.html` / `report.html` names; always include a slug.
