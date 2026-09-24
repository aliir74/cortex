# Rendering an HTML artifact

Renderer-side craft for `how-to-html`. Loaded by whoever writes the markup (the main thread by default, a render sub-agent on the dispatch path). The dispatch protocol and save locations live in `SKILL.md`, opening and task-linking in `references/operations.md`; nothing here repeats them.

## References, and when to read them

This file holds the decisions; two on-demand files hold the lookups. Both sit one level from here, so read them directly from this file. Neither points at the other for anything you need.

- **`references/charts.md`**, before ANY chart or diagram SVG: which visual fits which data shape, inline-SVG execution rules, sizing maths and viewBox gutters, label placement, text-on-fill contrast, verifier fix recipes, canonical chart shapes (Scaffold §5), and **node/connector craft for structural diagrams (§11)** when the visual is a flow, architecture, tree or state diagram rather than a chart.
- **`references/narrative.md`**, before ANY report, analysis, review, investigation or decision artifact, and **before choosing a single section heading**: the fixed spine, the five report middles, the two-minute block, severity tiers, the connective rule. A report written without it opens cold and runs findings-by-category, which is the shape a reader cannot follow.
- **`references/scaffolds.md`**, before the page shell or an interactive block: §1 tokens + dark mode, §2 skeleton, §3 Copy-result + toast, §4 drag-drop + keyboard, §6 responsive layout, §8 report navigation, **§9 collapse layer**.

Read the relevant file *before* writing, not after: a chart written without `references/charts.md` reproduces the border-escape bug the verifier then blocks.

## Turn budget

The craft in this file is not what makes a render expensive; repeating it is. Cost scales with turn count, so three caps bound the loop. None of them lowers the standard: every mandatory check below still runs once, and the two-round stop rule under "Bounded repair" still applies on top.

- **No browser screenshots.** Rendering the artifact in a browser to capture and eyeball it is not part of the contract. Do not open the file in a browser, do not capture PNGs, do not report a perceptual review.
- **Never re-`Read` a file you just wrote.** `Write` and `Edit` fail loudly, so a clean return already means the bytes landed, and reading a 100KB artifact back costs its full length again on every remaining turn. Two reads are legitimate: after a *script* mutated the file (`install_collapse_layer.py`, `install_report_nav.py`), and when you need a span you never wrote. Both take `sed -n '<start>,<end>p'` for the range in question, never a whole-file `Read`.
- **The budget is per pass, and a revision round is a new pass.** When a revision round starts, re-verify only what you changed. Do not re-run the class-coverage check or re-read the artifact end to end.

These caps are about *redundant* turns. They never argue for folding the document into fewer, larger writes (next section).

## Write in chunks, never one monolithic Write

A whole artifact in one `Write` is thousands of output tokens, and when that call fails the model re-emits the entire document from scratch, often byte-identical, with nothing surfaced but a stalled "Retrying Write" status.

**Cap any single `Write` or `Edit` at roughly 4,000 output tokens, about 120 lines of dense HTML.** Build the artifact in passes:

1. **Skeleton first.** One `Write` carrying `<style>` (tokens, dark mode, layout), the page shell, and an empty `<section>` per planned block with its heading and `id`. No prose, no SVG. This pass must be small, because everything after it is an `Edit` against a file that already exists.
2. **One `Edit` per section**, filling a single `<section>` from the content file.
3. **Diagrams in their own `Edit`, one SVG at a time**, and never split an `Edit` inside an `<svg>` block: a verifier run on half an SVG reports coordinates that are not wrong yet.
4. **Scripts and the installers last**, unchanged (`install_collapse_layer.py`, `install_report_nav.py`).

A retried 4k-token `Edit` costs seconds; a retried monolithic `Write` costs over a minute. Chunked passes are not redundant turns, so this does not conflict with "Turn budget". If you have to choose, keep the writes chunked.

## Design principles

No house style. Choose the palette, typefaces, spacing and component shapes per artifact, to fit its content and where it will be read: a cost dashboard, a meeting prep doc and a slide deck should not look alike. What stays fixed is functional:

