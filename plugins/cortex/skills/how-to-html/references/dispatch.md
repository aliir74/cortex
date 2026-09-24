# Dispatching a render to a sub-agent (NOT the default)

An inline build is several times cheaper than a dispatched renderer. Dispatch is therefore OFF by default. Use it only when the main thread genuinely cannot hold the work (a very large deck, or a render that must run while you do something else), and say why when you do.

### Dispatching the renderer

Use the Agent tool with `model: sonnet` and `name: "html-render-<slug>"` so follow-ups can `SendMessage` to it. Use `model: opus` only for a custom editor with real interaction state (drag state machine, multi-step JSON build). The brief is this, filled in, nothing added from the conversation:

```
Render an HTML artifact from a content file.

Content file (authoritative): <abs path>.content.md
Output: <abs path>.html
Skill: invoke /cortex:how-to-html first, then read references/render.md in that skill's
directory and the reference files it names for this artifact (narrative.md for a report,
charts.md for any chart or diagram, scaffolds.md for the shell and any interactive block).

The content file is authoritative: every sentence in the HTML is a sentence from the content
file, every heading is one of its headings, every chart or diagram is one it asks for. You add
page chrome only (nav labels, button text, axis labels, toast text). Do not add sections, do
not paraphrase, do not summarise, do not append caveats.

Then, in order: verify_diagrams.py, the class-coverage check, THEN the collapse layer via
install_collapse_layer.py (--collapsible matched to this artifact's own section and card
classes, --default from the content header), then install_report_nav.py for a report. Do NOT
add any annotation or comment layer. Do NOT open the artifact in a browser: no screenshots, no
viewport checks. Do not open the file for the user and do not edit any task records.

Report back in exactly this shape:
  path: <abs path>.html
  deterministic: <verifier result> / <class coverage result>
  layers: <collapse layer: collapsible selector + default, or "none">
  deviations: <anything in the content file you could not render as asked, or "none">
```

The agent runs in the background; do other work and wait for its report. Never predict it.
