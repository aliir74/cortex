---
name: figma-cli
description: Use when reading Figma design files — inspecting screens/frames, extracting the node tree, pulling copy/text, or rendering a node to PNG/SVG for a design or engineering analysis. Triggers on a figma.com/design URL, "check the Figma", "read the Figma", "what's in the Figma", "render the Figma frame", "figma node".
model: sonnet
---

# Figma with the `figma` CLI

A thin, stdlib-only Python wrapper over the Figma REST API that ships inside this skill. **Read-only**: it fetches node trees and renders node images. Figma's canvas is opaque to screenshot/DOM tools, so structured node data plus rendered PNGs beat interpreting pixels.

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/figma-cli/figma" whoami
```

Every `figma ...` example below means `"${CLAUDE_PLUGIN_ROOT}/skills/figma-cli/figma" ...`.

## Prerequisites

Requires `python3` and a Figma personal access token. If the token is missing (`figma whoami` fails with "No Figma token found"), point the user to `SETUP.md` at the plugin root (section: **figma-cli**) and stop until it's available.

## Auth

Token resolution, first hit wins:
1. `$FIGMA_TOKEN`
2. `~/.figma.env` (chmod 600), a line `FIGMA_TOKEN=figd_...`

Never put the token on a command line that lands in shell history. Verify with `figma whoami` (GET /v1/me).

## Inputs it accepts

- **File:** a bare file key **or** a full URL (`https://www.figma.com/design/<key>/<name>?node-id=...`). The wrapper extracts the key.
- **Node id:** either `123-45` (URL form) or `123:45` (API form), normalized automatically.

## Quick Reference

| Task | Command |
|------|---------|
| Verify token | `figma whoami` |
| Outline a frame's subtree (best first look) | `figma tree <url-or-key> <node> --depth 3` |
| Outline + show every text string | `figma tree <url-or-key> <node> --depth 4 --text` |
| Raw JSON for one/more nodes | `figma nodes <url-or-key> <node> [<node2> ...] --depth 2` |
| Render node(s) to PNG @2x into a dir | `figma image <url-or-key> <node> -o ./out` |
| Render SVG or PDF | `figma image <url-or-key> <node> --format svg -o ./out` |
| Whole-file tree (can be huge, cap depth) | `figma tree <url-or-key> --depth 2` |

## Read vs Write Operations

**Read (all commands):** whoami, tree, nodes, file, image. This CLI cannot modify Figma, so no permission hook is needed.

## Typical flow for a design pass

0. **Probe every Figma link you were given before reading anything else:** `figma nodes <file> <id1> <id2> ... --depth 0`. A `null` entry means the id is dead (deleted, or the file was reorganised); every later step built on it is guesswork. Ask for fresh links before continuing.
1. `figma tree <url> <node> --depth 2` → see the top-level frames/screens under the node.
2. Pick the screen frames; `figma tree <url> <frame> --depth 5 --text` → read their copy and structure.
3. `figma image <url> <frame1> <frame2> ... -o ./figma-renders` → render each screen, then Read the PNGs to view them.
4. Compare against the current implementation to state what changes.
5. **Measure the numbers, do not eyeball them.** A side-by-side render cannot see a 10px height delta, a 4px-vs-16px radius, or a gap one scale step off. Pull `absoluteBoundingBox`, `cornerRadius`, `itemSpacing` and `padding*` from `figma nodes ... --depth 4` JSON and compare them against the implementation's computed styles. Figma omits padding, `itemSpacing` and `cornerRadius` when they are zero, so a missing key means 0, not unknown.

## Notes

- `image` returns short-lived Figma S3 URLs and downloads them immediately; filenames are the node id with `:`→`-`.
- Default render scale is 2x. Bump with `--scale 3` for dense screens.
- For a huge frame, prefer `tree` (compact outline) over `nodes`/`file` (full JSON).

## Behavioral Rules

- Read-only tool; nothing it does is outward-facing. Treat design files as internal: do not paste their contents into third-party services unless the user asks.
- Prefer `tree`/`image` for analysis; reach for `nodes`/`file` raw JSON only when you need exact properties (fills, layout, constraints, tokens).

## Gotchas

- **Node ids in tickets go stale.** Probe them with `figma nodes <file> <id> ... --depth 0` before citing them.
- **Read copy from `tree --text`, not from the render.** Node names tell you what a string is (a `Label` under a button instance is a button label). Reading a screenshot can swap a title and a button label.
- **Section renders are not references.** A section renders as a huge mostly-empty canvas. Render frames one at a time.
- **Locating numbered frames:** `figma nodes <section> --depth 1` returns each child's `absoluteBoundingBox`; sort children by y then x to map them onto the section render.