- **Visuals carry the content.** Tables, charts, diagrams, timelines and before/after compares are the primary vehicle wherever information is spatial, comparative or relational; prose is the fallback. See "Visuals over text" below.
- **System font fallback always.** Every stack ends in `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif` so the artifact survives offline or a web-font outage.
- **Dark mode is not optional.** Every artifact includes a `prefers-color-scheme: dark` block (Scaffold §1).
- **No animation for decoration.** Animate progress, drag feedback, and state changes (toast appear, card move). Not hovers, fades, or "welcome" intros. Honour `prefers-reduced-motion`.

### Default looks to leave out

With no design direction the model falls back on a few default styles, and a general "avoid a generic look" only swaps one default for another. Leave out all of these:

- a cream or off-white page background
- italic accent words in headings
- numbered "01 / 02 / 03" section labels
- monospace labels (eyebrows, badges, meta lines); mono is for code, paths, IDs and SVG chart text only
- pill-shaped buttons

Then look at what you chose instead. When the user rejects the replacement look, add it to this list.

### Prose density

Concise style governs the artifact's own content, not just the chat reply wrapping it. An artifact is a reference the user scans, not a document they read.

- **Every section earns its place.** No decorative "Introduction", "Overview", "Context", "Background", "Executive summary" or "Conclusion" section unless it carries information found nowhere else in the file. The spine sections defined in `references/narrative.md` (orientation, the answer, the two-minute version, actions) are **exempt: they are required, not decorative**, and a report missing them is broken regardless of how dense its findings are.
- **Say it once.** Never restate a finding as a stat card, then a paragraph, then a bullet, then a closing recap. Pick the densest form and delete the others.
- **Orient in one line, then don't restate the brief.** Every report opens with a single line naming the question, who asked it, when, and what was read. That line is a *locator*, not a preamble: without it the reader has to reconstruct what the artifact even is before anything in it means anything. Everything past that one line stays banned: re-explaining the ask, narrating how the analysis ran, summarising what is about to be said. Then lead with the answer, the recommendation, or the number.
- **Weight the findings.** A blocking finding and a minor note must not look identical. Use the three severity tiers in `references/narrative.md`; the two-minute block is built from the top tier only.
- **Two sentences per block, not five.** Where prose is right, keep it to a couple of sentences under a heading. Longer reasoning goes inside a `<details>` or a collapsible card, out of the main scroll. The §9 collapse layer already takes every section and card out of the main scroll by default, so this rule is now about the prose *inside* an open section, not about hiding a long one.
- **Caveats get one line, and only when they change a decision.** No standing "Limitations" or "Assumptions" section by reflex.
- **Table over paragraph, chart over table.** Prose is the last resort for structured content, not the default.

### Narrative spine

**Reports and analysis only** (plans, decks, verify reports and editor UIs keep their own shapes). Spec, worked examples and counter-examples: **`references/narrative.md`**, read before choosing section headings.

A report is an argument that arrives somewhere, not a container for findings. Six parts, always in this order, and only part 5 varies:

1. **Orientation**, one line: the question, who asked, when, what was read.
2. **The answer**: verdict, recommendation or number.
3. **Two-minute version**: standalone, top-tier findings only, plus the decision the user owns.
4. **Actions**: above the evidence, in three buckets (already done / only you can do / needs approval).
5. **The middle**: one of **investigation · verdict · options · research · audit**, each with its own section order.
6. **Detail**, collapsed.

Every section is collapsed by default under the §9 collapse layer, so "Detail, collapsed" is now the shipped state of the whole spine rather than a choice made for one section. What still varies is *order*: the answer and the two-minute version stay first and stay open (`KEEP_FIRST_OPEN`), because a report whose answer is behind a click has no spine at all.

Pick the middle *before* any section exists and stamp it as `<!-- report-middle: verdict -->`. Every middle section opens with one sentence saying why it follows the previous one; that connective is what makes the order visible instead of arbitrary. Install the §8 nav so the reader can place themselves: `python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/install_report_nav.py" <file> --section-root ".container" --heading "h2"` (`--check` audits the spine without editing).

### Visuals over text

**Always reach for charts and diagrams when they aid readability.** A reader learns faster from a chart than from a paragraph or a wall of numbers. For any quantitative or relational content, ask "can a visual show this in one glance?" before reaching for prose or a table of numbers.

