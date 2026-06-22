---
name: how-to-html
description: Use whenever generating or substantially editing an HTML file — implementation plans, reports, dashboards, custom-editor UIs, slides, anything written to a `.html` file. Covers when to reach for HTML over markdown, design principles, allowed tech stack, the custom-editor round-trip pattern, an accessibility floor, and a bundled diagram verifier. SKIP for trivial HTML fragments under ~5KB or files inside `node_modules`/`dist`/`build`/`.git`.
---

# How to HTML

A meta-skill for any HTML-generating workflow (implementation plans, reports, dashboards, custom editors, slide decks) and for ad-hoc HTML generation. Based on the spatial-information argument from [thariqs' "The Unreasonable Effectiveness of HTML"](https://thariqs.github.io/html-effectiveness/).

The core claim: HTML is the right output format whenever the information has spatial structure (diffs, call graphs, timelines, before/after, dashboards, draggable cards). Markdown flattens spatial relationships into prose. The other half: custom editors close the loop — Claude generates a UI, the user manipulates it, the result round-trips back as JSON, the iteration cycle compresses from minutes to seconds.

## When to reach for HTML

| Reach for HTML | Stay in markdown |
|---|---|
| Implementation plans with phases + progress | Single-task plans, quick notes |
| Reports with charts, status pills, timelines | Status updates that grep well |
| Dashboards (cost, audit, PR babysit) | Logs, journals, anything searched later |
| Custom editors (triage, prioritize, build) | Decisions captured once and filed |
| Side-by-side comparisons (before/after, diff annotations) | Two paragraphs of prose |
| Slide decks | README-style docs |
| Diagrams + explanations together | Plain explanations |

Default to markdown. Reach for HTML when the information is *spatial* (positions relative to each other matter), *interactive* (the user needs to click/drag/toggle), or *dimensional* (multiple parallel attributes per item that compare visually). If the output will be grepped, version-controlled as text, or linked from other docs later, markdown wins regardless.

## Design principles

This skill does NOT enforce a single palette/font system — every artifact should fit its content. But these principles apply across all outputs:

**Restraint.** Limit each artifact to 3 colors max plus neutrals. Pick one accent and stick to it for the dominant interactive element (buttons, links, progress fills); use 1–2 secondary colors for status (success/warn/danger) only. No gradients unless they carry meaning. No drop-shadows on text. No more than two type sizes for body content (one for prose, one for meta/labels).

**Warm neutrals.** Pure white (`#FFFFFF`) and pure black (`#000000`) feel clinical. Prefer warm cream backgrounds (e.g. `#F5F4EF`, `#FAFAF7`) and near-black ink (`#0A0A0A`, `#181818`) in light mode. Dark mode should be a near-black with slight blue/warmth, not `#000`.

**Type matches purpose.** Editorial serifs (e.g. Instrument Serif, Source Serif, Crimson) for display headings and prose summaries that earn attention. A clean sans (e.g. Inter, IBM Plex Sans, system-ui) for body and UI chrome. A monospace (e.g. JetBrains Mono, IBM Plex Mono, ui-monospace) for code, file paths, IDs, timestamps, badges. Don't mix two serifs or two sans-serifs in one artifact.

**Spatial hierarchy.** Hero → section → block → card → field, with each level marked by a clear scale jump (1.6×–2× type size, or a hard rule). The reader should locate themselves in the document at any depth without reading.

**System font fallback always.** Every font stack must end in a system fallback (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`) so the artifact is usable offline or when fonts.googleapis.com is down. Don't ship without it.

**Dark mode is not optional.** Every artifact must include a `prefers-color-scheme: dark` block. See [scaffold §1](#scaffold-1-css-tokens--dark-mode) below.

**No animation for decoration.** Animate progress bars, drag feedback, and state changes (toast appear, card move). Don't animate hovers, fades, or "welcome" intros. Honour `prefers-reduced-motion`.

**Visuals over text. Always reach for charts and diagrams when they aid readability.** A reader takes in a chart faster than a paragraph or a wall of numbers. The default for any quantitative or relational content is: ask "can a visual show this in one glance?" before reaching for prose or a table-of-numbers.

| Data shape | Preferred visual | Avoid |
|---|---|---|
| 2-5 categorical proportions (one whole) | Stacked horizontal bar | **Pie / donut / sunburst** (see ban below) |
| 6+ categories (any distribution) | Sorted horizontal bar chart | Pie / donut / sunburst, treemap |
| Counts vs target (e.g. quota, SLO) | Bar with target rule line | Plain number with text aside |
| Time series (3+ points) | Sparkline or mini line chart | Comma-separated values |
| Comparison (A vs B, before/after) | Side-by-side bars or diff blocks | Two paragraphs |
| Single progress / ratio | Progress bar (or ring if `progress` framing helps) | "57%" alone |
| Process or flow (3+ steps) | Inline-SVG boxes + arrows | Numbered prose |
| Hierarchy / containment | Inline-SVG tree or nested rects | Indented bullets |
| Distribution across many bins | Horizontal bar chart | Long table |
| Schedule / timeline | Gantt-style bars on a date axis | Date-prefixed list |

**Banned: pie / donut / sunburst charts.** They look pretty in a screenshot and are almost always the wrong choice. Humans compare angles poorly; small slices become unreadable; labels collide; nested rings (sunburst) compound the problem. For category proportions, always reach for a **horizontal bar chart** (one bar per category, sorted by value, optionally stacked with subcategory segments). The same data fits the same screen height, with proportions readable at a glance and labels that always render. A *single*-ratio progress ring is acceptable; anything categorical is not.

Stat cards still earn their place for *single, headline numbers* where the trend is "today's count" with no comparison. But the moment there's a comparison (vs target, vs last week, vs other category), upgrade to a visual.

Charts must obey the same rules as diagrams (see Inline SVG patterns under Tech stack): semantic colors, dark-mode block, `viewBox` scaling, `role="img"` + `aria-label`. Hand-write the SVG. Don't reach for Chart.js unless the dataset is large enough that hand-drawing becomes ridiculous (>20 data points, real time-series). See [scaffold §5](#scaffold-5-inline-svg-charts) for canonical chart shapes.

## Tech stack — what's allowed

Baseline: every artifact is a **single self-contained `.html` file**. No build step, no bundler, no framework boilerplate. Inline CSS in a `<style>` block, inline JS in a `<script>` block at the end of `<body>`.

External dependencies, allowed in this order of preference:

1. **Always OK**: Google Fonts (display/sans/mono).
2. **OK when justified**: A small chart library (Chart.js, Apache ECharts) when a real data viz is needed and a hand-drawn SVG won't do.
3. **OK for substantial complexity gain**: htmx, Alpine.js, or a similar small lib when the alternative is hundreds of lines of vanilla JS for an interactive UI.

Never: full SPA frameworks (React/Vue/Svelte), CSS frameworks (Tailwind, Bootstrap), webfont-icon kits (Font Awesome — use inline SVG instead), trackers/analytics, anything requiring a build step.

**Diagrams: always inline SVG, never Mermaid.** Mermaid's rendered output is opaque (auto-generated SVG with arbitrary IDs), hard to color-control, fails silently over `file://` in some browsers, and adds a CDN runtime dependency. Hand-write inline `<svg>` instead — it's typically <50 lines for the structural diagrams that appear in plans/reports, gives you exact control over typography and color, and respects dark mode without theme-switching hacks.

**Inline SVG patterns:**
- Wrap colors in an internal `<style>` block with classes (`.box-tier1`, `.lbl-title`, etc.) — never inline `fill="..."` attributes that can't dark-mode-flip.
- Always include a `@media (prefers-color-scheme: dark)` block inside the SVG `<style>` overriding fills/strokes/text. Without this the diagram is unreadable on dark wallpaper.
- **Colors must carry semantic meaning**, not be decorative palette picks. Mint = positive/auto/safe, amber/warn = needs attention/routed, pink/danger = problem/split candidate, indigo = primary/entry, purple = on-demand/deferred. Use the same color for the same meaning across an artifact's diagrams.
- Use `viewBox` not fixed `width`/`height` so the SVG scales with its container.
- Add `role="img"` and `aria-label="<one-sentence description>"` for screen readers.
- For arrows, define one `<marker>` in `<defs>` and reuse it via `marker-end="url(#arrow)"`.

> **The border bug is solved by two mechanisms, not by trying harder at the math below.** (a) `.chart { overflow: hidden }` (scaffold §5) clips anything that would paint past the card — so a coordinate mistake can never *look* like a label hanging off the box. (b) the bundled `verify_diagrams.py` (see [Verify every diagram](#verify-every-diagram) below) statically checks every label/shape is inside its viewBox. The sizing rules below are how you make charts that pass the verifier *and* don't get clipped; they are no longer the last line of defense.

**SVG chart sizing — non-negotiable defaults.** SVG text uses *user units* (viewBox coordinates), not CSS pixels. When the SVG container stretches wider than the viewBox, text scales up proportionally. A `font-size: 11` label inside a `viewBox="0 0 320 200"` SVG rendered at 1200px wide becomes ~41px — labels overflow, overlap bars, and overlap each other. This happens silently because dev preview is usually narrower than production layouts (full-width container, mobile breakpoint collapsing a 2-col grid to 1-col, etc.). Rules to prevent this every time:

1. **Always cap `.chart { max-width: 460px; margin: 0 auto; }`.** Charts are designed for ~320–480 user-unit viewBoxes; let them sit at that physical size and don't stretch. Center inside the card.
2. **Always clip: `.chart { overflow: hidden; }`** (the scaffold §5 default). SVG clips at its box by default; the old advice to set `overflow: visible` was the *cause* of the recurring "label hanging off the card" bug — it let content placed past the viewBox paint outside the parent card. Clipping makes card-escape structurally impossible. The cost is that a mis-placed label gets cut off instead of escaping — which the verifier catches before you ship, so a well-formed chart is never actually clipped.

3. **Budget gutters INSIDE the viewBox so every label lives within `[0..W, 0..H]`.** Pick the viewBox so it already contains the labels, then no spill is possible. Concretely:
   - **Left gutter** ≥ the widest left-hand (category) label. If names are anchored `text-anchor="end"` at `x=L`, set `L` ≥ widest-label-width (~6.5 units/char at font-size 11) so the text runs from `0` to `L`, never negative. "annelier18" (10 chars) ≈ 65 units, so `L` ≥ 70 and bars start at ~`L+8`.
   - **Right gutter** ≥ the widest value/end label. If the longest bar ends at `x=E` and carries a value label, that label runs from `E+6` to `E+6+labelWidth`; the viewBox width `W` must be ≥ that end. For a stacked bar, account for the *outermost* segment's trailing label, not the bar.
   - **Top/bottom gutters** for value labels above bars and category labels below the baseline (descenders need ~4 units), plus room for a legend row if it lives inside the SVG.
   - Rule of thumb: `W = leftGutter + barArea + rightGutter`, and verify the rightmost text's end ≤ `W` and the leftmost text's start ≥ `0`. If a label would cross a boundary, widen the viewBox or shorten the label, do not lean on overflow.

4. **The card must out-pad the chart.** The parent card needs `padding` ≥ a few px and the chart's `max-width` must fit inside `card-width − 2·padding`. Combined with rule 2 (clip) and rule 3 (nothing outside the viewBox) this makes card escape impossible by construction, not by hand-checking.

### Verify every diagram

After writing or editing ANY HTML that contains a chart/diagram SVG, run the bundled geometry verifier before considering the file done:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/verify_diagrams.py" <path-to.html>
```

It parses every `<svg>` that has a `viewBox` and contains text (i.e. every chart/diagram), accounts for group `translate()` transforms and `text-anchor`, estimates each label's width, and reports any text/rect/line/circle/polyline whose extent falls outside `[0..W, 0..H]` — the exact condition that produces the border-escape bug. Exit 0 = clean, exit 1 = violations printed with the offending element and the numbers. Fix by widening the viewBox, shortening the label, or re-anchoring it (never by leaning on overflow), then re-run until clean. The deterministic `overflow: hidden` clip (rule 2) is the second layer: even a violation the estimator under-counts is clipped at the card rather than painted outside it.

Run `python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/verify_diagrams.py" --self-test` to lint the scaffolds in this file.

> **Optional: make it automatic.** Wire the verifier as a Claude Code `PostToolUse` hook on `Write`/`Edit` of `.html` files so a diagram with an out-of-bounds label can't ship even if you forget to run it by hand. The hook just calls the command above on the written file and blocks on a non-zero exit.

**Label-placement rules to prevent overlap:**
- **Text labels go in the long axis of free space.** For column/bar charts, put value labels ABOVE the bar (not beside it) and category labels BELOW the baseline. Putting a label beside a bar wastes the chart's widest dimension on text.
- **Threshold / reference-line labels go at the TOP of the chart, centered, above all bars** — never on the same y-coordinate as bar value labels. If a dashed threshold line is at y=60, the value labels for bars touching that line will be at y≈52 (just above the bar top). Putting threshold text at y=36 with text-anchor="end" places it in the same horizontal stripe → guaranteed overlap when the rightmost bar reaches the threshold. Move the threshold label to its own band (y=14, centered) and add ~30 user units of viewBox top-padding for it.
- **Budget ~6.5 user units per character at font-size 11** when planning label positions. "threshold · 5 FTEs" (18 chars) needs ~117 user units; an anchor at x=306 text-anchor="end" places it from x=189 to x=306. Either shorten the label or give it its own row.
- **Keep in-chart text terse.** Full descriptions go in the position pill / caption / aria-label, not inside the SVG. Inside the chart: numbers, short categories, axis ticks, one-line threshold marker. Anything longer goes outside.
- **Stacked bars: label every segment, never the bar's end.** A value anchored at a stacked bar's right edge reads as the total and silently swallows the segments before it. Label each segment in place (or in the legend) instead. See the stacked-bar scaffold in §5 for the full rule and litmus test.
- **Verify by resizing.** After writing a chart, mentally (or actually) resize the browser to the widest expected breakpoint and check that (a) no text overlaps another element, (b) nothing clips at the viewBox edge, and (c) no label or shape extends past the parent card's edge. The widest breakpoint is where edge labels escape the card, so check there, not just at dev width.

**Text-on-colored-bar contrast — non-negotiable:**
- When placing a `<text>` element *inside* a colored `<rect>` (stacked bars, multi-bar value labels, segment percentages), the chart's CSS `.chart text { fill: var(--muted); }` rule will paint it in a low-contrast grey unless you override. The `fill="white"` HTML attribute is **defeated by the CSS class selector** (CSS wins over presentation attributes for `fill`).
- **Always use `class="lbl-on-fill"` for in-segment text labels.** It sources from `var(--paper)` — white in light mode, dark in dark mode. **Critical:** the §5 rule is defined as `.chart text.lbl-on-fill` (specificity 0,2,1), NOT a bare `.lbl-on-fill` (0,1,0) — a bare class loses to `.chart text` (0,1,1) and the label silently renders muted grey on the colored fill. If you copy the class into an artifact, copy the qualified selector with it. Inline `style="fill: white"` also works but doesn't dark-mode-flip.
- White-on-fill meets AA on `c-indigo` and `c-pink` but not on `c-mint` / `c-orange` in light mode (mint and amber are too light). For those, place labels externally (above or below the bar) instead of in-segment.
- For text *outside* bars (axis labels, category labels below baseline), leave the default `var(--muted)` — that's fine on the card background.

**Value labels above bars need viewBox top padding:**
- A bar from `y=12` to `y=100` (height 88) with a value label at `y=8 dy=8` (baseline y=16) means the text's bottom edge sits on top of the bar — the descender of "2" or "g" gets clipped behind the bar. The label looks "cut off" even though the text is technically there.
- **Always pad the viewBox top by at least the text height (~14 user units at font-size 11–12) when value labels go above bars.** Use `viewBox="0 0 W H+20"` and start bars at `y=24`+ to leave a clean band for labels at `y=12`–`y=20`. Don't squeeze the label into the first 8 user units of the viewBox.
- Same lesson for the bottom: category labels below the baseline at `y=baseline+14` need viewBox bottom-padding so descenders ("p", "g", "y") don't clip.

**Chart-in-stat-card: don't.** Stat cards are typically 140–180px wide. Cramming a `viewBox=160x72` chart into a 140px card shrinks all SVG text to ~10 device pixels — barely legible. **Stat cards with comparisons should use a big number + a small text meta line (`target 12 · +50% over`)**, not a tiny chart. Reserve charts for their own full-width sections where the SVG can breathe at 320–460px wide. If a stat card really needs a sparkline, give it `min-height: 80px` and don't add extra `<text>` labels — let the sparkline shape carry the meaning.

## Custom editor pattern — THE round-trip

When the artifact's job is "the user manipulates something and the result feeds back to Claude", use this exact shape:

1. **The UI**: cards, columns, sliders, drag-drop, toggles, whatever fits the decision space.
2. **A persistent "Copy result" button**, sticky in the header or floating bottom-right, that:
   - Is disabled until at least one decision has been made
   - Shows a live counter ("3 decided" → "47 decided") so progress is visible
   - On click: serialises decisions to **JSON only** (no XML, no CSV, no custom format), calls `navigator.clipboard.writeText(text)`, shows a toast
3. **A toast** that appears for ~1800ms confirming "Copied N items — paste into chat".
4. **Fallback**: if `navigator.clipboard` fails (older browsers, file:// in some setups), `window.prompt("Copy this JSON manually:", text)` so the user can still grab the result.
5. **Reset button** that returns the UI to its initial state without reloading the page.
6. **JSON shape**: keys should be the natural identifier the user knows about (filenames, task IDs, person names — not opaque hashes). Values should be the decision (a string, a number, a small object). Keep it flat where possible.

The whole point is closing the loop in seconds rather than minutes. See [scaffold §3](#scaffold-3-copy-result--toast) below.

Anti-patterns: auto-saving to localStorage instead of explicit Copy (creates ghost state), download .json files (slower round-trip, leaves litter on disk), printing JSON inside the page for manual selection (clipboard API exists, use it).

## Accessibility floor

Even for throwaway personal tools, the floor is:

- **Semantic HTML.** Buttons are `<button>`, links are `<a>`, form fields have `<label>`. Don't `<div onclick>`.
- **Heading hierarchy.** Single `<h1>` per artifact, nested `<h2>`/`<h3>` follow logically. No skipping levels.
- **Keyboard nav for interactive UIs.** Tab through buttons and cards. For drag-drop, also support: Space/Enter to pick up a card, arrow keys to move between columns, Space/Enter to drop, Escape to cancel. See [scaffold §4](#scaffold-4-drag-drop-with-keyboard-support).
- **Focus visible.** Don't blanket-disable `outline`. If you customise focus styling, keep it strong (2px ring in the accent color is fine).
- **Reduced motion.** Wrap non-essential transitions in `@media (prefers-reduced-motion: no-preference)`.

Full WCAG AA isn't required for personal artifacts. If the output will be shared externally (slide decks, public reports), apply ARIA labels and check colour contrast in addition.

## Where to save output

| Caller | Default location |
|---|---|
| Ad-hoc generation (no specific skill) | `$CLAUDE_JOB_DIR/<slug>.html` if set, else `/tmp/<slug>.html` |
| Inside a repo, tied to work | A docs/output dir your repo conventions define (e.g. `docs/plans/<YYYY-MM-DD-slug>.html`) |
| A skill with its own convention | Whatever that skill specifies |

Default for ad-hoc: ephemeral. If the user wants to keep it, they'll say so. Don't litter the working tree with one-shot HTML files. Specialised skills override this with their own conventions. Defer to the repo's `CLAUDE.md` for project-specific output paths rather than hardcoding any here.

## Link the artifact back to its work

A persistent HTML artifact (plan, report, deck) is only useful if it's discoverable from the work it was generated for. When the artifact belongs to a specific task, issue, or PR, link to it from wherever that work is tracked — the issue body, the PR description, the task line in your tracker — using whatever link format that surface understands.

**Only link when a related item actually exists.** If the artifact wasn't generated for a specific tracked item, don't invent one — just leave the file at its path. Don't append a link to an unrelated task. Defer to the repo's `CLAUDE.md` for the project's own linking convention.

## Auto-open

After writing, open the file in the default browser so the user sees it immediately. Skip when `$HTML_NO_OPEN` is set (background sessions, batch jobs, chained skills that handle opening themselves).

```bash
# macOS: open · Linux: xdg-open
[[ -z "$HTML_NO_OPEN" ]] && { command -v open >/dev/null && open "$PATH_TO_HTML" || xdg-open "$PATH_TO_HTML"; }
```

## Scaffolds

Copy-modify these. They're the canonical shapes — vary the values, not the structure.

### Scaffold §1: CSS tokens + dark mode

```html
<style>
  :root {
    /* Neutrals — warm */
    --bg: #F5F4EF;
    --ink: #0A0A0A;
    --ink-2: #5A5A55;
    --paper: #FFFFFF;
    --rule: rgba(10,10,10,0.10);
    --rule-2: rgba(10,10,10,0.18);

    /* Accents — pick what fits the artifact */
    --accent: #5856D6;    /* primary interactive */
    --success: #00C781;
    --warn: #FFB020;
    --danger: #E8437F;

    /* Type */
    --display: "Instrument Serif", Georgia, serif;
    --sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;

    /* Surface */
    --shadow: 0 1px 0 rgba(0,0,0,0.04), 0 8px 24px -12px rgba(10,10,10,0.10);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0F1014;
      --ink: #ECECEC;
      --ink-2: #9B9B9B;
      --paper: #181920;
      --rule: rgba(255,255,255,0.10);
      --rule-2: rgba(255,255,255,0.18);
      --shadow: 0 1px 0 rgba(0,0,0,0.4), 0 8px 24px -12px rgba(0,0,0,0.6);
    }
  }
  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
  }
</style>
```

### Scaffold §2: HTML skeleton

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{TITLE}}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <!-- <style> from Scaffold §1 -->
</head>
<body>
  <main class="container">
    <!-- artifact -->
  </main>
  <script>
    // interactive behaviour
  </script>
</body>
</html>
```

### Scaffold §3: Copy result + toast

```html
<button class="btn primary" id="copy" disabled>
  Copy result · <span id="decided-count">0</span> decided
</button>
<div class="toast" id="toast">Copied to clipboard</div>

<style>
  .toast {
    position: fixed; bottom: 32px; left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: var(--ink); color: var(--paper);
    padding: 12px 20px; border-radius: 999px;
    font-family: var(--mono); font-size: 12px;
    opacity: 0; pointer-events: none;
    transition: opacity 0.2s, transform 0.2s;
    z-index: 1000;
  }
  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
</style>

<script>
  let toastTimer;
  function showToast(msg) {
    const t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 1800);
  }

  function buildResult() {
    // Return a plain object keyed by natural IDs. Override per artifact.
    const result = {};
    document.querySelectorAll("[data-decision]").forEach((el) => {
      result[el.dataset.id] = el.dataset.decision;
    });
    return result;
  }

  // Call this from your decision handler (click, drop, toggle, etc.) every time a decision is added, changed, or removed so the counter and button enabled state stay in sync.
  function refreshCopyState() {
    const n = document.querySelectorAll("[data-decision]").length;
    document.getElementById("decided-count").textContent = n;
    document.getElementById("copy").disabled = n === 0;
  }

  document.getElementById("copy").addEventListener("click", async () => {
    const result = buildResult();
    const text = JSON.stringify(result, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      showToast(`Copied ${Object.keys(result).length} items, paste into chat`);
    } catch (err) {
      window.prompt("Copy this JSON manually:", text);
    }
  });
</script>
```

### Scaffold §4: Drag-drop with keyboard support

Assumes the artifact defines `.btn`, `.btn.primary`, `.card`, `.card.dragging`, `.card.picked-up`, `.column`, `.column.drop-target`, and a `[data-cards]` wrapper inside each column for the card list — the scaffold targets these classes but doesn't style them.

```html
<script>
  // Helper: get the card-list container inside a column. Falls back to the column itself if no [data-cards] wrapper exists.
  const cardsContainer = (col) => col.querySelector("[data-cards]") ?? col;

  // Mouse drag-drop
  document.querySelectorAll(".card").forEach((card) => {
    card.setAttribute("draggable", "true");
    card.addEventListener("dragstart", (e) => {
      card.classList.add("dragging");
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", card.dataset.id);
    });
    card.addEventListener("dragend", () => card.classList.remove("dragging"));
  });

  document.querySelectorAll(".column").forEach((col) => {
    // Make columns themselves focusable so keyboard nav can reach empty ones.
    col.tabIndex = -1;
    col.addEventListener("dragover", (e) => { e.preventDefault(); col.classList.add("drop-target"); });
    col.addEventListener("dragleave", () => col.classList.remove("drop-target"));
    col.addEventListener("drop", (e) => {
      e.preventDefault();
      col.classList.remove("drop-target");
      const dragging = document.querySelector(".card.dragging");
      if (dragging) cardsContainer(col).appendChild(dragging);
    });
  });

  // Keyboard nav: focus a card, Space picks it up, arrow keys move between columns, Space drops, Esc cancels.
  let pickedUp = null;
  document.addEventListener("keydown", (e) => {
    const focused = document.activeElement;
    const card = focused?.closest?.(".card");

    if (e.key === " " && (card || focused?.classList?.contains?.("column"))) {
      e.preventDefault();
      if (!pickedUp && card) {
        pickedUp = card;
        card.classList.add("picked-up");
      } else if (pickedUp) {
        const col = focused.closest?.(".column") ?? (focused?.classList?.contains?.("column") ? focused : null);
        if (col) cardsContainer(col).appendChild(pickedUp);
        pickedUp.classList.remove("picked-up");
        pickedUp.focus();  // keep focus on the moved card so the user can continue interacting with it
        pickedUp = null;
      }
    }
    if (e.key === "Escape" && pickedUp) {
      pickedUp.classList.remove("picked-up");
      pickedUp = null;
    }
    if (pickedUp && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
      e.preventDefault();
      const cols = [...document.querySelectorAll(".column")];
      const current = cols.findIndex((c) => c.contains(document.activeElement));
      const next = cols[current + (e.key === "ArrowRight" ? 1 : -1)];
      // Focus the column itself so empty columns are reachable.
      if (next) next.focus();
    }
  });

  // Make cards focusable
  document.querySelectorAll(".card").forEach((c) => c.tabIndex = 0);
</script>
```

### Scaffold §5: Inline-SVG charts

Hand-write these. They scale, respect dark mode, and don't need a runtime library. Drop the `<style>` block once at the top of the page; each chart reuses the same classes.

**Shared CSS (one block, all chart types share it):**

```html
<style>
  /* Chart palette. Override --c-* if the artifact uses different semantic colors. */
  .chart {
    display: block;
    width: 100%;
    max-width: 460px;     /* cap physical size — prevents text from scaling up massively in wide containers */
    margin: 0 auto;
    height: auto;
    overflow: hidden;     /* DETERMINISTIC GUARD: clip to the SVG box so a mis-placed label can NEVER paint past the card edge. This is the structural fix for the recurring border-escape bug. Pair it with correct viewBox gutters (verify_diagrams.py) so well-formed charts never actually get clipped. Do NOT change this to `visible`. */
  }
  .chart text { font-family: var(--mono, ui-monospace, monospace); font-size: 11px; fill: var(--ink-2); }
  .chart .chart-title { font-family: var(--sans, system-ui); font-size: 12px; fill: var(--ink); font-weight: 600; }
  .chart .grid { stroke: var(--line); stroke-width: 1; }
  .chart .axis { stroke: var(--ink-2); stroke-width: 1; }
  .chart .target { stroke: var(--danger, #E8437F); stroke-width: 1.5; stroke-dasharray: 4 3; }
  .c-indigo  { fill: var(--indigo,  #5856D6); }
  .c-mint    { fill: var(--mint,    #00C781); }
  .c-pink    { fill: var(--pink,    #E8437F); }
  .c-orange  { fill: var(--orange,  #FFB020); }
  .c-muted   { fill: var(--line,    rgba(0,0,0,0.18)); }
  /* For text labels rendered on top of a saturated fill (in-segment % labels, KPI overlays). White-on-fill meets AA on c-indigo and c-pink but not c-mint / c-orange in light mode; prefer external labels (above/below the bar) for the latter two. */
  /* MUST be more specific than `.chart text` (0,1,1) or the muted fill wins — `.chart text.lbl-on-fill` is (0,2,1) and beats it. A bare `.lbl-on-fill` (0,1,0) does NOT. */
  .chart text.lbl-on-fill { fill: var(--paper, #FFFFFF); }
</style>
```

**Stacked horizontal bar (one whole split N ways).** Use for proportions like a maintenance/build/strategic pulse, language mix, time-spent breakdown.

```html
<svg class="chart" viewBox="0 0 320 48" role="img" aria-label="Maintenance 17%, build 38%, strategic 45%.">
  <!-- segments: x and width sum to 300 (the bar) inside a 320-unit viewBox for breathing room. -->
  <rect class="c-pink"   x="0"    y="16" width="51"  height="20" />
  <rect class="c-indigo" x="51"   y="16" width="114" height="20" />
  <rect class="c-mint"   x="165"  y="16" width="135" height="20" />
  <!-- In-segment labels for segments where white-on-fill meets AA (c-indigo, c-pink). For c-mint / c-orange (lower luminance), place labels externally. -->
  <text x="25"  y="30" text-anchor="middle" class="lbl-on-fill">17%</text>
  <text x="108" y="30" text-anchor="middle" class="lbl-on-fill">38%</text>
  <text x="233" y="30" text-anchor="middle" class="lbl-on-fill">45%</text>
  <!-- legend row -->
  <g transform="translate(0, 0)">
    <rect class="c-pink"   x="0"   y="0" width="10" height="10" />
    <text x="14"  y="9">Maint</text>
    <rect class="c-indigo" x="64"  y="0" width="10" height="10" />
    <text x="78"  y="9">Build</text>
    <rect class="c-mint"   x="128" y="0" width="10" height="10" />
    <text x="142" y="9">Strategic</text>
  </g>
</svg>
```

**Never put a single value label at the END of a stacked bar.** A stacked bar's right edge is the position the eye reads as "the total". If you anchor one number there, that number claims the whole bar, including every segment before it. When the segments mean *different things* (content vs onboarding, done vs remaining, billable vs internal), an end-anchored label is an outright lie: it makes a 2-artifact green segment plus a 1-onboarding grey segment read as a single bar worth "2", with the grey silently absorbed into that 2. This is the most common stacked-bar bug. Two correct options:

1. **Label each segment in place** (the scaffold above) — one number per segment, centered in or just past that segment, so every value is anchored to the region it measures. This is the default for any stacked bar.
2. **If a segment is too thin to hold its label**, put each segment's value just *outside its own end* (at the segment boundary, not the bar's end), or move all values into the legend (`Content 2 · Onboarding 1`). Never collapse them to one number at the far edge.

Litmus test before you ship a stacked bar: cover everything except the rightmost label with your hand. Does that number, alone, describe the entire bar correctly? If the bar has mixed-meaning segments, the answer is always no, so the single-end-label layout is always wrong for them. (A single end label is only acceptable when the whole bar is one homogeneous quantity, i.e. not actually stacked.)

**Bar with target rule (counts vs quota).** Use for "current vs cap" stats: queue size, error budget, work-plate vs healthy load.

```html
<svg class="chart" viewBox="0 0 200 80" role="img" aria-label="Work plate 30 of healthy 12, well over target">
  <line class="grid" x1="0" y1="60" x2="200" y2="60" />
  <!-- the bar (height scaled to value, anchored at y=60). scale = (60 - 44) / 12 = 1.333 units per value, matching the target line. value 30 → height 40, top y = 60 - 40 = 20. -->
  <rect class="c-orange" x="20" y="20" width="36" height="40" rx="3" />
  <!-- target line (horizontal at the cap height) -->
  <line class="target" x1="0" y1="44" x2="200" y2="44" />
  <text x="196" y="42" text-anchor="end" class="chart-title">target 12</text>
  <text x="38" y="16" text-anchor="middle" class="chart-title">30</text>
  <text x="38" y="74" text-anchor="middle">work plate</text>
</svg>
```

**Sparkline (3+ time-series points).** Use for "last 7 days" stat trends, error-rate over time, queue-depth history.

```html
<svg class="chart" viewBox="0 0 120 40" preserveAspectRatio="none" role="img" aria-label="Last 7 days: 12, 9, 14, 8, 5, 7, 11. Trended down to 5 then partially recovered.">
  <!-- Min-max scaling fills the available y range. For values v with min=5 max=14: y = 5 + ((max - v) / (max - min)) * 30, mapping the data into y=5..35 of a 40-tall viewBox. -->
  <!-- Don't add class="c-indigo" here: .c-indigo { fill: var(--indigo) } wins over inline fill="none" via CSS specificity and the line renders as a filled polygon. -->
  <polyline fill="none" stroke="var(--indigo, #5856D6)" stroke-width="1.5"
    points="0,12 20,22 40,5 60,25 80,35 100,28 120,15" />
  <!-- dot on latest point -->
  <circle class="c-indigo" cx="120" cy="15" r="2.5" />
</svg>
```

**Sorted horizontal bar list (6+ categories — REPLACES pie/donut).** This is the canonical pattern for category proportions when you have more than 5 categories or proportions span orders of magnitude. Each category gets its own row sorted by value, the bar width is proportional to the category total, and optional stacked segments inside each bar show subcategory mix. Labels are always legible because they're laid out on a baseline grid, not crammed around a circle.

```html
<svg class="chart" viewBox="0 0 340 220" role="img" aria-label="Spending by category: Rent $3,195, Shopping $1,200, Groceries $800, ...">
  <!-- One <g> per row. row height ~24, gap 4. Label column ~80px, bar column ~200px, value column ~50px.
       viewBox width 340 = 84 (label+gap) + 200 (bar) + 56 (value gutter): a 6-char "$3,195" at x=288 ends ~328, inside 340. -->
  <g transform="translate(0, 0)">
    <text x="78" y="14" text-anchor="end">Rent</text>
    <rect x="84" y="4" width="200" height="14" rx="2" class="c-indigo" />
    <text x="288" y="14">$3,195</text>
  </g>
  <g transform="translate(0, 28)">
    <text x="78" y="14" text-anchor="end">Shopping</text>
    <rect x="84" y="4" width="75"  height="14" rx="2" class="c-pink" />
    <text x="288" y="14">$1,200</text>
  </g>
  <!-- For stacked subcategory segments, render multiple <rect> per row sharing one class with declining opacity. Opacity survives dark mode for free. -->
  <g transform="translate(0, 56)">
    <text x="78" y="14" text-anchor="end">Groceries</text>
    <rect x="84"  y="4" width="30" height="14" rx="2" class="c-mint" />
    <rect x="114" y="4" width="15" height="14"        class="c-mint" opacity="0.7" />
    <rect x="129" y="4" width="5"  height="14" rx="2" class="c-mint" opacity="0.45" />
    <text x="288" y="14">$800</text>
  </g>
</svg>
```

Sort by total descending. Cap to top ~20 rows; the tail goes to an "Other" row at the bottom.

**Progress ring (single ratio only).** Use for one-number progress: % triaged, % closed, % migration complete. Do NOT use for category proportions — that's what the horizontal bar list above is for.

```html
<svg class="chart" viewBox="0 0 80 80" role="img" aria-label="38% complete">
  <!-- background ring -->
  <circle cx="40" cy="40" r="32" fill="none" stroke="var(--line)" stroke-width="10" />
  <!-- progress ring: stroke-dasharray = (pct/100)*circumference, circumference = 2*π*r ≈ 201 -->
  <circle cx="40" cy="40" r="32" fill="none" stroke="var(--indigo, #5856D6)" stroke-width="10"
    stroke-dasharray="76 201" stroke-linecap="round" transform="rotate(-90 40 40)" />
  <text x="40" y="44" text-anchor="middle" class="chart-title" style="font-size: 16px;">38%</text>
</svg>
```

**Process flow (3+ steps with arrows).** Use for pipeline diagrams: routine flows, deploy stages, decision trees.

```html
<svg class="chart" viewBox="0 0 480 80" role="img" aria-label="Pipeline: fetch then classify then save then archive">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--ink-2)" />
    </marker>
  </defs>
  <!-- boxes -->
  <g class="step">
    <rect x="0"   y="20" width="100" height="40" rx="6" fill="var(--indigo-soft)" stroke="var(--indigo)" />
    <text x="50" y="44" text-anchor="middle" class="chart-title">Fetch</text>
  </g>
  <g class="step">
    <rect x="130" y="20" width="100" height="40" rx="6" fill="var(--mint-soft)" stroke="var(--mint)" />
    <text x="180" y="44" text-anchor="middle" class="chart-title">Classify</text>
  </g>
  <g class="step">
    <rect x="260" y="20" width="100" height="40" rx="6" fill="var(--orange-soft)" stroke="var(--orange)" />
    <text x="310" y="44" text-anchor="middle" class="chart-title">Save</text>
  </g>
  <g class="step">
    <rect x="390" y="20" width="90"  height="40" rx="6" fill="var(--pink-soft)" stroke="var(--pink)" />
    <text x="435" y="44" text-anchor="middle" class="chart-title">Archive</text>
  </g>
  <!-- arrows -->
  <line x1="100" y1="40" x2="130" y2="40" stroke="var(--ink-2)" marker-end="url(#arrow)" />
  <line x1="230" y1="40" x2="260" y2="40" stroke="var(--ink-2)" marker-end="url(#arrow)" />
  <line x1="360" y1="40" x2="390" y2="40" stroke="var(--ink-2)" marker-end="url(#arrow)" />
</svg>
```

**Multi-bar / category compare (group of 3-6 counts).** Use for "saved vs skipped vs also-mentioned" per batch, plate-size by section.

```html
<svg class="chart" viewBox="0 0 280 130" role="img" aria-label="Must-read 16, also-mentioned 9, skipped 35.">
  <line class="grid" x1="40" y1="100" x2="240" y2="100" />
  <!-- Bars all scale at one ratio: height = (value / max) * 84 with max=35. Cap at 84 leaves 6-unit headroom for the value label above the tallest bar. Heights: 38, 22, 84. Tops: y = 100 - height. -->
  <rect class="c-indigo" x="50"  y="62"  width="40" height="38" rx="3" />
  <rect class="c-mint"   x="120" y="78"  width="40" height="22" rx="3" />
  <rect class="c-pink"   x="190" y="16"  width="40" height="84" rx="3" />
  <!-- value labels 6 units above each bar's top -->
  <text x="70"  y="56" text-anchor="middle" class="chart-title">16</text>
  <text x="140" y="72" text-anchor="middle" class="chart-title">9</text>
  <text x="210" y="10" text-anchor="middle" class="chart-title">35</text>
  <!-- category labels below baseline -->
  <text x="70"  y="114" text-anchor="middle">must-read</text>
  <text x="140" y="114" text-anchor="middle">also</text>
  <text x="210" y="114" text-anchor="middle">skipped</text>
</svg>
```

Sizing rules for all chart scaffolds:
- Set `viewBox` and let `width: 100%` from `.chart` scale it. Don't fix `width="200"` in the SVG element.
- Pick the viewBox to match the *aspect ratio* you want; the absolute numbers are arbitrary.
- For multi-bar charts, derive bar heights as `(value / max_value) * H`, where `H` is the cap that leaves room for value labels above the tallest bar (the scaffold uses `H = 84` with baseline at `y=100`, leaving 6-unit label headroom). The bar's top y-coord is `baseline - height`. Round to integers in the source.
- Always include `aria-label` with the actual numbers so screen readers and `grep` both work.

## Anti-patterns

- **Don't ship without dark mode.** If you skip the `prefers-color-scheme: dark` block, the artifact looks broken to anyone whose OS is in dark mode.
- **Don't write multi-paragraph CSS comments.** Match the codebase tone — terse, only when WHY is non-obvious.
- **Don't add settings panels, theme switchers, or "preferences"** unless the artifact is genuinely reused. Personal tools shouldn't have settings UIs — pick a default and ship it.
- **Don't embed user content inside `<script>` blocks without escaping.** Any string that came from the filesystem (titles, file paths, summaries) goes through `JSON.stringify` or HTML-escaping before reaching the page.
- **Don't `open` the file from inside a skill that's wrapped by a chain.** The outer skill controls when to open; the inner one respects `$HTML_NO_OPEN`.
- **Don't reuse `triage.html` / `plan.html` / `report.html` names across artifacts.** Always include a slug so multiple generated files don't clobber each other in the same dir.
