#!/usr/bin/env python3
"""verify-diagrams.py — deterministic geometry linter for inline-SVG charts/diagrams.

The recurring "diagram border problem" is always the same root cause: a label or
shape is placed OUTSIDE the SVG's `viewBox` box. With `overflow: visible` it then
paints past the parent card edge; with clipping it gets silently cut off. Either
way it looks broken. Prose telling Claude to "budget the gutters" hasn't fixed it
because the gutter math is done by hand and gets it wrong.

This script removes the hand-math from the trust path. It parses every chart SVG
in an HTML file and checks that EVERY drawable element (text, rect, line, circle,
polyline, polygon, ellipse, path-ish) lies within its `viewBox`, accounting for:
  - non-zero viewBox min-x / min-y
  - accumulated `transform="translate(...)"` from ancestor <g> groups and the
    element itself
  - text width estimated from char count x font-size (monospace chart text),
    respecting `text-anchor` (start / middle / end)
  - text ascent/descent above & below the baseline
  - stroke half-width spilling past a shape edge

Elements (or ancestors) carrying rotate/scale/matrix/skew transforms are skipped
for geometry (their bbox can't be derived cheaply) so we never false-positive on
the progress-ring rotation trick. Anything that fails to parse degrades to "no
violation" — this tool only ever reports things it is confident are out of bounds.

Usage:
    python3 verify-diagrams.py FILE.html [FILE2.html ...]
    python3 verify-diagrams.py --self-test     # lint the scaffolds in SKILL.md

Exit code 0 = clean (or nothing to check), 1 = at least one violation.
Stdlib only.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# --- tunables -------------------------------------------------------------
# Per-char width as a fraction of font-size. Chart text is monospace
# (`.chart text { font-family: var(--mono) }`); mono glyphs are ~0.6em wide.
# The skill's own constant is 6.5 units at font-size 11 == 0.59. Use 0.6.
CHAR_W = 0.60
ASCENT = 0.80   # text rises this fraction of font-size above the baseline
DESCENT = 0.22  # ...and drops this fraction below it
EPS = 1.0       # tolerance in user units before something counts as "outside"
STROKE_PAD = 1.0  # half a typical stroke spilling past a shape edge
DEFAULT_FS = 11.0       # `.chart text` default font-size
TITLE_FS = 12.0         # `.chart .chart-title` font-size

_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.IGNORECASE | re.DOTALL)
_FS_STYLE_RE = re.compile(r"font-size\s*:\s*([\d.]+)")
_TRANSLATE_RE = re.compile(r"translate\(\s*([-\d.]+)(?:[ ,]+([-\d.]+))?\s*\)")
_OTHER_TF_RE = re.compile(r"\b(rotate|scale|matrix|skew[XY]?)\s*\(")


@dataclass
class Violation:
    svg_index: int
    aria: str
    element: str
    detail: str
    extent: tuple[float, float, float, float]  # left, right, top, bottom
    box: tuple[float, float, float, float]      # minx, maxx, miny, maxy


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if "}" in tag else tag.lower()


def _num(val: str | None, default: float = 0.0) -> float:
    if val is None:
        return default
    m = re.search(r"-?[\d.]+", val)
    return float(m.group()) if m else default


def _font_size(el: ET.Element) -> float:
    style = el.get("style", "") or ""
    m = _FS_STYLE_RE.search(style)
    if m:
        return float(m.group(1))
    fs_attr = el.get("font-size")
    if fs_attr:
        return _num(fs_attr, DEFAULT_FS)
    cls = el.get("class", "") or ""
    if "chart-title" in cls:
        return TITLE_FS
    return DEFAULT_FS


def _anchor(el: ET.Element) -> str:
    style = el.get("style", "") or ""
    m = re.search(r"text-anchor\s*:\s*(start|middle|end)", style)
    if m:
        return m.group(1)
    return (el.get("text-anchor") or "start").strip().lower()


def _text_len(el: ET.Element) -> int:
    """Visible char count (entities already decoded by the XML parser)."""
    return len("".join(el.itertext()).strip())


def _stroke_w(el: ET.Element) -> float:
    style = el.get("style", "") or ""
    m = re.search(r"stroke-width\s*:\s*([\d.]+)", style)
    if m:
        return float(m.group(1))
    return _num(el.get("stroke-width"), 0.0)


def _parse_transform(el: ET.Element) -> tuple[float, float, bool]:
    """Return (dx, dy, has_complex_transform) for this element's own transform."""
    tf = el.get("transform", "") or ""
    if not tf:
        return 0.0, 0.0, False
    complex_tf = bool(_OTHER_TF_RE.search(tf))
    dx = dy = 0.0
    for m in _TRANSLATE_RE.finditer(tf):
        dx += float(m.group(1))
        dy += float(m.group(2)) if m.group(2) is not None else 0.0
    return dx, dy, complex_tf