Which visual fits which data shape is a 10-row lookup in **`references/charts.md`** (first section). Read it when you reach for a chart.

**Banned: pie / donut / sunburst charts.** They look pretty in a screenshot and are almost always the wrong choice. Humans compare angles poorly; small slices become unreadable; labels collide; nested rings (sunburst) compound the problem. For category proportions, always reach for a **horizontal bar chart** (one bar per category, sorted by value, optionally stacked with subcategory segments). The same data fits the same screen height, with proportions readable at a glance and labels that always render. A *single*-ratio progress ring is acceptable; anything categorical is not.

Stat cards still earn their place for *single, headline numbers* with no comparison. The moment there is a comparison (vs target, vs last week, vs another category), upgrade to a visual. **Chart-in-stat-card: don't.** A 140-180px card shrinks SVG text to about 10 device pixels. Use a big number plus a small meta line (`target 12 · +50% over`); charts get their own full-width section at 320-460px. Reasoning: `references/charts.md`.

Charts follow the same execution rules as diagrams and are hand-written SVG. Don't reach for Chart.js unless the dataset is genuinely large (>20 points, real time-series).

**Structural diagrams (flow, architecture, sequence, tree, state) get four extra decisions**, all detailed in `references/charts.md` §11:

- **Does it beat a paragraph?** A diagram is right for *relational* content. For a list of things, a simple before/after, or plain sequence, a table or bullets or one sentence wins. This is the one place to hold back on the visuals-over-text default.
- **Budget: 9 nodes, 12 connectors, hard cap.** Over budget means split into overview plus per-zone detail, never shrink the type. Then try deleting each node and arrow: if the diagram still says the same thing, the deletion was right.
- **Focal accent on at most 2 nodes.** Accent marks where to look first; on five nodes it marks nothing. Per diagram, choose either semantic colouring (state) or focal colouring (attention), not both.
- **Draw on a 4-unit grid.** Every coordinate, size and gap a multiple of 4 (stroke widths, radii, opacity and data-derived heights exempt). Mixed 1-unit offsets are what make a hand-written diagram read as generated.

Connectors are **orthogonal elbows with a rounded `r=8` bend, never diagonals**; arrow labels clear the line by 6-10 units over a paper-filled mask rect; connectors sharing a box edge attach at least 12 units apart. The verifier blocks all three (§11 has the elbow scaffold).

## Mobile-friendly (phone-first), mandatory

**Every artifact must be usable on a phone, not just a desktop.** Artifacts are routinely opened on a phone (shared to a chat app, opened from a notification), so a layout that only works at 1200px is broken. Phone-first is not optional, the same way dark mode is not. Design for ~390px first, then let it expand. The whole floor:

| # | Requirement |
|---|---|
| 1 | `<meta name="viewport" content="width=device-width, initial-scale=1" />`, non-negotiable (Scaffold §2 has it). Without it iOS renders at 980px and shrinks everything. |
| 2 | **No horizontal scroll, ever**, down to 360px. `html, body { overflow-x: hidden }` is the backstop, fluid widths the real fix: `max-width` + `width: 100%`, never a fixed `width: 900px`. |
| 3 | Fluid container with gutters: `.container { width: min(720px, 100% - 2rem); margin-inline: auto; }`. Text never runs edge to edge. |
| 4 | Multi-column grids (stat cards, compare, board columns) fold to one column under ~640px: prefer `repeat(auto-fit, minmax(240px, 1fr))`, plus an explicit `@media (max-width: 640px)` where needed. Before/after diffs stack vertically. |
| 5 | Touch targets at least 44x44px: buttons, link-as-button, toggles, drag handles, pills. A 24px desktop button is unhittable with a thumb. |
| 6 | Fluid type via `clamp()`: display at `clamp(1.75rem, 6vw, 3rem)`, body at 16px or more. **Form inputs at least 16px** or iOS Safari auto-zooms on focus. |
| 7 | No hover-only affordances. Touch has no hover, so anything revealed on `:hover` (tooltips, per-card buttons, hidden controls) must also be tap-reachable. |
| 8 | Wide tables: wrap in `<div style="overflow-x:auto; -webkit-overflow-scrolling:touch">`, or restructure as stacked cards under the breakpoint for 3 columns or fewer. A raw `<table>` must never set the page min-width. |
| 9 | Sticky and floating elements respect the notch: `bottom: calc(16px + env(safe-area-inset-bottom))`, plus bottom padding so a floating button can't cover the last row. |
| 10 | Charts cap at 460px (Scaffold §5), which fits phones, but check the SVG text is legible at ~340px rendered. Keep labels terse; borderline on desktop is illegible on a phone. |

