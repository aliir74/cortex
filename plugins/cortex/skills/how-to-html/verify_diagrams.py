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

It ALSO catches the sibling failure mode that pure viewBox-containment misses: a
text label that sits inside the viewBox but STRADDLES the border of a card/panel
rect (a large background box). A caption placed just below a block of cards whose
own text-height pushes it back up into the cards reads as "clipped / colliding
with the border" even though the label is technically inside the viewBox. A label
must be either fully inside a panel or fully outside it; crossing the edge is the
bug. Only large container rects (area >= PANEL_RATIO x the label's own area) count
as panels, so in-bar / in-segment value labels are never flagged.

It ALSO lints connector craft on structural diagrams (flow / architecture / tree),
where the failure modes are different from chart geometry:
  - a diagonal connector segment instead of an orthogonal elbow (H then V, rounded
    bend), since diagonals read as sketch, not schematic
  - an arrow label sitting ON its connector instead of clearing it by 6-10 units
  - two connectors sharing one attach point on a box edge, so their arrowheads and
    first segments overlap
  - a connector passing behind a node it does not connect (dashed = allowed)
  - two parallel connectors sharing a corridor less than 8 units apart
Only `line`/`path` elements carrying a `marker-start`/`marker-end` count as
connectors, so sparklines, axes, grid lines and target rules are never touched.

Elements (or ancestors) carrying rotate/scale/matrix/skew transforms are skipped
for geometry (their bbox can't be derived cheaply) so we never false-positive on
the progress-ring rotation trick. Anything that fails to parse degrades to "no
violation" — this tool only ever reports things it is confident are out of bounds.

Usage:
    python3 verify-diagrams.py FILE.html [FILE2.html ...]
    python3 verify_diagrams.py --self-test     # lint the scaffolds in SKILL.md + references/*.md

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
# A rect this many times larger (by area) than a text label's own box is treated
# as a "panel" (card / background container). A label that straddles a panel's
# border is flagged. 6x is conservative: bar/segment rects that snugly hold their
# value labels never reach it, so in-segment labels are never false-positived.
PANEL_RATIO = 6.0
# --- connector craft (structural diagrams) --------------------------------
# Both axes off by more than this in one straight segment = a diagonal, not an elbow.
CONNECTOR_OFFAXIS = 4.0
# Slack before an arrow label counts as sitting ON its connector. The prose rule is a
# 6-10 unit gap; the linter only flags a genuine collision so it never nags at 5.
LABEL_CLEARANCE = 2.0
# Two connector endpoints closer than this are "the same attach point".
ATTACH_SAME = 4.0
# Class 6 (behind-node): a connector segment crossing a node rect that is not one of
# its endpoints. Only rects at least NODE_MIN on both axes count as nodes (label mask
# rects are smaller), container rects (ones that fully enclose another rect) never
# count, and a dashed connector is the documented escape hatch, so it is skipped.
NODE_MIN = 20.0
ENDPOINT_TOL = 3.0     # an end within this many units of a rect makes it an endpoint node
BEHIND_SHRINK = 2.0    # shrink the node box so a grazing segment is not a crossing
# Class 7 (corridor): two parallel segments from different connectors closer than
# CORRIDOR_MIN across, overlapping by more than CORRIDOR_OVERLAP along the axis.
CORRIDOR_MIN = 8.0
CORRIDOR_OVERLAP = 8.0

# Stable class ids, so the hook's block message and charts.md recipes line up.
CLASS_ID = {"viewbox": 1, "panel": 2, "diagonal": 3, "label-on-connector": 4,
            "attach": 5, "behind-node": 6, "corridor": 7}

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
    box: tuple[float, float, float, float]      # minx, maxx, miny, maxy (or panel rect)
    kind: str = "viewbox"                       # "viewbox" or "panel"


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


_PATH_CMD_RE = re.compile(r"([MLHVQZ])([^MLHVQZ]*)")
_PATH_UNSUPPORTED_RE = re.compile(r"[CSATcsatmlhvqz]")


@dataclass
class Connector:
    label: str
    segs: list          # [(x1, y1, x2, y2, kind)]; kind "L" straight, "Q" rounded bend
    stroke: float
    ends: list          # [(x, y), (x, y)]; the two attach points
    dashed: bool = False  # stroke-dasharray present: the "passing through" escape hatch


def _path_points(d: str) -> list | None:
    """On-path vertices for a simple absolute M/L/H/V/Q/Z path, else None.

    Q control points are dropped: a rounded elbow's curve stays inside the corner
    box its endpoints define, so the endpoints are enough for both checks."""
    if _PATH_UNSUPPORTED_RE.search(d):
        return None
    pts: list = []
    cx = cy = 0.0
    for cmd, args in _PATH_CMD_RE.findall(d):
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+", args)]
        if cmd in ("M", "L"):
            for i in range(0, len(nums) - 1, 2):
                cx, cy = nums[i], nums[i + 1]
                pts.append((cx, cy, cmd))
        elif cmd == "H":
            for n in nums:
                cx = n
                pts.append((cx, cy, "L"))
        elif cmd == "V":
            for n in nums:
                cy = n
                pts.append((cx, cy, "L"))
        elif cmd == "Q":
            for i in range(0, len(nums) - 3, 4):
                cx, cy = nums[i + 2], nums[i + 3]
                pts.append((cx, cy, "Q"))
    return pts or None


def _connector(el: ET.Element, ox: float, oy: float) -> Connector | None:
    """A marker-bearing line/path, in viewBox coords. None if not a connector."""
    if not (el.get("marker-end") or el.get("marker-start")):
        return None
    tag = _localname(el.tag)
    stroke = _stroke_w(el) or 1.0
    style = el.get("style", "") or ""
    dashed = bool(el.get("stroke-dasharray")) or "stroke-dasharray" in style
    if tag == "line":
        x1 = _num(el.get("x1")) + ox
        y1 = _num(el.get("y1")) + oy
        x2 = _num(el.get("x2")) + ox
        y2 = _num(el.get("y2")) + oy
        return Connector("connector line", [(x1, y1, x2, y2, "L")], stroke,
                         [(x1, y1), (x2, y2)], dashed)
    if tag == "path":
        pts = _path_points(el.get("d", "") or "")
        if not pts or len(pts) < 2:
            return None
        segs = []
        for (ax, ay, _ak), (bx, by, bk) in zip(pts, pts[1:]):
            segs.append((ax + ox, ay + oy, bx + ox, by + oy, bk))
        return Connector("connector path", segs, stroke,
                         [(pts[0][0] + ox, pts[0][1] + oy),
                          (pts[-1][0] + ox, pts[-1][1] + oy)], dashed)
    return None


def _seg_hits_box(seg, left: float, right: float, top: float, bottom: float,
                  pad: float = 0.0) -> bool:
    """Liang-Barsky: does the segment cross the (padded) axis-aligned box?"""
    x1, y1, x2, y2, _kind = seg
    left -= pad
    right += pad
    top -= pad
    bottom += pad
    dx, dy = x2 - x1, y2 - y1
    ps = (-dx, dx, -dy, dy)
    qs = (x1 - left, right - x1, y1 - top, bottom - y1)
    u1, u2 = 0.0, 1.0
    for pv, qv in zip(ps, qs):
        if abs(pv) < 1e-9:
            if qv < 0:
                return False
        else:
            t = qv / pv
            if pv < 0:
                u1 = max(u1, t)
            else:
                u2 = min(u2, t)
    return u1 <= u2


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
    el: ET.Element, ox: float, oy: float, frozen: bool, out: list,
    conns: list | None = None
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
        if conns is not None:
            conn = _connector(el, nox, noy)
            if conn is not None:
                conns.append(conn)

    for child in el:
        _walk(child, nox, noy, nfrozen, out, conns)


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
    conns: list = []
    for child in root:
        _walk(child, 0.0, 0.0, False, collected, conns)

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

    violations.extend(_panel_crossings(collected, index, aria))
    violations.extend(_connector_checks(collected, conns, index, aria))
    return violations


def _panel_crossings(collected: list, index: int, aria: str) -> list[Violation]:
    """Flag text labels that straddle a card/panel rect border (inside the
    viewBox but colliding with a big container box). A label must be fully inside
    a panel or fully outside it. Only rects >= PANEL_RATIO x the label's own area
    count as panels, so in-bar / in-segment value labels are never flagged."""
    rects = [ext for tag, _lbl, ext in collected if tag == "rect"]
    texts = [(lbl, ext) for tag, lbl, ext in collected if lbl.startswith("text")]
    out: list[Violation] = []
    for tlabel, (tl, tr, tt, tb) in texts:
        t_area = max(0.0, tr - tl) * max(0.0, tb - tt)
        if t_area <= 0:
            continue
        for rl, rr, rt, rb in rects:
            if (rr - rl) * (rb - rt) < PANEL_RATIO * t_area:
                continue  # too small to be a panel — skip (in-segment labels live here)
            # genuine 2D overlap by more than EPS in both axes?
            if min(tr, rr) - max(tl, rl) <= EPS or min(tb, rb) - max(tt, rt) <= EPS:
                continue
            contained = (tl >= rl - EPS and tr <= rr + EPS
                         and tt >= rt - EPS and tb <= rb + EPS)
            if contained:
                continue  # label sits cleanly inside the panel — intended
            out.append(Violation(
                index, aria, tlabel,
                "label straddles the panel border instead of clearing it; move it "
                "fully outside the card (add viewBox room) or fully inside",
                (tl, tr, tt, tb), (rl, rr, rt, rb), kind="panel"))
            break  # one report per label is enough
    return out


def _connector_checks(collected: list, conns: list, index: int,
                      aria: str) -> list[Violation]:
    """Connector craft on structural diagrams. Five classes, all conservative:

    1. diagonal: a straight segment off-axis on BOTH axes. Redraw as an elbow.
    2. label-on-connector: an arrow label whose text box actually collides with the
       line it annotates. The prose rule asks for a 6-10 unit gap; this flags only a
       real collision, so a 5-unit gap is a taste call, not a blocked write.
    3. attach: two connectors leaving or arriving at the same point on a box edge,
       so their arrowheads and first segments sit on top of each other.
    4. behind-node: a segment crossing a node rect that is neither of the
       connector's endpoints (charts.md §11 connector rule 5). Dashed connectors
       are the documented "passing through" form and are skipped.
    5. corridor: two parallel segments from different connectors running closer
       than CORRIDOR_MIN apart while overlapping along their axis (rule 4).
    """
    out: list[Violation] = []
    if not conns:
        return out

    for c in conns:
        for (x1, y1, x2, y2, kind) in c.segs:
            if kind != "L":
                continue  # a Q bend is the elbow itself
            if (abs(x2 - x1) > CONNECTOR_OFFAXIS
                    and abs(y2 - y1) > CONNECTOR_OFFAXIS):
                out.append(Violation(
                    index, aria, c.label,
                    f"diagonal segment ({x1:.0f},{y1:.0f}) -> ({x2:.0f},{y2:.0f}); "
                    "redraw as an orthogonal elbow (H then V) with a rounded r=8 bend",
                    (min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)),
                    (0.0, 0.0, 0.0, 0.0), kind="diagonal"))
                break

    texts = [(lbl, ext) for tag, lbl, ext in collected if lbl.startswith("text")]
    for tlabel, (tl, tr, tt, tb) in texts:
        for c in conns:
            pad = c.stroke / 2 + LABEL_CLEARANCE
            if any(_seg_hits_box(seg, tl, tr, tt, tb, pad) for seg in c.segs):
                out.append(Violation(
                    index, aria, tlabel,
                    "label sits on its connector; move it 6-10 units clear of the "
                    "line and back it with a paper-filled mask rect",
                    (tl, tr, tt, tb), (0.0, 0.0, 0.0, 0.0),
                    kind="label-on-connector"))
                break

    seen: list = []
    for c in conns:
        for (px, py) in c.ends:
            for (sx, sy, other) in seen:
                if other is c:
                    continue
                if abs(px - sx) <= ATTACH_SAME and abs(py - sy) <= ATTACH_SAME:
                    out.append(Violation(
                        index, aria, c.label,
                        f"shares an attach point with another connector at "
                        f"({px:.0f},{py:.0f}); spread them at least 12 units apart "
                        "along the box edge so the arrowheads do not overlap",
                        (px, px, py, py), (0.0, 0.0, 0.0, 0.0), kind="attach"))
                    break
            else:
                seen.append((px, py, c))
                continue
            break

    out.extend(_behind_node_checks(collected, conns, index, aria))
    out.extend(_corridor_checks(conns, index, aria))
    return out


def _behind_node_checks(collected: list, conns: list, index: int,
                        aria: str) -> list[Violation]:
    rects = [ext for tag, _lbl, ext in collected if tag == "rect"]
    nodes = []
    for (l, r, t, b) in rects:
        if r - l < NODE_MIN or b - t < NODE_MIN:
            continue  # label mask or decoration, not a node
        encloses_other = any(
            (ol, orr, ot, ob) != (l, r, t, b)
            and ol >= l - EPS and orr <= r + EPS and ot >= t - EPS and ob <= b + EPS
            for (ol, orr, ot, ob) in rects)
        if encloses_other:
            continue  # a zone / container box; connectors legitimately cross its border
        nodes.append((l, r, t, b))
    out: list[Violation] = []
    for c in conns:
        if c.dashed:
            continue
        for (l, r, t, b) in nodes:
            if any(l - ENDPOINT_TOL <= ex <= r + ENDPOINT_TOL
                   and t - ENDPOINT_TOL <= ey <= b + ENDPOINT_TOL for ex, ey in c.ends):
                continue  # this rect is one of the connector's own endpoints
            for seg in c.segs:
                if seg[4] != "L":
                    continue
                if _seg_hits_box(seg, l, r, t, b, pad=-BEHIND_SHRINK):
                    out.append(Violation(
                        index, aria, c.label,
                        f"passes behind a node it does not connect "
                        f"[{l:.0f}..{r:.0f} x {t:.0f}..{b:.0f}]; route around it "
                        "(extend the elbow's run before turning), or make the "
                        "connector dashed if the crossing is genuinely unavoidable",
                        (min(seg[0], seg[2]), max(seg[0], seg[2]),
                         min(seg[1], seg[3]), max(seg[1], seg[3])),
                        (l, r, t, b), kind="behind-node"))
                    break
            else:
                continue
            break
    return out


def _corridor_checks(conns: list, index: int, aria: str) -> list[Violation]:
    def axis(seg):
        x1, y1, x2, y2, kind = seg
        if kind != "L":
            return None
        if abs(y2 - y1) <= CONNECTOR_OFFAXIS and abs(x2 - x1) > CONNECTOR_OFFAXIS:
            return ("H", (y1 + y2) / 2, min(x1, x2), max(x1, x2))
        if abs(x2 - x1) <= CONNECTOR_OFFAXIS and abs(y2 - y1) > CONNECTOR_OFFAXIS:
            return ("V", (x1 + x2) / 2, min(y1, y2), max(y1, y2))
        return None
    out: list[Violation] = []
    for i, a in enumerate(conns):
        flagged = False
        for b in conns[i + 1:]:
            for sa in a.segs:
                fa = axis(sa)
                if not fa:
                    continue
                for sb in b.segs:
                    fb = axis(sb)
                    if not fb or fb[0] != fa[0]:
                        continue
                    across = abs(fa[1] - fb[1])
                    along = min(fa[3], fb[3]) - max(fa[2], fb[2])
                    if across < CORRIDOR_MIN and along > CORRIDOR_OVERLAP:
                        lo, hi = max(fa[2], fb[2]), min(fa[3], fb[3])
                        ext = ((lo, hi, fa[1], fb[1]) if fa[0] == "H"
                               else (fa[1], fb[1], lo, hi))
                        out.append(Violation(
                            index, aria, a.label,
                            f"shares a corridor with another connector "
                            f"({fa[0]} run, {across:.0f} units apart over {along:.0f} "
                            f"units); offset the two paths by at least {CORRIDOR_MIN:.0f} "
                            "units or route one around",
                            (min(ext[0], ext[1]), max(ext[0], ext[1]),
                             min(ext[2], ext[3]), max(ext[2], ext[3])),
                            (0.0, 0.0, 0.0, 0.0), kind="corridor"))
                        flagged = True
                        break
                if flagged:
                    break
            if flagged:
                break
    return out


def check_html(text: str) -> list[Violation]:
    out: list[Violation] = []
    for i, m in enumerate(_SVG_RE.finditer(text)):
        out.extend(_check_svg(m.group(), i))
    return out


def _format(path: str, violations: list[Violation]) -> str:
    lines = [f"\n{len(violations)} diagram geometry violation(s) in {path}:"]
    for v in violations:
        where = f' (aria: "{v.aria}")' if v.aria else ""
        cid = f"[class {CLASS_ID.get(v.kind, '?')}]"
        if v.kind in ("diagonal", "label-on-connector", "attach", "behind-node", "corridor"):
            lines.append(f"  {cid} svg #{v.svg_index}{where}: {v.element} -> {v.detail}")
        elif v.kind == "panel":
            lines.append(
                f"  {cid} svg #{v.svg_index}{where}: {v.element} straddles a card/panel "
                f"border [{v.box[0]:.0f}..{v.box[1]:.0f} x {v.box[2]:.0f}..{v.box[3]:.0f}] "
                f"-> {v.detail}"
            )
        else:
            lines.append(
                f"  {cid} svg #{v.svg_index}{where}: {v.element} escapes viewBox "
                f"[{v.box[0]:.0f}..{v.box[1]:.0f} x {v.box[2]:.0f}..{v.box[3]:.0f}] "
                f"-> {v.detail}"
            )
    lines.append(
        "  Fix (class 1, viewBox escape): widen the viewBox to contain the label, "
        "re-anchor it (end-anchor near the right edge, start near the left), and only "
        "then shorten it. "
        "Fix (class 2, panel straddle): give the label its own band clear of the card "
        "(more viewBox room above/below the panel) or move it fully inside. "
        "Do NOT rely on overflow to hide either. "
        "Fix (classes 3-7, connectors): orthogonal elbows only; an arrow label is "
        "moved 6-10 units clear over a paper mask rect, then the route is adjusted, "
        "then the wording is shortened, and it is never deleted; connectors sharing a "
        "box edge attach at least 12 units apart; a connector routes around any node "
        "it does not connect (or is dashed); parallel connectors sit at least 8 units "
        "apart. Recipe per class number: references/charts.md, "
        "\"What verify_diagrams.py checks, and how to fix each class\"."
    )
    return "\n".join(lines)


# Regression fixtures for the panel-crossing check (kept out of SKILL.md so the
# scaffold self-test stays clean). BAD reproduces the monorepo-combine bug: a
# caption at y=346 whose text-height pushes it up into two cards that end at y=340.
# GOOD is the same caption given its own band below the cards (taller viewBox).
_BAD_PANEL = """<svg class="chart" viewBox="0 0 900 360" role="img" aria-label="x">
  <rect x="20" y="20" width="410" height="320" rx="16" fill="#eee"/>
  <rect x="470" y="20" width="410" height="320" rx="16" fill="#eee"/>
  <text x="450" y="346" text-anchor="middle" font-size="12">no shared critical path</text>
</svg>"""
_GOOD_PANEL = """<svg class="chart" viewBox="0 0 900 372" role="img" aria-label="x">
  <rect x="20" y="20" width="410" height="320" rx="16" fill="#eee"/>
  <rect x="470" y="20" width="410" height="320" rx="16" fill="#eee"/>
  <text x="450" y="358" text-anchor="middle" font-size="12">no shared critical path</text>
</svg>"""


# Connector-craft fixtures. GOOD must pass EVERY check (it is the reference elbow
# scaffold in references/charts.md); each BAD isolates one class.
_BAD_DIAGONAL = """<svg class="chart" viewBox="0 0 200 120" role="img" aria-label="x">
  <rect x="8" y="8" width="60" height="32" fill="none" stroke="#333"/>
  <text x="38" y="28" text-anchor="middle" font-size="11">A</text>
  <line x1="68" y1="24" x2="132" y2="88" stroke="#333" marker-end="url(#arrow)"/>
  <rect x="132" y="72" width="60" height="32" fill="none" stroke="#333"/>
</svg>"""
_BAD_LABEL_ON_LINE = """<svg class="chart" viewBox="0 0 200 80" role="img" aria-label="x">
  <line x1="20" y1="40" x2="180" y2="40" stroke="#333" marker-end="url(#arrow)"/>
  <text x="100" y="42" text-anchor="middle" font-size="8">poll</text>
</svg>"""
_BAD_ATTACH = """<svg class="chart" viewBox="0 0 200 120" role="img" aria-label="x">
  <line x1="88" y1="40" x2="150" y2="40" stroke="#333" marker-end="url(#arrow)"/>
  <line x1="88" y1="40" x2="88" y2="96" stroke="#333" marker-end="url(#arrow)"/>
</svg>"""
_BAD_BEHIND = """<svg class="chart" viewBox="0 0 320 80" role="img" aria-label="x">
  <rect x="8" y="24" width="64" height="32" fill="none" stroke="#333"/>
  <rect x="128" y="24" width="64" height="32" fill="none" stroke="#333"/>
  <rect x="248" y="24" width="64" height="32" fill="none" stroke="#333"/>
  <line x1="72" y1="40" x2="248" y2="40" stroke="#333" marker-end="url(#arrow)"/>
</svg>"""
# Same topology, connector dashed: the documented "passing through" form, not flagged.
_GOOD_BEHIND_DASHED = _BAD_BEHIND.replace('stroke="#333" marker-end', 'stroke="#333" stroke-dasharray="4 3" marker-end')
# A zone box enclosing two nodes; the connector between them crosses no node and the
# zone is a container, so nothing is flagged.
_GOOD_ZONE = """<svg class="chart" viewBox="0 0 240 120" role="img" aria-label="x">
  <rect x="8" y="8" width="224" height="104" rx="8" fill="none" stroke="#999"/>
  <rect x="24" y="40" width="64" height="32" fill="none" stroke="#333"/>
  <rect x="152" y="40" width="64" height="32" fill="none" stroke="#333"/>
  <line x1="88" y1="56" x2="152" y2="56" stroke="#333" marker-end="url(#arrow)"/>
</svg>"""
_BAD_CORRIDOR = """<svg class="chart" viewBox="0 0 240 80" role="img" aria-label="x">
  <line x1="20" y1="40" x2="200" y2="40" stroke="#333" marker-end="url(#arrow)"/>
  <line x1="40" y1="44" x2="220" y2="44" stroke="#333" marker-end="url(#arrow)"/>
</svg>"""
_GOOD_PARALLEL = """<svg class="chart" viewBox="0 0 240 80" role="img" aria-label="x">
  <line x1="20" y1="32" x2="200" y2="32" stroke="#333" marker-end="url(#arrow)"/>
  <line x1="40" y1="48" x2="220" y2="48" stroke="#333" marker-end="url(#arrow)"/>
</svg>"""
_GOOD_ELBOW = """<svg class="chart" viewBox="0 0 240 120" role="img" aria-label="Queue feeds worker">
  <rect x="8" y="16" width="80" height="40" rx="8" fill="none" stroke="#333"/>
  <text x="48" y="40" text-anchor="middle" font-size="11">Queue</text>
  <path d="M88,36 H112 Q120,36 120,44 V76 Q120,84 128,84 H152" fill="none"
        stroke="#333" marker-end="url(#arrow)"/>
  <rect x="78" y="62" width="28" height="12" fill="#fff"/>
  <text x="104" y="70" text-anchor="end" font-size="8">retry</text>
  <rect x="152" y="64" width="80" height="40" rx="8" fill="none" stroke="#333"/>
  <text x="192" y="88" text-anchor="middle" font-size="11">Worker</text>
</svg>"""


def _self_test() -> int:
    import pathlib
    rc = 0

    # Scaffolds live in SKILL.md AND references/*.md (the chart scaffolds moved to
    # references/charts.md when SKILL.md was split). Scan both, and fail loudly if
    # no chart SVG is found at all: a vacuous pass would look identical to a clean one.
    here = pathlib.Path(__file__).parent
    sources = [here / "SKILL.md"] + sorted((here / "references").glob("*.md"))
    svgs = 0
    for src in sources:
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        svgs += len(re.findall(r"<svg\b", text))
        v = check_html(text)
        if v:
            print(_format(str(src), v))
            rc = 1
    if svgs == 0:
        print("REGRESSION: no <svg> found in SKILL.md or references/*.md; "
              "the self-test would pass vacuously. Check the scaffold locations.")
        rc = 1
    elif rc == 0:
        print(f"scaffolds ({svgs} SVGs across {len(sources)} files): "
              "all pass geometry check.")

    bad = [x for x in check_html(_BAD_PANEL) if x.kind == "panel"]
    good = [x for x in check_html(_GOOD_PANEL) if x.kind == "panel"]
    if not bad:
        print("REGRESSION: panel-straddle fixture was NOT flagged.")
        rc = 1
    elif good:
        print("REGRESSION: cleared-caption fixture was wrongly flagged.")
        rc = 1
    else:
        print("panel-straddle check: catches the straddle, passes the cleared layout.")

    conn_cases = [
        ("diagonal", _BAD_DIAGONAL, "diagonal connector"),
        ("label-on-connector", _BAD_LABEL_ON_LINE, "label sitting on a connector"),
        ("attach", _BAD_ATTACH, "shared attach point"),
        ("behind-node", _BAD_BEHIND, "connector passing behind a non-endpoint node"),
        ("corridor", _BAD_CORRIDOR, "two connectors sharing a corridor"),
    ]
    for kind, fixture, name in conn_cases:
        if not [x for x in check_html(fixture) if x.kind == kind]:
            print(f"REGRESSION: {name} fixture was NOT flagged.")
            rc = 1
    for name, fixture in (("_GOOD_ELBOW", _GOOD_ELBOW),
                          ("_GOOD_BEHIND_DASHED", _GOOD_BEHIND_DASHED),
                          ("_GOOD_ZONE", _GOOD_ZONE),
                          ("_GOOD_PARALLEL", _GOOD_PARALLEL)):
        good = check_html(fixture)
        if good:
            print(_format(f"{name} fixture", good))
            print(f"REGRESSION: the {name} fixture was wrongly flagged.")
            rc = 1
    if rc == 0:
        print("connector checks: catch diagonal / label-on-line / shared attach / "
              "behind-node / corridor, pass the elbow, dashed, zone and parallel fixtures.")
    return rc


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