def _element_extent(
    el: ET.Element, ox: float, oy: float
) -> tuple[str, tuple[float, float, float, float]] | None:
    """(label, (left, right, top, bottom)) in viewBox coords, or None to skip."""
    tag = _localname(el.tag)

    if tag == "text":
        x = _num(el.get("x")) + ox
        y = _num(el.get("y")) + oy
        fs = _font_size(el)
        w = _text_len(el) * CHAR_W * fs
        anchor = _anchor(el)
        if anchor == "middle":
            left, right = x - w / 2, x + w / 2
        elif anchor == "end":
            left, right = x - w, x
        else:
            left, right = x, x + w
        top = y - ASCENT * fs
        bottom = y + DESCENT * fs
        snippet = "".join(el.itertext()).strip()[:24]
        return f'text "{snippet}"', (left, right, top, bottom)

    if tag == "rect":
        x = _num(el.get("x")) + ox
        y = _num(el.get("y")) + oy
        w = _num(el.get("width"))
        h = _num(el.get("height"))
        s = _stroke_w(el) / 2
        return "rect", (x - s, x + w + s, y - s, y + h + s)

    if tag in ("line",):
        x1 = _num(el.get("x1")) + ox
        x2 = _num(el.get("x2")) + ox
        y1 = _num(el.get("y1")) + oy
        y2 = _num(el.get("y2")) + oy
        s = _stroke_w(el) / 2
        return "line", (min(x1, x2) - s, max(x1, x2) + s, min(y1, y2) - s, max(y1, y2) + s)

    if tag == "circle":
        cx = _num(el.get("cx")) + ox
        cy = _num(el.get("cy")) + oy
        r = _num(el.get("r"))
        s = _stroke_w(el) / 2
        return "circle", (cx - r - s, cx + r + s, cy - r - s, cy + r + s)

    if tag == "ellipse":
        cx = _num(el.get("cx")) + ox
        cy = _num(el.get("cy")) + oy
        rx = _num(el.get("rx"))
        ry = _num(el.get("ry"))
        s = _stroke_w(el) / 2
        return "ellipse", (cx - rx - s, cx + rx + s, cy - ry - s, cy + ry + s)

    if tag in ("polyline", "polygon"):
        pts = re.findall(r"(-?[\d.]+)[ ,]+(-?[\d.]+)", el.get("points", "") or "")
        if not pts:
            return None
        xs = [float(px) + ox for px, _ in pts]
        ys = [float(py) + oy for _, py in pts]
        s = _stroke_w(el) / 2
        return "polyline", (min(xs) - s, max(xs) + s, min(ys) - s, max(ys) + s)

    return None  # path, defs, marker, unknown — not geometry-checked


def _walk(
    el: ET.Element, ox: float, oy: float, frozen: bool, out: list
) -> None:
    """Depth-first, accumulating translate offsets; freeze on complex transforms."""
    dx, dy, complex_tf = _parse_transform(el)
    nox, noy = ox + dx, oy + dy
    nfrozen = frozen or complex_tf

    tag = _localname(el.tag)
    if tag in ("defs", "marker", "clippath", "mask", "lineargradient", "radialgradient"):
        return  # template/paint defs are never drawn in place

    if not nfrozen:
        ext = _element_extent(el, nox, noy)
        if ext is not None:
            out.append((tag, *ext))

    for child in el:
        _walk(child, nox, noy, nfrozen, out)


def _check_svg(svg_text: str, index: int) -> list[Violation]:
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError:
        return []  # malformed fragment — don't guess

    vb = root.get("viewBox")
    if not vb:
        return []  # no coordinate system to check against
    nums = re.findall(r"-?[\d.]+", vb)
    if len(nums) != 4:
        return []
    minx, miny, w, h = (float(n) for n in nums)
    maxx, maxy = minx + w, miny + h

    # Only lint charts/diagrams: must carry class="chart" OR contain text.
    cls = root.get("class", "") or ""
    has_text = any(_localname(e.tag) == "text" for e in root.iter())
    if "chart" not in cls and not has_text:
        return []

    aria = (root.get("aria-label") or "")[:60]
    collected: list = []
    for child in root:
        _walk(child, 0.0, 0.0, False, collected)

    violations: list[Violation] = []
    for _tag, label, (left, right, top, bottom) in collected:
        is_text = label.startswith("text")
        pad = 0.0 if is_text else STROKE_PAD
        msgs = []
        if left < minx - EPS - pad:
            msgs.append(f"left edge {left:.1f} < {minx:.1f}")
        if right > maxx + EPS + pad:
            msgs.append(f"right edge {right:.1f} > {maxx:.1f}")
        if top < miny - EPS - pad:
            msgs.append(f"top edge {top:.1f} < {miny:.1f}")
        if bottom > maxy + EPS + pad:
            msgs.append(f"bottom edge {bottom:.1f} > {maxy:.1f}")
        if msgs:
            violations.append(
                Violation(index, aria, label, "; ".join(msgs),
                          (left, right, top, bottom), (minx, maxx, miny, maxy))
            )
    return violations


def check_html(text: str) -> list[Violation]:
    out: list[Violation] = []
    for i, m in enumerate(_SVG_RE.finditer(text)):
        out.extend(_check_svg(m.group(), i))
    return out


def _format(path: str, violations: list[Violation]) -> str:
    lines = [f"\n{len(violations)} diagram overflow violation(s) in {path}:"]
    for v in violations:
        where = f' (aria: "{v.aria}")' if v.aria else ""
        lines.append(
            f"  svg #{v.svg_index}{where}: {v.element} escapes viewBox "
            f"[{v.box[0]:.0f}..{v.box[1]:.0f} x {v.box[2]:.0f}..{v.box[3]:.0f}] "
            f"-> {v.detail}"
        )
    lines.append(
        "  Fix: widen the viewBox to contain the label, shorten the label, or "
        "re-anchor it (end-anchor near the right edge, start near the left). "
        "Do NOT rely on overflow to hide it."
    )
    return "\n".join(lines)


def _self_test() -> int:
    import pathlib
    skill = pathlib.Path(__file__).with_name("SKILL.md")
    text = skill.read_text(encoding="utf-8")
    v = check_html(text)
    if v:
        print(_format(str(skill), v))
        return 1
    print("SKILL.md scaffolds: all chart SVGs pass geometry check.")
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 0
    if argv[0] == "--self-test":
        return _self_test()
    rc = 0
    for path in argv:
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except OSError as e:
            print(f"skip {path}: {e}", file=sys.stderr)
            continue
        violations = check_html(text)
        if violations:
            print(_format(path, violations))
            rc = 1
    if rc == 0:
        print("No diagram overflow violations.")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