**Drag-drop needs a touch path.** Native HTML5 drag events don't fire on touch, so the §4 scaffold is mouse plus keyboard only. Any custom editor shipping to a phone needs the **tap-to-move fallback** (tap a card to select, tap a column to drop, same state machine as keyboard pick-up/drop) from `references/scaffolds.md` §6. Without it the round-trip UI is dead on mobile. If an editor is genuinely desktop-only, say so on the page and don't send it to a phone.

**Verify at phone width before shipping:** ~390px and 360px, no horizontal scroll, nothing clipped, every control thumb-tappable, text legible without zoom.

## Tech stack, what's allowed

Baseline: every artifact is a **single self-contained `.html` file**. No build step, no bundler, no framework boilerplate. Inline CSS in a `<style>` block, inline JS in a `<script>` block at the end of `<body>`.

External dependencies, in this order of preference:

1. **Always OK:** Google Fonts (display/sans/mono).
2. **OK when justified:** a small chart library (Chart.js, Apache ECharts) when a real data viz is needed and a hand-drawn SVG will not do.
3. **OK for substantial complexity gain:** htmx, Alpine.js or similar, when the alternative is hundreds of lines of vanilla JS for an interactive UI.

Never: full SPA frameworks (React/Vue/Svelte), CSS frameworks (Tailwind, Bootstrap), webfont-icon kits (Font Awesome, use inline SVG instead), trackers or analytics, anything requiring a build step.

**Diagrams: always inline SVG, never Mermaid.** Mermaid's output is opaque (auto-generated IDs), hard to color-control, fails silently over `file://` in some browsers, and adds a CDN runtime dependency. Hand-written inline `<svg>` is typically under 50 lines for the structural diagrams in plans and reports, gives exact control over type and color, and dark-modes without theme hacks.

**Inline SVG execution rules** (semantic color classes, the in-SVG dark-mode block, `viewBox` over fixed sizes, `role="img"` + `aria-label`, one reusable `<marker>` for arrows) are in **`references/charts.md`**.

**Geometry is where charts go wrong, and trying harder at the maths is not the fix.** SVG text is measured in viewBox user units, so an SVG stretched wider than its viewBox scales its labels up and they overflow, silently, because dev preview is narrower than production. Two mechanisms make card-escape structurally impossible: `.chart { overflow: hidden }` clips anything painting past the card, and `verify_diagrams.py` statically checks containment. The rules that make a chart pass both (cap `.chart` at 460px, clip, budget gutters so every label lives in `[0..W, 0..H]`, card out-pads the chart) are in **`references/charts.md`**.

### Verify every diagram (mandatory)

