#!/usr/bin/env python3
"""render-plan.py — Render a plan structure to HTML using the template files.

Reads JSON from stdin with the shape:
{
  "feature_name": "Foo bar",
  "date": "2024-01-15",
  "slug": "foo-bar",
  "architecture": "Optional 2-3 sentences.",
  "architecture_diagram": {"svg": "<svg viewBox=\"0 0 800 240\" ...>...</svg>"},
  "tdd": true,
  "phases": [
    {
      "name": "Scaffold",
      "tasks": [
        {
          "id": "1.1",
          "name": "Create the file",
          "files": ["Create: path/to/foo.py", "Modify: path/to/bar.py"],
          "steps": ["Write the function", "Verify with pytest", "Commit: feat: foo"],
          "notes": {
            "rationale": "Why this task exists in 1-2 sentences.",
            "risks": ["Risk 1", "Risk 2"],
            "links": ["docs/design.md", "https://docs.example.com"]
          },
          "compare": {
            "before": "old code or structure (plain text, preserved as-is)",
            "after":  "new code or structure",
            "file":   "optional path:lines for the header label",
            "lang":   "optional language name (e.g. Python, TypeScript)"
          }
        }
      ]
    }
  ],
  "diagrams": [
    {"caption": "What X does", "svg": "<svg viewBox=\"0 0 800 240\" ...>...</svg>"}
  ]
}

All fields except feature_name/date/slug/phases are optional.
Prints the rendered HTML to stdout.
"""

from __future__ import annotations

import difflib
import html
import json
import pathlib
import re
import sys

TPL_DIR = pathlib.Path(__file__).resolve().parent.parent / "templates"

# Matches [[Page]] or [[Page|Display]] wikilinks; rendered as plain text.
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
URL_RE = re.compile(r"^(https?://\S+)$")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def render_link(item: str) -> str:
    """Render a notes link: URL → anchor, wikilink → its display text, else plain."""
    item = item.strip()
    m = WIKILINK_RE.match(item)
    if m:
        return esc(m.group(2) or m.group(1))
    m = URL_RE.match(item)
    if m:
        return f'<a href="{esc(item)}" target="_blank" rel="noopener">{esc(item)}</a>'
    return esc(item)


def render_files(files: list[str]) -> str:
    if not files:
        return " <em>(none specified)</em>"
    return " " + " · ".join(esc(f) for f in files)


def render_step(text: str) -> str:
    parts = text.split("`")
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            out.append(esc(part))
        else:
            out.append(f"<code>{esc(part)}</code>")
    rendered = "".join(out)
    return (
        '        <li class="step" data-status="pending">\n'
        '          <input type="checkbox" />\n'
        f'          <span class="step-text">{rendered}</span>\n'
        '        </li>'
    )


def render_notes(notes: dict | None) -> tuple[str, str]:
    """Returns (notes_block_html, has_notes_class).

    has_notes_class is " with-notes" or "" so the task-grid switches to a two-column layout.
    """
    if not notes:
        return "", ""
    rationale = notes.get("rationale", "").strip()
    risks = [r for r in notes.get("risks", []) if r and r.strip()]
    links = [l for l in notes.get("links", []) if l and l.strip()]
    if not (rationale or risks or links):
        return "", ""

    parts = ['        <aside class="notes">']
    if rationale:
        parts.append('          <span class="notes-label">Rationale</span>')
        parts.append(f"          <p>{esc(rationale)}</p>")
    if risks:
        parts.append('          <span class="notes-label">Risks</span>')
        parts.append("          <ul>")
        for r in risks:
            parts.append(f"            <li>{esc(r)}</li>")
        parts.append("          </ul>")
    if links:
        parts.append('          <span class="notes-label">Context</span>')
        parts.append("          <ul>")
        for l in links:
            parts.append(f"            <li>{render_link(l)}</li>")
        parts.append("          </ul>")
    parts.append("        </aside>")
    return "\n".join(parts), " with-notes"


