---
name: make-slides
description: "Use when user wants to build an HTML slide deck: pitch deck, research synthesis, brand manifesto, classroom material, talk slides, founder pitch, etc. Triggers on 'make slides', 'build a deck', 'slide deck', 'create slides', 'pitch deck', or explicit /make-slides command."
disable-model-invocation: true
argument-hint: "<what the deck is for>"
---

# Make Slides: Beautiful HTML Slide Deck

Builds an HTML slide deck using the [beautiful-html-templates](https://github.com/zarazhangrui/beautiful-html-templates) library by Zara Zhang (agent-curated templates, MIT licensed).

If the `how-to-html` skill is installed, load it for the shared HTML conventions (design principles, dark mode, tech-stack rules, accessibility floor). The template library stays the visual source of truth; `how-to-html` supplies the overlay rules.

## Prerequisites

Requires `git` (to fetch the template library). See `SETUP.md` at the plugin root (section: **make-slides**).

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/make-slides.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/make-slides/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/make-slides.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/make-slides.md` — edit anytime to customize."
2. Read it. Empty fields fall back to the defaults below:
   - `templates_dir` (default `${CLAUDE_PLUGIN_DATA}/beautiful-html-templates`): local clone of the library.
   - `output_dir` (default `./decks`): where previews and the final deck are written, relative to the current working directory unless absolute.

## Library location

Use the clone at `templates_dir`. If it doesn't exist, clone it once:

```bash
git clone https://github.com/zarazhangrui/beautiful-html-templates "<templates_dir>"
```

Do not re-clone on every run. Pull (`git -C "<templates_dir>" pull`) only if the user asks for the latest templates or the clone looks stale (>30 days since the last commit).

## Operating manual

The library's `AGENTS.md` is the canonical workflow. **Read `<templates_dir>/AGENTS.md` once at the start of every deck task** and follow its six-step flow (clarify → pick 3 → preview → choose → build → open) verbatim. Do not invent shortcuts.

## Quick reference (the six steps from AGENTS.md)

1. **Ask** the user two questions: occasion + mood/vibe. Do not skip even if the brief seems obvious.
2. **Read `index.json`**, match against `mood` / `tone` / `best_for` / `formality` / `density` / `scheme`, pick **3 candidates different enough from each other** to offer a real choice.
3. **Build a real title-slide preview for each**: clone the template's first slide, replace placeholder content with the user's actual title/subtitle/author/date. Save each preview as a self-contained HTML file (keep sibling CSS/JS so it opens correctly).
4. **Open all 3 previews** in the browser (`open` on macOS, `xdg-open` on Linux), give the three absolute paths with a one-line tone description each, ask which feels right.
5. **Build the full deck** in the chosen template. Adapt every slide per AGENTS.md §3 (preserve fonts/colors/grid/decoration; replace only headlines/body/stats/names/images). If the user needs a layout the template doesn't have, **design it from scratch using the template's design system**; do not bail or switch templates (AGENTS.md §5).
6. **Open the final deck**, give the absolute path + one-line rationale + any caveats.

## Where to save the output

Write previews and the final deck to `<output_dir>/<YYYY-MM-DD>-<slug>/`. If the surrounding workspace has its own convention (a `docs/` or `slides/` folder, rules in CLAUDE.md), follow that instead.

## Non-negotiables (from AGENTS.md §6)

- **Do not skip the clarifying step** (Step 1), even with a detailed brief.
- **Do not skip the previews** (Steps 3–4); title slides beat prose for visual choice.
- **Do not substitute fonts.** Fix the Google Fonts import if it fails; don't swap families.
- **Do not recolor.** Even small accent shifts break palette harmony.
- **Do not combine layouts from different templates.** Each template is a closed visual system.
- **Do not strip decoration** thinking it's noise: corner brackets, paper grain, SVG ornaments are part of the identity.
- **Always open** every artifact (previews, iterations, final deck) and give the absolute path.

## License

The template library is MIT licensed (copyright Zara Zhang), so it is fine for personal and commercial decks. Keep its `LICENSE` file when copying a template folder into a deliverable repo.

## When NOT to use this skill

- Reveal.js / pptx / Google Slides requests; those are different tools.
- A single-slide / one-off HTML mockup with no deck framing; just write the HTML directly.
- An existing deck the user wants to *edit* (not rebuild); open the file and edit in place.