After writing or editing ANY HTML containing a chart or diagram SVG, run the geometry verifier before considering the file done:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/verify_diagrams.py" <path-to.html>
```

Exit 0 is clean; exit 1 prints each offending element with its class number and the measured numbers. It flags seven classes. Chart geometry: (1) a label or shape falling outside `[0..W, 0..H]` (border escape), (2) a label straddling a card/panel border (reads as clipped even though containment passes). Connector craft on structural diagrams: (3) a diagonal connector segment, (4) an arrow label sitting on its own connector, (5) two connectors sharing one attach point, (6) a connector passing behind a node it does not connect, (7) two parallel connectors closer than 8 units. Repair in this order: widen the viewBox or move the label clear, re-anchor it, adjust the route, and only then shorten the wording. A label is never deleted to make geometry pass, and `overflow` never hides anything. Re-run until clean, within the two-round stop rule below. Only marker-bearing lines and paths count as connectors, so sparklines, axes and target rules are never touched. Per-class fix recipes: `references/charts.md`.

**Optional: make it automatic.** Wire the verifier as a Claude Code `PostToolUse` hook on `Write`/`Edit` of `.html` files so an out-of-bounds label cannot ship even if you forget to run it by hand. The hook just calls the command above on the written file and blocks on a non-zero exit. `--self-test` lints the scaffolds in `references/charts.md`.

**A passing verifier is NOT evidence the chart renders correctly, so also run the class-coverage check.** `verify_diagrams.py` checks label containment *inside the viewBox*. It cannot see CSS. If the Scaffold §5 chart CSS is missing or the artifact uses different token names, the geometry stays perfectly valid while the rendered chart is broken: without `.chart { max-width: 460px }` the SVG stretches to the container width and every label scales up with it (a 320-unit viewBox in an 1800px card magnifies text about 5x and clips it), and without `.c-indigo` / `.c-mint` / `.c-orange` / `.c-muted` the `fill` is never set, so **every bar renders solid black and indistinguishable**.

After writing any HTML containing a chart, assert every class the SVG uses is actually defined:

```bash
python3 - "$FILE" <<'EOF'
import re, sys
t = open(sys.argv[1]).read()
used = set(re.findall(r'class="(c-[a-z]+|chart|chart-title|target|grid|axis|lbl-on-fill)"', t))
defined = set(re.findall(r'\.(c-[a-z]+|chart|chart-title|target|grid|axis|lbl-on-fill)\s*\{', t))
defined |= set(re.findall(r'\.chart \.(\w[\w-]*)\s*\{', t))
defined |= set(re.findall(r'\.chart text\.([\w-]+)\s*\{', t))
missing = sorted(used - defined)
print("MISSING CSS:", missing or "none")
sys.exit(1 if missing else 0)
EOF
```

Non-empty output means the chart is broken regardless of what the verifier said. Fix by adding the Scaffold §5 block (`references/charts.md`), mapped onto **the artifact's own token names** — check `:root` first, since a template may define `--card` rather than `--paper`, or a `--line` too faint to use for `.c-muted`.

### Bounded repair: stop after two rounds without a new minimum

Track the violation count per round. When two consecutive rounds fail to beat the best count seen before them, stop tweaking geometry. Split the diagram into an overview plus per-zone detail, drop it to a table, or report the remaining violations to the user as unresolved. Track the count yourself; the verifier does not stop you.

## Custom editor pattern, the round-trip

When the artifact's job is "the user manipulates something and the result feeds back to Claude", the shape is: a UI that fits the decision space (cards, columns, sliders, drag-drop, toggles); a persistent **"Copy result" button** (sticky header or floating bottom-right) that stays disabled until one decision exists, shows a live counter, and serialises to **JSON only**; a **Cmd+Enter / Ctrl+Enter shortcut** for the same action, with the hint printed on the button; a ~1800ms toast; and a **Reset** that restores the initial state without reloading.

**The copy itself is `execCommand`-first.** `navigator.clipboard.writeText` can hang forever on a `file://` artifact, neither resolving nor rejecting, so a bare `.catch()` fallback never runs and the copy dies with no feedback at all. Copy synchronously via a hidden textarea + `document.execCommand("copy")`, keep the async API as a second attempt behind a ~1200ms timeout, and make the last-resort fallback an **in-page selectable panel, never `window.prompt`** (Chrome silently blocks dialogs raised without user activation, and a pending dialog freezes the page). Call the copy function inline from the keydown handler, never through `copyBtn.click()`: a synthetic click loses the user gesture. Scaffold §3 has the working version.

**JSON shape:** keys are the identifier the user knows (filenames, task IDs, person names, not opaque hashes), values are the decision, flat where possible. The point is closing the loop in seconds rather than minutes. Mechanism: `references/scaffolds.md` §3 and §4.

Anti-patterns: auto-saving to localStorage instead of an explicit Copy (ghost state), downloading `.json` files (slower, litters the disk), printing JSON in the page for manual selection (the clipboard API exists).

## Collapse layer, default for every read-mostly artifact

**Every section and every card collapses, and ships collapsed.** Install it on every report,
analysis, dashboard, plan, research synthesis, prep doc and verification report:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/install_collapse_layer.py" <file> \
    --collapsible "section, .card" --default collapsed
