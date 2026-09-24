---
name: md-to-pdf
description: Use when user wants to convert/export a markdown file (including Obsidian-flavoured markdown) to PDF, typically for an email attachment, an upload to an external tool, or any place that needs a PDF copy of a note. Triggers on "export to pdf", "convert to pdf", "make pdf from this", "generate pdf", "save as pdf", or any request to produce a PDF from a markdown file.
---

# md-to-pdf

Convert a markdown file to a clean PDF using pandoc + headless Chrome/Chromium.

## Prerequisites

Requires `pandoc`, Google Chrome or Chromium, and Python 3 (stdlib only). If any is missing, point the user to `SETUP.md` at the plugin root (section: **md-to-pdf**) and stop until it's available.

## What it does

1. Strips YAML frontmatter (so it doesn't render as a duplicate title block above the H1)
2. Resolves Obsidian wikilinks: `[[path|label]]` → `label`, `[[name]]` → last segment of `name`
3. Adds a hard line break after each top-block metadata line (`**Owner:** ...`, `**Date:** ...`) so they render as separate lines, not one paragraph
4. Renders standalone HTML styled by `style.css`, with images base64-inlined
5. Prints HTML → PDF with headless Chrome, no headers/footers

## Usage

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/md-to-pdf/md-to-pdf.py" INPUT.md [OUTPUT.pdf]
```

- `INPUT.md`: absolute or relative path to the source markdown
- `OUTPUT.pdf` (optional): defaults to the input path with a `.pdf` extension, next to the source file

The script prints the absolute output path. The browser is found via `$CHROME_PATH`, then `google-chrome` / `chromium` on `PATH`, then the macOS app bundle.

## In conversation

1. Identify the input file (the file just edited, or the path the user names).
2. Run the script with the absolute path.
3. Open the PDF for review (`open` on macOS, `xdg-open` on Linux).
4. If the user spots formatting issues, edit `style.css` and rerun; don't recreate the conversion inline.

## Customising styles

Edit `style.css` in this skill folder. Keep it minimal: clean, readable document output, not a designer template. A plugin update replaces this file, so keep a copy of any custom styling.

**Images:** reference them by plain filename with the file next to the source `.md`, using standard `![alt](name.png)`. A wikilink embed `![[name.png]]` is stripped to text. The script resolves image paths against the source directory and inlines them; `style.css` caps `img` at `max-width: 100%` so wide screenshots aren't cropped on the print page. Always eyeball the rendered PDF: a cropped or missing image still produces a valid-looking file.

**Tables need explicit CSS.** pandoc HTML gets no default table styling. `style.css` sets `border-collapse`, borders, padding, and row-level `break-inside: avoid`. If tables render without borders or split badly, check `style.css` first.

## Why pandoc + Chrome instead of LaTeX

LaTeX engines are a heavy install (several GB). pandoc + headless Chrome is fast (~1s end to end), produces clean system typography, and preserves markdown fidelity (lists, tables, code blocks, inline links).
