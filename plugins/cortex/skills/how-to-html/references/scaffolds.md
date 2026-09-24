# how-to-html reference: scaffolds

On-demand reference for `how-to-html`. **Read this before writing the page shell,
a Copy-result round-trip, a drag-drop board, the responsive layout, the report nav, or the
collapse layer.** Copy-modify these; they are the canonical shapes, so vary the values, not
the structure. Chart scaffolds live in the sibling `charts.md` (Scaffold §5), not here.

## Contents

1. [Scaffold §1: CSS tokens + dark mode](#scaffold-1-css-tokens--dark-mode): the warm-neutral palette, dark-mode block, reduced-motion block
2. [Scaffold §2: HTML skeleton](#scaffold-2-html-skeleton): doctype, viewport meta, font preconnect, container
3. [Scaffold §3: Copy result + toast](#scaffold-3-copy-result--toast): the custom-editor clipboard round-trip, counter, Cmd+Enter shortcut, execCommand-first copy
4. [Scaffold §4: Drag-drop with keyboard support](#scaffold-4-drag-drop-with-keyboard-support): mouse drag plus Space/arrow/Escape keyboard nav
5. [Scaffold §6: Responsive layout](#scaffold-6-responsive-layout): phone-first container, auto-collapsing grid, 44px targets, safe-area floating button, table wrapper, tap-to-move touch fallback
6. Scaffold §7: retired (no annotation layer ships in artifacts)
7. [Scaffold §8: Report navigation](#scaffold-8-report-navigation): sticky numbered rail, scroll-spy, progress, phone sheet
8. [Scaffold §9: Collapse layer](#scaffold-9-collapse-layer-collapsed-by-default): every section and card collapsible, collapsed by default, find-in-page safe

Section numbers are stable identifiers cited by other skills. Scaffold §5 (charts)
is in the sibling `charts.md`. Do not renumber, and do not fill the §5 or §7 gaps here.

## Scaffold §1: CSS tokens + dark mode


```html
<style>
  :root {
    /* Token NAMES are the contract (installers and scaffolds read them).
       Every VALUE below is a neutral placeholder: choose the real palette and
       typefaces per artifact. See render.md "Default looks to leave out". */
    --bg: #FFFFFF;
    --ink: #111111;
    --ink-2: #5F5F5F;
    --paper: #FFFFFF;
    --rule: rgba(0,0,0,0.10);
    --rule-2: rgba(0,0,0,0.18);

    --accent: #2F6FEB;    /* primary interactive */
    --success: #1F9D55;
    --warn: #C98A00;
    --danger: #D23F3F;

    --display: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, monospace;

    --radius: 8px;
    --shadow: 0 1px 2px rgba(0,0,0,0.06);
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

## Scaffold §2: HTML skeleton


```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{TITLE}}</title>
  <!-- optional: <link> to a web font chosen for THIS artifact; the system stack is the fallback -->
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

## Scaffold §3: Copy result + toast


```html
<button class="btn primary" id="copy" disabled>
  Copy result · <span id="decided-count">0</span> decided
</button>
<div class="toast" id="toast">Copied to clipboard</div>

<style>
  .toast {
    position: fixed; bottom: calc(32px + env(safe-area-inset-bottom)); left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: var(--ink); color: var(--paper);
    padding: 12px 20px; border-radius: var(--radius, 8px);
    font-family: var(--sans); font-size: 13px;
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

  // Clipboard, gesture-safe. Do NOT rely on navigator.clipboard.writeText alone: on a
  // local file:// artifact it can hang forever (never resolves, never rejects), so the
  // .catch() fallback never fires and the copy dies with zero feedback (seen in
  // recent Chrome). execCommand("copy") is deprecated but synchronous, immune to
  // that hang, and works on file://, so it goes first.
  function copySync(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;top:0;left:-9999px;opacity:0";
    document.body.appendChild(ta);
    const sel = document.getSelection();
    const prev = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
    ta.select();
    ta.setSelectionRange(0, text.length);
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    if (prev && sel) { sel.removeAllRanges(); sel.addRange(prev); }
    return ok;
  }

  // Manual fallback, in page. Never window.prompt(): Chrome silently blocks dialogs raised
  // without user activation, and a pending dialog freezes the whole page. Style .cl-copy-fallback
  // as a fixed, centered panel above the action bar.
  function manualCopyFallback(text) {
    let box = document.getElementById("copy-fallback");
    if (!box) {
      box = document.createElement("div");
      box.id = "copy-fallback";
      box.className = "cl-copy-fallback";
      box.innerHTML = "<label>Automatic copy was blocked. Select all below, then copy:</label>";
      const ta = document.createElement("textarea");
      ta.readOnly = true;
      const close = document.createElement("button");
      close.type = "button";
      close.textContent = "Close";
      close.addEventListener("click", () => box.remove());
      box.appendChild(ta);
      box.appendChild(close);
      document.body.appendChild(box);
    }
    const ta = box.querySelector("textarea");
    ta.value = text;
    ta.focus();
    ta.select();
  }

  function doCopy() {
    const result = buildResult();
    const n = Object.keys(result).length;
    if (!n) return;
    const text = JSON.stringify(result, null, 2);
    const ok = () => showToast(`Copied ${n} items, paste into chat`);
    if (copySync(text)) { ok(); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      let settled = false;
      const timer = setTimeout(() => {           // hung promise must still surface a fallback
        if (!settled) { settled = true; manualCopyFallback(text); }
      }, 1200);
      navigator.clipboard.writeText(text).then(
        () => { if (!settled) { settled = true; clearTimeout(timer); ok(); } },
        () => { if (!settled) { settled = true; clearTimeout(timer); manualCopyFallback(text); } }
      );
      return;
    }
    manualCopyFallback(text);
  }

  document.getElementById("copy").addEventListener("click", doCopy);

  // Keyboard shortcut. Call doCopy() inline, NEVER via copyBtn.click(): a synthetic click
  // loses the user gesture in some browsers, which breaks the clipboard write.
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && !e.shiftKey && !e.altKey && e.key === "Enter") {
      const btn = document.getElementById("copy");
      if (btn && !btn.disabled) { e.preventDefault(); doCopy(); }
    }
  });
</script>
```

## Scaffold §4: Drag-drop with keyboard support


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

## Scaffold §6: Responsive layout


The phone-first container, auto-collapsing grid, safe-area-aware floating button, and table wrapper. Copy the bits the artifact needs.

```html
<style>
  /* Backstop: never allow sideways scroll on a phone. */
  html, body { overflow-x: hidden; }
  body { margin: 0; }

  /* Fluid container: capped on desktop, gutters on phone. */
  .container {
    width: min(720px, 100% - 2rem);
    margin-inline: auto;
    padding-block: 2rem;
  }

  /* Fluid display type — scales down on narrow screens, never below body size. */
  h1 { font-size: clamp(1.75rem, 6vw, 3rem); line-height: 1.1; }
  h2 { font-size: clamp(1.25rem, 4vw, 1.75rem); }
  body { font-size: 16px; }            /* 1rem floor — keeps iOS from auto-zooming */
  input, select, textarea { font-size: 16px; }  /* same reason, specifically for fields */

  /* Auto-collapsing card grid: reflows to fewer columns as width shrinks, no media query needed. */
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
  }

  /* Touch targets: every tappable control clears 44px. */
  .btn, button, a.btn, .pill, .toggle {
    min-height: 44px;
    display: inline-flex; align-items: center; justify-content: center;
    padding: 0 16px;
  }

  /* Floating action button that clears the iPhone home indicator and never sits under the notch. */
  .fab {
    position: fixed;
    right: calc(16px + env(safe-area-inset-right));
    bottom: calc(16px + env(safe-area-inset-bottom));
    z-index: 1000;
  }
  /* When a fab is present, pad the page bottom so it can't cover the last row. */
  .container { padding-bottom: calc(2rem + 64px); }

  /* Side-by-side compare → stacks vertically on phone. */
  .compare { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  @media (max-width: 640px) {
    .compare { grid-template-columns: 1fr; }
  }

  /* Wide tabular data: allow horizontal scroll WITHIN the table only, not the page. */
  .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
</style>

<div class="table-scroll">
  <table><!-- wide table here --></table>
</div>
```

For a custom-editor that ships to a phone, pair this with a tap-to-move handler alongside the §4 drag-drop (tap a card to select, tap a column to drop):

```html
<script>
  // Touch fallback for drag-drop: native dragstart doesn't fire on touch.
  let selected = null;
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("click", () => {
      if (selected === card) { card.classList.remove("picked-up"); selected = null; return; }
      selected?.classList.remove("picked-up");
      selected = card; card.classList.add("picked-up");
    });
  });
  document.querySelectorAll(".column").forEach((col) => {
    col.addEventListener("click", (e) => {
      // Only treat clicks on the column background (not on a card) as a drop.
      if (selected && !e.target.closest(".card")) {
        (col.querySelector("[data-cards]") ?? col).appendChild(selected);
        selected.classList.remove("picked-up");
        selected = null;
      }
    });
  });
</script>
```

## Scaffold §7: retired

Artifacts ship with no comment layer, no Copy-comments bar, no Send-to-Claude button and no
relay; feedback comes back in chat. The number stays claimed because other skills cite these
identifiers. Do not renumber, and do not reuse §7 for something else.

## Scaffold §8: Report navigation

Solves the "where am I" half of report disorientation. The narrative spine
(`references/narrative.md`) fixes what a report says and in what order; this fixes the
reader's ability to locate themselves inside it. A long report without it is a scroll with
no landmarks: you cannot tell how much is left, cannot jump to the part you came back for,
and cannot resume where you stopped.

**Install it, do not hand-copy it:**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/install_report_nav.py" report.html \
    --section-root ".container" \
    --heading "h2" \
    --alias paper=--card --alias rule=--line --alias accent=--indigo
```

`--check` reports install status and audits the spine without editing anything.

### What it renders

- **A sticky contents rail** on desktop, listing every heading under `--section-root`,
  **numbered automatically** so the reader can say "4 of 7" without the author hand-numbering
  anything. Numbering is derived at runtime, so adding a section never desynchronises it.
- **Scroll-spy**: the current section is marked as the reader moves. Use an
  `IntersectionObserver`, never a scroll handler recomputing offsets, or long reports jank.
- **A reading-progress indicator**, thin and non-decorative. It answers "how much is left",
  which is the question a long report refuses to answer otherwise.
- **A phone sheet** under 640px. A fixed side rail is unusable at that width, so the rail
  collapses to a tappable control that opens a sheet of the same numbered list. The floor in
  SKILL.md applies unchanged: 44px minimum target, no horizontal scroll at 360px.

### Rules

- **Tokens.** The layer expects the §1 names (`--paper`, `--rule`, `--rule-2`, `--accent`,
  `--mono`, `--sans`). An artifact using its own names must pass `--alias`, exactly as the
  collapse layer requires, or `var()` falls back to literals and dark mode breaks.
- **Dark mode on every colour.** Same rule as everywhere: no colour may have its only
  definition inside a light-mode block.
- **`prefers-reduced-motion`** suppresses the scroll-spy transition and any smooth-scroll on
  jump. Movement the reader did not ask for is exactly what that setting is about.
- **Degrade to nothing.** A report with fewer than three headings does not need a rail, and
  the script must no-op rather than render an empty one. Guard on the heading count.

## Scaffold §9: Collapse layer (collapsed by default)

**Every section and every card in a read-mostly artifact is collapsible, and collapsed by
default.** This is the default for reports, analyses, dashboards, plans, research
syntheses, prep docs, and verification reports, installed from the canonical file.

**Don't hand-write it; install it from the canonical file** so every artifact stays in sync:

```
${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/templates/collapse-layer.html   # source of truth
${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/install_collapse_layer.py       # splices it into a file
```

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/how-to-html/install_collapse_layer.py" report.html \
    --collapsible "section, .card" --default collapsed \
    --alias paper=--card --alias rule=--line --alias accent=--indigo
```

`--check` reports install status, `--upgrade` replaces an older layer in place, `--uninstall`
takes it back out, `--self-test` exercises all four paths plus the namespace guard.

**Why collapsed and not merely collapsible.** An artifact that opens fully expanded has no
shape: on a phone the two-minute version and the appendix scroll identically, and coming
back for one section means thumbing past everything already read. Collapsed-by-default makes
the file an index of itself, which is the mode these artifacts are actually read in (phone,
days later, looking for one thing). It costs one tap on the section you want and saves the
scroll through the six you don't.

### What it does

- **The heading becomes the control.** Every element matching `COLLAPSIBLE` that owns a
  direct-child heading gets that heading turned into a disclosure control: chevron,
  `role="button"`, `aria-expanded`, `aria-controls`, Enter/Space, 44px row on phone.
  Everything after the heading is wrapped in a `.cx-body`.
- **A closed section still says how much is inside** (`4 items`, `12 rows`, `3 paras`), so a
  collapsed heading is a summary, not a mystery. The count is hidden while the section is open.
- **Find-in-page still works.** The body is hidden with `hidden="until-found"`, so Ctrl+F (and
  the phone's find bar) matches inside a closed section and the `beforematch` handler opens
  it around the hit. Browsers without support degrade to `display: none` plus the toggle.
- **One Expand all / Collapse all**, docked into the §8 rail when installed and floating
  **bottom-left** when not. Bottom-right is free since §7 was retired, but keep this one
  bottom-left: two floating stacks in one corner is how a phone artifact loses its last section,
  and the 203 artifacts that still carry a baked layer put their action bar bottom-right.
- **State persists** per artifact in `localStorage`, so returning to a report resumes where
  the reading stopped. Wrapped in try/catch; a private window just reads as all-default.
- **A `#hash` opens what it points into**, ancestors included, before the scroll lands.
  Otherwise a shared anchor drops the reader on a heading with nothing under it.
- **Print is the whole artifact**, never the index of it: `beforeprint` opens everything and
  `afterprint` restores, and the print stylesheet forces `.cx-body[hidden]` visible as a floor.
- **JS-rendered content is picked up.** Most of these artifacts build their sections from a
  data blob after the layer's script runs, so a one-shot scan at parse time finds nothing and
  the page ships with no controls at all. A debounced `MutationObserver`
  re-scans new subtrees, pausing itself around the layer's own DOM writes, and never re-closes
  a group the reader has already opened. `window.cxCollapseRefresh()` is the explicit hook for
  a template that would rather call it than wait.
- **A header row counts as the heading.** Card and column headers are routinely a
  `<div class="col-header"><h2>…</h2><span>count</span></div>` rather than a bare `<h2>`, so
  the first child element that *wraps* a heading is used when there is no direct heading child.
  First child only, so a heading further down the body is never hoisted into a header.
- **The header swallows its own events.** `pointerdown`, `pointerup` and `click` stop at the
  header (except on a link or form control inside it). A host that treats the whole block as a
  drop target sees `closest(".card") === null` for a header tap and would otherwise read the
  toggle as a drop: a card board that binds `pointerup` on `.column` would otherwise file a
  card on a phone tap on a column header.

### The three things to tune per artifact

- **`COLLAPSIBLE`** — which blocks collapse. Default `"section, .card, .finding, .phase,
  article"`. Widen it to the artifact's own block classes; do not widen it to `div`.
- **`COLLAPSE_DEFAULT`** — `"collapsed"` (default) or `"expanded"`. Use `expanded` only for
  an artifact genuinely read top-to-bottom in one pass: a slide deck, a one-screen dashboard,
  a page with three sections. It still installs the affordance; it only changes initial state.
- **`KEEP_FIRST_OPEN`** — default `true`. The opening section of a report is the orientation
  line and the answer, which must never be behind a click. A report's whole spine
  (`references/narrative.md`) depends on the answer being visible without interaction.

**Typical settings:**

| Artifact | `--collapsible` | `--default` |
|---|---|---|
| Report or dashboard | `section.card, section` | `collapsed` |
| `create-plan/templates/plan-template.html` | `section, .phase, .task` | `collapsed` |
| Card board (drag-drop triage) | `section.column` | `expanded` |

Card boards are `expanded` because their whole job is a decision taken across visible
columns: a board that opens with every bucket shut cannot be triaged. They still get the
affordance, which is what a long column actually needs.

Per-element overrides, for the cases the constants cannot express: `data-collapse="open"`
starts one section open, `data-collapse="off"` opts one out of collapsing entirely, and
`data-no-collapse` on an ancestor exempts a whole subtree.

### What it never touches

Legacy annotation chrome (`.cl-*`, `.claude-response`), the §8 nav rail, anything under `[data-no-collapse]`, and any element with no heading
to hang the control off (there is nothing to click, so collapsing it would hide content behind
no affordance).

### It composes with §8, in that order

Install the collapse layer first, then the nav: the collapse layer rewrites headings and moves
content into `.cx-body` wrappers, so the nav must see the final structure.

### The namespace, and the guard that ate its own chevron

**Every class this layer creates is `cx-` prefixed**, and the guard below enforces it. The collision guard at the top of the style block
carries one non-obvious clause:

```css
.cx-head > span:not([class*="cx-"]),
.cx-bar button > span:not([class*="cx-"]) { border: 0; margin: 0; /* … */ }
```

The `:not([class*="cx-"])` is load-bearing. Without it the guard matches the layer's own
spans and **wins on specificity** ((0,1,1) against a bare `.cx-chevron`'s (0,1,0)): `border: 0`
computes `border-right-style: none` on every chevron, so the
affordance is invisible on every heading, and `margin: 0` kills the count chip's
`margin-left: auto` so it sits glued to the heading text. Nothing errors and the
deterministic checks pass. `--self-test` now asserts the clause.