```

Spec, per-artifact constants, per-element overrides and mechanics: **`references/scaffolds.md`
Scaffold §9**, read before installing.

**Pass `--alias mono=` and `--alias sans=` to EVERY installer you run, whenever the artifact
defines its own font tokens, or they silently replace them with generic stacks.** Both
`install_collapse_layer.py` and `install_report_nav.py` carry an identical
`DEFAULT_ALIASES` seeding `mono` and `sans` with generic values, both do
`aliases = dict(DEFAULT_ALIASES)` so user `--alias` pairs override only individual keys, and
both emit the result from `alias_css` as a `:root` block appended *after* the artifact's own
`<style>`. Equal specificity, later in the document, so **the last installer to run decides the
font**, and any installer you did not pass aliases to is a generic-stack landmine.

The failure is silent and invisible to the deterministic checks: a custom typeface reverts to
`ui-monospace` / `-apple-system` with no error, and the file ends up with several `--mono` definitions in
source order:

```
1  --mono: "JetBrains Mono", ...   <- the artifact's own token
2  --mono: ui-monospace, ...       <- an installer run without aliases
3  --mono: "JetBrains Mono", ...   <- the next installer, aliased correctly
```

Whichever installer runs last decides the font, so one un-aliased run anywhere in the sequence is
a landmine.

```bash
# Pass these to EVERY installer you run, and again on --upgrade,
# which re-emits the alias block.
--alias mono='<this artifact's own --mono stack>' \
--alias sans='<this artifact's own --sans stack>'
```

Confirm by listing every definition in source order, not by grepping for the typeface name:
`grep -oE '\-\-mono:[^;]*;' <file> | nl`. The last line is the one that renders.


**Order matters: collapse layer first, then the nav.** The collapse layer rewrites headings and
moves content into `.cx-body` wrappers, so the nav has to see the final structure.

**Set `--default expanded` only for an artifact genuinely read in one pass** — a deck, a
one-screen dashboard, a three-section page. That still installs the affordance; it only changes
the initial state. It is never the answer to "this report feels hidden": the opening section
stays open by default (`KEEP_FIRST_OPEN`), and that is where the orientation line and the answer
live.

**A collapsed section still says how much is inside** (`4 items`, `12 rows`). If a section's
heading does not survive being read alone, with only a count under it, the heading is the
problem, not the collapsing.

## No annotation layer

**Artifacts ship clean.** No Copy-comments bar, no Send-to-Claude button, no `+` affordances on blocks, no highlight machinery, no relay. Feedback on the page comes back in chat; answer it there.

## Accessibility floor

These are personal tools but the floor is still:

- **Semantic HTML.** Buttons are `<button>`, links are `<a>`, form fields have `<label>`. Never `<div onclick>`.
- **Heading hierarchy.** One `<h1>` per artifact, nested `<h2>`/`<h3>` following logically, no skipped levels.
- **Keyboard nav for interactive UIs.** Tab through buttons and cards. For drag-drop also support Space/Enter to pick up, arrow keys to move between columns, Space/Enter to drop, Escape to cancel (Scaffold §4).
- **Focus visible.** Do not blanket-disable `outline`. A customised focus style stays strong (a 2px ring in the accent color is fine).
- **Reduced motion.** Wrap non-essential transitions in `@media (prefers-reduced-motion: no-preference)`.

Full WCAG AA is not required for personal artifacts. If the output will be shared externally (slide decks, public reports), add ARIA labels and check colour contrast too.

## Anti-patterns

- **Don't ship without dark mode.** No `prefers-color-scheme: dark` block means the artifact looks broken on a dark OS.
- **Don't ship a desktop-only layout.** Fixed widths, grids that don't collapse, sub-44px targets, hover-only controls, or horizontal scroll at 390px is a broken artifact.
- **Don't draw diagonal connectors, or crowd a diagram past 9 nodes.** Elbows and a split diagram, respectively. The verifier blocks the first; the second is on you.
- **Don't write multi-paragraph CSS comments.** Terse, only when WHY is non-obvious.
- **Don't open a report with the findings.** Without the one-line orientation the reader has to reconstruct what the artifact is before anything in it means anything. A verdict answers a question they cannot see.
- **Don't order report sections by category.** Findings-by-category is what produces a pile instead of an argument. The middle's order comes from the chosen archetype, and every section says why it follows the previous one.
- **Don't bury the actions at the bottom.** They go above the evidence. The evidence exists to justify them, so a reader who accepts the answer never has to reach it.
- **Don't pad the artifact with narration.** Intro/overview/conclusion sections, a recap of the brief, the same finding in three forms, a reflexive limitations block. Concise style applies to file content, not only chat (see "Prose density").
- **Don't add settings panels, theme switchers, or "preferences"** unless the artifact is genuinely reused. Pick a default and ship it.
- **Don't ship a copy button that only calls `navigator.clipboard.writeText`, and don't fall back to `window.prompt`.** On `file://` the promise can hang, so the user gets silence, and a native dialog can freeze the page. `execCommand` first, in-page panel last.
- **Don't ship a report without the collapse layer, and don't reach for `--default expanded` to "make it readable".** Every section and card ships collapsed; the opening section stays open, which is where the orientation line and the answer are. If a collapsed heading reads as meaningless with only its item count under it, rewrite the heading.
- **Don't add a bare `cx-`-adjacent class, or let a guard match the layer's own spans.** Same silent CSS failure as the `cl-` namespace, and it has already happened once inside this layer: `.cx-head > span { border: 0 }` out-specified `.cx-chevron`, so every disclosure chevron rendered with no border and the page merely looked oddly indented. Deterministic checks pass; only a rendered view shows it.
- **Don't embed user content in `<script>` without escaping.** Anything from the filesystem (titles, paths, summaries) goes through `JSON.stringify` or HTML-escaping first.
- **Don't `open` the file from inside a skill wrapped by a chain** (e.g. a plan-then-execute wrapper). The outer skill controls opening; the inner respects `$HTML_NO_OPEN`.
- **Don't emit the whole artifact in one `Write`.** It is re-emitted in full on every retry. Skeleton first, then one `Edit` per section, roughly 4k tokens a pass. See "Write in chunks".
- **Don't re-`Read` an artifact you just wrote or edited.** `Write` and `Edit` error on failure, so a clean return is already the confirmation, and a whole-file read of a 100KB artifact is charged again on every remaining turn. Read a range with `sed -n` when a script changed the file under you; otherwise hold your own output.
- **Don't open the artifact in a browser to look at it.** No browser render pass, no screenshots, no viewport checks. The deterministic verifiers are the whole check.
- **Don't re-verify the whole artifact on a revision round.** Answering a comment touches one block. Re-running class coverage and a full re-read across the untouched remainder costs several times a normal render and finds nothing.
- **Don't reuse `triage.html` / `plan.html` / `report.html` names.** Always include a slug so generated files don't clobber each other.