def render_compare(compare: dict | None) -> str:
    """Render a before/after pair as a single unified git-style diff card.

    Input shape stays compatible with prior plans:
      compare: {"before": "...", "after": "...", "file": "path:lines", "lang": "Python"}
    file/lang are optional header metadata.
    """
    if not compare:
        return ""
    before = (compare.get("before") or "").rstrip("\n")
    after = (compare.get("after") or "").rstrip("\n")
    if not (before or after):
        return ""

    file_label = (compare.get("file") or "").strip()
    lang_label = (compare.get("lang") or "").strip()

    before_lines = before.split("\n") if before else []
    after_lines = after.split("\n") if after else []

    spans = []
    for raw in difflib.ndiff(before_lines, after_lines):
        tag, content = raw[:2], raw[2:]
        if tag == "? ":
            # ndiff hint lines (e.g. "^^^") are noise for our display
            continue
        if tag == "- ":
            cls = "line del"
        elif tag == "+ ":
            cls = "line add"
        else:
            cls = "line"
        body = esc(content) if content else " "
        spans.append(f'<span class="{cls}">{body}</span>')

    header_left = esc(file_label) if file_label else "Diff"
    header_right = (
        f"{esc(lang_label)} · unified diff" if lang_label else "unified diff"
    )
    return (
        '      <div class="diff-card">\n'
        '        <div class="diff-card-header">\n'
        f'          <span class="diff-file">{header_left}</span>\n'
        f'          <span>{header_right}</span>\n'
        '        </div>\n'
        f'        <pre class="diff"><code>{"".join(spans)}</code></pre>\n'
        '      </div>'
    )


def render_task(task: dict) -> str:
    tpl = (TPL_DIR / "task-template.html").read_text()
    steps_html = "\n".join(render_step(s) for s in task.get("steps", []))
    notes_block, has_notes_class = render_notes(task.get("notes"))
    compare_block = render_compare(task.get("compare"))
    return (
        tpl.replace("{{TASK_ID}}", esc(task["id"]))
        .replace("{{TASK_NAME}}", esc(task["name"]))
        .replace("{{FILES_HTML}}", render_files(task.get("files", [])))
        .replace("{{STEPS}}", steps_html)
        .replace("{{NOTES_BLOCK}}", notes_block)
        .replace("{{HAS_NOTES_CLASS}}", has_notes_class)
        .replace("{{COMPARE_BLOCK}}", compare_block)
    )


def render_phase(num: int, phase: dict) -> str:
    tpl = (TPL_DIR / "phase-template.html").read_text()
    tasks_html = "\n".join(render_task(t) for t in phase.get("tasks", []))
    return (
        tpl.replace("{{PHASE_NUM}}", str(num))
        .replace("{{PHASE_NAME}}", esc(phase["name"]))
        .replace("{{TASKS}}", tasks_html)
    )


def render_architecture_diagram(diagram: dict | None) -> str:
    if not diagram:
        return ""
    svg = diagram.get("svg", "").strip()
    if not svg:
        return ""
    return f'<section class="architecture-diagram">{svg}</section>'


def render_diagrams(diagrams: list[dict]) -> str:
    if not diagrams:
        return ""
    blocks = ['<section class="diagrams section"><h2>Diagrams</h2>']
    for d in diagrams:
        cap = esc(d.get("caption", ""))
        if cap:
            blocks.append(f'  <p class="caption">{cap}</p>')
        svg = d.get("svg", "").strip()
        if svg:
            blocks.append(f'  {svg}')
    blocks.append("</section>")
    return "\n".join(blocks)


def main() -> None:
    data = json.load(sys.stdin)
    tpl = (TPL_DIR / "plan-template.html").read_text()

    phases_html = "\n\n".join(
        render_phase(i + 1, p) for i, p in enumerate(data.get("phases", []))
    )
    arch_diagram_html = render_architecture_diagram(data.get("architecture_diagram"))
    diagrams_html = render_diagrams(data.get("diagrams", []))

    tdd_flag = "true" if data.get("tdd") else "false"
    tdd_label = "TDD" if data.get("tdd") else "no TDD"

    rendered = (
        tpl.replace("{{FEATURE_NAME}}", esc(data["feature_name"]))
        .replace("{{DATE}}", esc(data["date"]))
        .replace("{{SLUG}}", esc(data["slug"]))
        .replace(
            "{{ARCHITECTURE}}",
            esc(data.get("architecture", "")) or "<em>(fill in before execution)</em>",
        )
        .replace("{{ARCHITECTURE_DIAGRAM}}", arch_diagram_html)
        .replace("{{TDD_FLAG}}", tdd_flag)
        .replace("{{TDD_LABEL}}", tdd_label)
        .replace("{{PHASES}}", phases_html)
        .replace("{{DIAGRAMS}}", diagrams_html)
    )
    sys.stdout.write(rendered)


if __name__ == "__main__":
    main()
