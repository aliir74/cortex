# how-to-html reference: charts and diagram geometry

On-demand reference for `how-to-html`. **Read this before writing or editing any
chart or diagram SVG.** It holds the sizing maths, the label-placement rules, and
the canonical chart shapes (Scaffold §5). The decisions live in `SKILL.md`: which
visual to pick for a data shape, the pie/donut ban, and the mandatory
`verify_diagrams.py` run.

## Contents

1. [Which visual for which data shape](#which-visual-for-which-data-shape)
2. [Inline SVG patterns (charts and diagrams both)](#inline-svg-patterns-charts-and-diagrams-both)
3. [Why the border bug is structurally solved](#why-the-border-bug-is-structurally-solved)
4. [SVG chart sizing, non-negotiable defaults](#svg-chart-sizing-non-negotiable-defaults) (cap at 460px, clip, budget gutters inside the viewBox, card out-pads the chart)
5. [Label-placement rules to prevent overlap](#label-placement-rules-to-prevent-overlap)
6. [Text-on-colored-bar contrast](#text-on-colored-bar-contrast)
7. [Value labels above bars need viewBox top padding](#value-labels-above-bars-need-viewbox-top-padding)
8. [Chart-in-stat-card, the full reasoning](#chart-in-stat-card-the-full-reasoning)
9. [What verify_diagrams.py checks, and how to fix each class](#what-verify_diagramspy-checks-and-how-to-fix-each-class)
10. [Scaffold §5: Inline-SVG charts](#scaffold-5-inline-svg-charts): shared CSS, stacked horizontal bar, bar with target rule, sparkline, sorted horizontal bar list, progress ring, process flow, multi-bar compare, and the sizing rules for all of them
11. [Structural diagrams: node and connector craft](#structural-diagrams-node-and-connector-craft) (§11): complexity budget, focal accent, 4-unit grid, orthogonal elbows, arrow-label masks, attach points, and the elbow scaffold. Read this instead of the chart sections when the visual is a flow, architecture, tree or state diagram.

Section numbers (`§5`) are stable identifiers cited by other skills (`create-plan`,
`make-slides`). Do not renumber them.

## Which visual for which data shape

The decision to use a visual at all, and the pie/donut/sunburst ban, live in
`SKILL.md`. This is the shape-to-chart mapping.

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

## Inline SVG patterns (charts and diagrams both)

**Inline SVG patterns:**
- Colors go in an internal `<style>` block as classes (`.box-tier1`, `.lbl-title`), never inline `fill="..."` attributes that can't dark-mode-flip.
- Always include a `@media (prefers-color-scheme: dark)` block inside the SVG `<style>` overriding fills, strokes and text, or the diagram is unreadable on a dark wallpaper.
- **Colors carry semantic meaning**, not decorative picks. Mint = positive/auto/safe, amber = needs attention/routed, pink = problem/split candidate, indigo = primary/entry, purple = on-demand/deferred. Same color, same meaning, across an artifact.
- `viewBox`, not fixed `width`/`height`, so the SVG scales with its container.
- `role="img"` plus `aria-label="<one-sentence description>"` for screen readers.
- One `<marker>` in `<defs>`, reused via `marker-end="url(#arrow)"`, for all arrows.

## Why the border bug is structurally solved

> **The border bug is solved by two mechanisms, not by trying harder at the math below.** (a) `.chart { overflow: hidden }` (scaffold §5) clips anything that would paint past the card — so a coordinate mistake can never *look* like a label hanging off the box. (b) `verify_diagrams.py` (see "Verify every diagram (mandatory)" in `SKILL.md`) statically checks every label/shape is inside its viewBox AND that no label straddles a card/panel border, and a PostToolUse hook runs it on every `.html` write. The sizing rules below are how you make charts that pass the verifier *and* don't get clipped; they are no longer the last line of defense.

## SVG chart sizing, non-negotiable defaults

**SVG chart sizing — non-negotiable defaults.** SVG text uses *user units* (viewBox coordinates), not CSS pixels. When the SVG container stretches wider than the viewBox, text scales up proportionally. A `font-size: 11` label inside a `viewBox="0 0 320 200"` SVG rendered at 1200px wide becomes ~41px — labels overflow, overlap bars, and overlap each other. This happens silently because dev preview is usually narrower than production layouts (full-width container, mobile breakpoint collapsing a 2-col grid to 1-col, etc.). Rules to prevent this every time:

1. **Always cap `.chart { max-width: 460px; margin: 0 auto; }`.** Charts are designed for ~320–480 user-unit viewBoxes; let them sit at that physical size and don't stretch. Center inside the card.
2. **Always clip: `.chart { overflow: hidden; }`** (the scaffold §5 default). SVG clips at its box by default; the old advice to set `overflow: visible` was the *cause* of the recurring "label hanging off the card" bug — it let content placed past the viewBox paint outside the parent card. Clipping makes card-escape structurally impossible. The cost is that a mis-placed label gets cut off instead of escaping — which the verifier catches before you ship, so a well-formed chart is never actually clipped.

3. **Budget gutters INSIDE the viewBox so every label lives within `[0..W, 0..H]`.** Pick the viewBox so it already contains the labels, then no spill is possible. Concretely:
   - **Left gutter** ≥ the widest left-hand (category) label. If names are anchored `text-anchor="end"` at `x=L`, set `L` ≥ widest-label-width (~6.5 units/char at font-size 11) so the text runs from `0` to `L`, never negative. "annelier18" (10 chars) ≈ 65 units, so `L` ≥ 70 and bars start at ~`L+8`.
   - **Right gutter** ≥ the widest value/end label. If the longest bar ends at `x=E` and carries a value label, that label runs from `E+6` to `E+6+labelWidth`; the viewBox width `W` must be ≥ that end. For a stacked bar, account for the *outermost* segment's trailing label, not the bar.
   - **Top/bottom gutters** for value labels above bars and category labels below the baseline (descenders need ~4 units), plus room for a legend row if it lives inside the SVG.
   - Rule of thumb: `W = leftGutter + barArea + rightGutter`, and verify the rightmost text's end ≤ `W` and the leftmost text's start ≥ `0`. If a label would cross a boundary, widen the viewBox or shorten the label, do not lean on overflow.

4. **The card must out-pad the chart.** The parent card needs `padding` ≥ a few px and the chart's `max-width` must fit inside `card-width − 2·padding`. Combined with rule 2 (clip) and rule 3 (nothing outside the viewBox) this makes card escape impossible by construction, not by hand-checking.

## Label-placement rules to prevent overlap

**Label-placement rules to prevent overlap:**
- **Text labels go in the long axis of free space.** For column/bar charts, put value labels ABOVE the bar (not beside it) and category labels BELOW the baseline. Putting a label beside a bar wastes the chart's widest dimension on text.
- **Threshold / reference-line labels go at the TOP of the chart, centered, above all bars** — never on the same y-coordinate as bar value labels. If a dashed threshold line is at y=60, the value labels for bars touching that line will be at y≈52 (just above the bar top). Putting threshold text at y=36 with text-anchor="end" places it in the same horizontal stripe → guaranteed overlap when the rightmost bar reaches the threshold. Move the threshold label to its own band (y=14, centered) and add ~30 user units of viewBox top-padding for it.
- **Budget ~6.5 user units per character at font-size 11** when planning label positions. "BC PNP threshold · 5 FTEs" (24 chars) needs ~156 user units; an anchor at x=306 text-anchor="end" places it from x=150 to x=306 — extending across more than half the chart. Either shorten the label or give it its own row.
- **Keep in-chart text terse.** Full descriptions go in the position pill / caption / aria-label, not inside the SVG. Inside the chart: numbers, short categories, axis ticks, one-line threshold marker. Anything longer goes outside.
- **Stacked bars: label every segment, never the bar's end.** A value anchored at a stacked bar's right edge reads as the total and silently swallows the segments before it. Label each segment in place (or in the legend) instead. See the stacked-bar scaffold in §5 for the full rule and litmus test.
- **A caption/label is fully inside a card/panel or fully outside it, never straddling the border.** A caption placed in the strip just below a row of cards looks fine in your head, but the label's own text-height (~ascent 0.8 × font-size above the baseline) pushes its top edge back UP into the cards, so the caps collide with the card's bottom border and read as "clipped". This passes a pure viewBox-containment check (the label IS inside the viewBox) but still looks broken. Fix: give the caption its own band — extend the viewBox below the cards and set the baseline so the whole text box (top ≈ `y − 0.8·fs`, bottom ≈ `y + 0.22·fs`) clears the card's bottom edge by a few units. `verify_diagrams.py` now flags this as a "panel straddle" violation, so the hook blocks it on write.
- **Multi-line node/bar labels: use sibling `<text>` elements, never `<tspan>` continuations.** Under a middle-anchored parent, `verify_diagrams.py` mismeasures a `<tspan>` continuation line and silently reports a huge false overflow, so a correct diagram fails the hook with no clue why. Split each line into its own `<text x=… y=…>` at the same anchor instead.
- **Verify by resizing.** After writing a chart, mentally (or actually) resize the browser to the widest expected breakpoint and check that (a) no text overlaps another element, (b) nothing clips at the viewBox edge, and (c) no label or shape extends past the parent card's edge. The widest breakpoint is where edge labels escape the card, so check there, not just at dev width.

## Text-on-colored-bar contrast

**Text-on-colored-bar contrast — non-negotiable:**
- When placing a `<text>` element *inside* a colored `<rect>` (stacked bars, multi-bar value labels, segment percentages), the chart's CSS `.chart text { fill: var(--muted); }` rule will paint it in a low-contrast grey unless you override. The `fill="white"` HTML attribute is **defeated by the CSS class selector** (CSS wins over presentation attributes for `fill`).
- **Always use `class="lbl-on-fill"` for in-segment text labels.** It sources from `var(--paper)` — white in light mode, dark in dark mode. **Critical:** the §5 rule is defined as `.chart text.lbl-on-fill` (specificity 0,2,1), NOT a bare `.lbl-on-fill` (0,1,0) — a bare class loses to `.chart text` (0,1,1) and the label silently renders muted grey on the colored fill. If you copy the class into an artifact, copy the qualified selector with it. Inline `style="fill: white"` also works but doesn't dark-mode-flip.
- White-on-fill meets AA on `c-indigo` and `c-pink` but not on `c-mint` / `c-orange` in light mode (mint and amber are too light). For those, place labels externally (above or below the bar) instead of in-segment.
- For text *outside* bars (axis labels, category labels below baseline), leave the default `var(--muted)` — that's fine on the card background.

## Value labels above bars need viewBox top padding

**Value labels above bars need viewBox top padding:**
- A bar from `y=12` to `y=100` (height 88) with a value label at `y=8 dy=8` (baseline y=16) means the text's bottom edge sits on top of the bar — the descender of "2" or "g" gets clipped behind the bar. The label looks "cut off" even though the text is technically there.
- **Always pad the viewBox top by at least the text height (~14 user units at font-size 11–12) when value labels go above bars.** Use `viewBox="0 0 W H+20"` and start bars at `y=24`+ to leave a clean band for labels at `y=12`–`y=20`. Don't squeeze the label into the first 8 user units of the viewBox.
- Same lesson for the bottom: category labels below the baseline at `y=baseline+14` need viewBox bottom-padding so descenders ("p", "g", "y") don't clip.

## Chart-in-stat-card, the full reasoning

**Chart-in-stat-card: don't.** Stat cards are typically 140–180px wide. Cramming a `viewBox=160x72` chart into a 140px card shrinks all SVG text to ~10 device pixels — barely legible. **Stat cards with comparisons should use a big number + a small text meta line (`target 12 · +50% over`)**, not a tiny chart. Reserve charts for their own full-width sections where the SVG can breathe at 320–460px wide. If a stat card really needs a sparkline, give it `min-height: 80px` and don't add extra `<text>` labels — let the sparkline shape carry the meaning.

## What verify_diagrams.py checks, and how to fix each class

`SKILL.md` carries the mandate to run it (and the PostToolUse hook that enforces
it). This is the detail of what it measures.

It parses every `<svg>` that has a `viewBox` and contains text (i.e. every
chart/diagram), accounts for group `translate()` transforms and `text-anchor`,
estimates each label's width, and reports seven failure classes (each violation line carries its `[class N]`):

1. **Border escape.** Any `text`/`rect`/`line`/`circle`/`polyline` whose extent
   falls outside `[0..W, 0..H]`. Fix by widening the viewBox (budget the gutters
   per the sizing rules above), then re-anchoring the label, and only then
   shortening it. Never by setting `overflow: visible`.
2. **Panel straddle.** A label that sits inside the viewBox but crosses the border
   of a card/panel rect (a container box at least 6x the label's own area), which
   reads as "clipped" even though containment passes. Fix by giving the caption its
   own band: extend the viewBox below the cards and set the baseline so the whole
   text box (top about `y - 0.8*fs`, bottom about `y + 0.22*fs`) clears the card
   edge by a few units.

3. **Diagonal connector.** A straight segment of a marker-bearing `line`/`path` that
   is off-axis on both axes. Fix by redrawing it as an orthogonal elbow (§11). Only
   marker-bearing elements are checked, so sparklines, axes, grid lines and target
   rules are never flagged.
4. **Label on connector.** An arrow label whose text box actually collides with the
   line it annotates. Repair order, label-preserving: move the label 6-10 units
   clear over a paper-filled mask rect; then adjust the route or spacing; then
   shorten the wording while keeping its meaning. Deleting the label is not a
   geometry repair: the labels are the content of a structural diagram (§11).
5. **Shared attach point.** Two connectors leaving or arriving at the same point on a
   box edge, so their arrowheads overlap. Fix by spreading them at least 12 units
   apart along the edge (§11).
6. **Behind a node.** A connector segment crossing a node rect that is not one of its
   endpoints (rects under 20 units on a side, and container boxes that enclose other
   rects, do not count). Fix by routing around: extend the elbow's run before
   turning. If the crossing is genuinely unavoidable, make the connector dashed, which
   the verifier accepts as the documented "passing through" form (§11 rule 5).
7. **Shared corridor.** Two parallel segments from different connectors less than 8
   units apart while overlapping along their axis, including collinear runs 0 units
   apart. Fix by offsetting one path by at least 8 units or routing it around (§11
   rule 4).

Classes 3-7 flag only genuine collisions, not near-misses: a 5-unit label gap is a
taste call the linter leaves to you, a label sitting *on* the line is a blocked write.

Exit 0 is clean; exit 1 prints the offending element with the numbers. Re-run until
clean. `python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/verify_diagrams.py" --self-test` lints
the scaffolds in this file.

## Scaffold §5: Inline-SVG charts


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

**Stacked horizontal bar (one whole split N ways).** Use for proportions like the maintenance/build/strategic pulse, language mix, time-spent breakdown.

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

**Progress ring (single ratio only).** Use for one-number progress: % triaged, % SOC 2 closed, % migration complete. Do NOT use for category proportions — that's what the horizontal bar list above is for.

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

**Process flow (3+ steps with arrows).** Use for pipeline diagrams: a daily routine flow, deploy stages, decision trees. Straight-line arrows are fine for a single left-to-right row like this one; the moment a connector has to change direction, read §11 and draw an elbow.

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

**Multi-bar / category compare (group of 3-6 counts).** Use for "saved vs skipped vs also-mentioned" per newsletter batch, plate-size by section.

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

## Structural diagrams: node and connector craft

The sections above are about charts, where the geometry risk is a label escaping its
viewBox. Structural diagrams (flow, architecture, sequence, tree, state) fail
differently: they end up cluttered, and their arrows look sketched rather than drawn.
These rules are what separate the two, adapted from
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design).
`verify_diagrams.py` enforces the five mechanical ones (classes 3-7 above); the
focal, budget and grid rules are yours to apply.

### Before drawing: is a diagram the right answer?

**A diagram earns its place only when the reader learns more from it than from a
well-written paragraph.** Skip it for: a list of things (use a table or bullets), a
simple before/after (use a two-column table), a single shape with a label (write the
sentence), and anything whose only structure is sequence (numbered steps read fine as
prose). This sits under the skill's "always reach for visuals" rule, not against it:
the point is that *relational* content wants a diagram and *enumerable* content does
not.

### Complexity budget, hard cap

- **Maximum 9 nodes and 12 connectors per diagram.** Past that, the reader stops
  tracing paths and starts skimming, which is the failure the diagram existed to
  prevent.
- Over budget means **split, never shrink the type**: one overview diagram of the
  zones, then a detail diagram per zone. Two legible diagrams beat one dense one.
- **The highest-quality edit is deletion.** Before shipping, try removing each node
  and each arrow. If the diagram still says the same thing, the removal was correct.
  A schematic is done when nothing more can come out, not when everything is in.

### Focal rule: accent on at most 2 nodes

The artifact's accent colour marks the 1-2 nodes the reader should look at first (the
entry point, the thing that changed, the bottleneck). Everything else is ink, muted,
or soft. **Accent on five nodes is the same as accent on none**, it just costs the
reader a scan. Semantic colour (mint = safe, amber = attention, pink = problem) still
applies to *state*; the focal accent applies to *attention*, and the two should not
fight in one diagram: pick semantic colouring or focal colouring per diagram.

Node treatments, in decreasing prominence: focal (accent tint fill + accent stroke),
primary (paper fill + ink stroke), store or state (soft tint fill + muted stroke),
external (soft grey, thin stroke), optional or deferred (dashed stroke, 0.6 opacity).

### Draw on a 4-unit grid

**Every x, y, width, height and gap in a structural diagram is a multiple of 4.**
Exempt: stroke widths, opacity, corner radii, and anything derived from data (bar
heights). This one rule does most of the work in making a hand-written diagram look
drawn rather than generated: mixed 1-unit offsets read as noise even when nothing
technically misaligns. Node heights of 40, gaps of 24, label offsets of 8, arrows on
grid centre lines. A gap is clear space between two shape edges, not a distance
between centres: two 80-wide nodes whose centres sit 96 apart have a 16-unit gap,
not 96.

### Connectors, six rules

1. **Orthogonal elbows only, never diagonals.** A connector runs horizontally then
   vertically (or vice versa) with a rounded bend, `r=8`. Drawn as a `path`:
   `M88,36 H112 Q120,36 120,44 V76 Q120,84 128,84 H152`. The `Q` control point sits at
   the corner the two straight runs would have met at. *Verifier class 3.*
2. **Arrow labels clear the line by 6-10 units, over a mask rect.** A label touching
   its own connector is unreadable at phone width. Put the label beside or above the
   segment, and back it with a `rect` filled `var(--paper)` sized to the text plus ~4
   units of padding, drawn *before* the text and *after* the line. *Verifier class 4.*
3. **One attach point per connector, at least 12 units apart on a shared edge.** Two
   arrows leaving the same node get separate exit points on that edge (or exit
   different edges). Coincident attach points overlap arrowheads. *Verifier class 5.*
4. **Connectors never overlap each other.** Route around instead: extend one elbow's
   horizontal run further before turning. If two paths must share a corridor, offset
   them by 8 units. *Verifier class 7.*
5. **A connector does not pass behind a node that is not its endpoint.** Route around
   it. When the geometry genuinely forbids that, make the crossing connector dashed so
   the reader can see it is passing through, not terminating. *Verifier class 6
   (dashed connectors are exempt).*
6. **Mask rects go under their own label only.** A mask sized to cover a neighbouring
   node erases part of that node's stroke, which reads as a rendering bug.

### Accessibility contract for diagrams

Charts carry `role="img"` plus `aria-label`. Structural diagrams carry more, because
the relationships are the content and a single label cannot hold them:

```html
<svg class="chart" viewBox="0 0 240 120" role="img" aria-labelledby="d1-t d1-d">
  <title id="d1-t">Queue feeds the worker pool</title>
  <desc id="d1-d">Jobs land in the queue, are pulled by the worker pool, and failures
  return to the queue on the retry path.</desc>
  ...
</svg>
```

`<title>` is the first child and IDs are prefixed per diagram so multiple diagrams on
one page do not collide.

### Elbow connector scaffold (§11)

The reference layout, and the fixture the verifier's connector checks are tested
against. Two nodes on different rows, one elbow, one masked label, everything on the
4-unit grid.

```html
<svg class="chart" viewBox="0 0 240 120" role="img" aria-labelledby="q-t q-d">
  <title id="q-t">Queue feeds worker</title>
  <desc id="q-d">Jobs flow from the queue to the worker over a retry path.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="var(--ink-2)" />
    </marker>
  </defs>
  <!-- focal node: accent tint + accent stroke. At most 2 of these per diagram. -->
  <rect x="8" y="16" width="80" height="40" rx="8" fill="var(--indigo-soft)" stroke="var(--indigo)" />
  <text x="48" y="40" text-anchor="middle" class="chart-title">Queue</text>
  <!-- orthogonal elbow: H, rounded bend, V, rounded bend, H. All coords on the 4-grid. -->
  <path d="M88,36 H112 Q120,36 120,44 V76 Q120,84 128,84 H152" fill="none"
        stroke="var(--ink-2)" marker-end="url(#arrow)" />
  <!-- label mask: paper fill, drawn after the line and before the text, sized to the text + 4 units -->
  <rect x="78" y="62" width="28" height="12" fill="var(--paper)" />
  <text x="104" y="70" text-anchor="end">retry</text>
  <rect x="152" y="64" width="80" height="40" rx="8" fill="none" stroke="var(--line)" />
  <text x="192" y="88" text-anchor="middle" class="chart-title">Worker</text>
</svg>
```