## Canonical examples

When a scaffold is not enough, read the `create-plan` skill's `templates/plan-template.html` (editorial layout, progress ring, collapsible task cards, side-by-side compare, print stylesheet) or the `make-slides` skill (keyboard-navigable deck), if installed.

## Rationalizations (renderer side)

| Excuse | Reality |
|---|---|
| "The diagram verifier passed, so the chart renders" | The verifier checks viewBox containment. It cannot see CSS. Without the §5 chart block every bar renders solid black and the SVG stretches its labels, with the verifier green throughout. Run the class-coverage check too. |
| "The verdict is in the hero, so the reader is oriented" | A verdict answers a question the reader cannot see. A report that opens with a verdict and nine category sections leaves the reader unable to tell what it is or how to read it. One line naming the question, who asked and what was read is the fix, and it is required (`references/narrative.md`). |
| "This report doesn't fit any of the five middles" | The fallback covers it: Options if a decision is pending, Audit otherwise. Inventing a sixth shape silently is the drift the archetypes exist to prevent. Add one deliberately, or use the fallback. |
| "I edited the file, so I should read it back to confirm" | `Edit` fails loudly; a clean return IS the confirmation. The read-back is pure cost, charged again on every remaining turn. Use `sed -n` for a range when a script changed the file under you. |
| "This is a revision round, so I should re-verify the artifact" | Re-verify what you changed. Re-verifying and re-reading the whole file every round costs several times a normal render and finds nothing in the parts nothing touched. |
| "One `Write` is fewer turns than six `Edit`s, so it is cheaper" | Only if it succeeds. It re-emits the entire document on failure, and retries are invisible. Six 4k `Edit`s cost five extra turns and bound a retry to seconds. |
