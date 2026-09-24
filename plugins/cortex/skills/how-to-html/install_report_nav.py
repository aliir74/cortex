#!/usr/bin/env python3
"""Install the canonical report navigation into an existing HTML artifact.

Mirrors install_collapse_layer.py deliberately: same three-block splice, same alias
mechanism, same idempotency marker, same refusal to double-install. The two installers
are meant to be learnable as one pattern.

  python3 install_report_nav.py report.html \
      --section-root ".container" \
      --heading "h2" \
      --alias paper=--card --alias rule=--line --alias accent=--indigo

  python3 install_report_nav.py report.html --check   # status + spine audit, changes nothing
  python3 install_report_nav.py --self-test           # exercise the installer end to end

Aliases exist because the layer expects the scaffold section 1 token names (--paper,
--rule, --rule-2, --accent, --mono, --sans). An artifact using its own names needs them
mapped, or var() falls back to literals and dark mode breaks.

--check also audits the narrative spine (references/narrative.md). That audit is a
heuristic and reports only: it never edits, never blocks, and a false negative on an
unusual but valid report is expected. It exists so a structural rule has a cheap check
rather than relying on memory.
"""
import argparse, re, sys, pathlib, tempfile

CANON = pathlib.Path(__file__).parent / "templates/report-nav.html"
MARK = "report-nav:installed"

DEFAULT_ALIASES = {
    "mono": "ui-monospace, SFMono-Regular, Menlo, monospace",
    "sans": '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
}

# Spine parts the --check audit looks for, and the signals that count as present.
SPINE_SIGNALS = {
    "middle marker": [r"<!--\s*report-middle:\s*\w+"],
    "orientation": [r'class="[^"]*\borient\b', r'class="[^"]*\bkicker\b'],
    "two-minute": [r'class="[^"]*\btwo-minute\b', r'class="[^"]*\btldr\b',
                   r">\s*(Two-minute|In two minutes|The short version)"],
    "actions": [r'class="[^"]*\bactions\b', r">\s*(What you need to do|Actions|What's left for you)"],
}


def blocks():
    s = CANON.read_text()
    style = re.search(r"<style>(.*?)</style>", s[s.index("1. STYLE"):], re.S).group(1)
    j, k = s.index("2. MARKUP"), s.index("3. SCRIPT")
    markup = s[j:k]
    markup = markup[markup.index("-->") + 3:]
    markup = markup[:markup.rindex("<!--")].strip()
    script = re.search(r"<script>(.*?)</script>", s[k:], re.S).group(1)
    return style, markup, script


def alias_css(pairs):
    if not pairs:
        return ""
    light, dark = [], []
    for name, value in pairs.items():
        val = f"var({value})" if value.startswith("--") else value
        light.append(f"  --{name}: {val};")
        if name == "rule-2":
            dark.append(f"  --{name}: rgba(255,255,255,0.20);")
    out = ["/* Report nav token aliases: the layer expects the scaffold section 1 names. */",
           ":root {", *light, "}"]
    if dark:
        out += ["@media (prefers-color-scheme: dark) {", "  :root {",
                *["  " + d for d in dark], "  }", "}"]
    return "\n".join(out) + "\n"


def audit_spine(src):
    """Report which spine parts look absent. Heuristic, report-only."""
    missing = [name for name, pats in SPINE_SIGNALS.items()
               if not any(re.search(p, src, re.I) for p in pats)]
    return missing


def install(target, section_root=None, heading=None, aliases_in=()):
    p = pathlib.Path(target)
    src = p.read_text()
    if MARK in src or 'id="rnav"' in src:
        return 1, f"{p.name}: already has report nav, refusing to double-install"
    if "</body>" not in src:
        return 1, f"{p.name}: no </body>, cannot install"

    style, markup, script = blocks()
    if section_root:
        script = re.sub(r'const SECTION_ROOT = "[^"]*";',
                        'const SECTION_ROOT = "%s";' % section_root, script, count=1)
    if heading:
        script = re.sub(r'const HEADING = "[^"]*";',
                        'const HEADING = "%s";' % heading, script, count=1)

    aliases = dict(DEFAULT_ALIASES)
    for item in aliases_in:
        if "=" not in item:
            return 1, f"bad --alias {item!r}, expected token=value"
        k, v = item.split("=", 1)
        aliases[k.lstrip("-")] = v

    css = f"\n/* {MARK} */\n" + alias_css(aliases) + style
    if "</style>" in src:
        i = src.rindex("</style>")
        src = src[:i] + css + src[i:]
    else:
        i = src.index("</head>") if "</head>" in src else src.index("<body>")
        src = src[:i] + f"<style>{css}</style>\n" + src[i:]

    i = src.rindex("</body>")
    src = src[:i] + "\n" + markup + "\n\n<script>\n" + script + "</script>\n" + src[i:]
    p.write_text(src)
    return 0, (f"{p.name}: report nav installed "
               f"(section-root={section_root or '.container'}, heading={heading or 'h2'})")


SELF_TEST_PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8"><title>t</title>
<style>:root{--ink:#000}</style></head><body><div class="container">
<h2>One</h2><h2>Two</h2><h2>Three</h2></div></body></html>"""


def self_test():
    ok = True

    def check(label, cond):
        nonlocal ok
        print(f"  {'PASS' if cond else 'FAIL'}  {label}")
        ok = ok and cond

    print("install_report_nav --self-test")
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "t.html"
        f.write_text(SELF_TEST_PAGE)

        code, msg = install(f, section_root=".container", heading="h2")
        check("first install exits 0", code == 0)
        s = f.read_text()
        check("style block spliced", MARK in s and ".rnav {" in s)
        check("markup block spliced", 'id="rnav"' in s and 'id="rnav-toggle"' in s)
        check("script block spliced", "IntersectionObserver" in s)
        check("marker appears exactly once", s.count(MARK) == 1)
        check("SECTION_ROOT rewritten", 'const SECTION_ROOT = ".container";' in s)
        check("HEADING rewritten", 'const HEADING = "h2";' in s)
        check("markup sits before </body>", s.rindex('id="rnav"') < s.rindex("</body>"))

        code2, _ = install(f, section_root=".container", heading="h2")
        check("second install refused", code2 == 1)
        check("file unchanged after refusal", f.read_text() == s)

        code3, _ = install(f, section_root=".main", heading="h3")
        check("refusal is not partial (no second marker)", f.read_text().count(MARK) == 1)

        g = pathlib.Path(d) / "custom.html"
        g.write_text(SELF_TEST_PAGE)
        install(g, section_root="#report", heading="h3", aliases_in=["paper=--card"])
        gs = g.read_text()
        check("custom section root honoured", 'const SECTION_ROOT = "#report";' in gs)
        check("custom heading honoured", 'const HEADING = "h3";' in gs)
        check("alias emitted", "--paper: var(--card);" in gs)

        check("spine audit flags a bare page", len(audit_spine(SELF_TEST_PAGE)) == 4)
        full = ('<!-- report-middle: verdict --><p class="orient">x</p>'
                '<div class="two-minute">y</div><div class="actions">z</div>')
        check("spine audit passes a conforming page", audit_spine(full) == [])

    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?")
    ap.add_argument("--section-root", help="CSS selector holding the sections (default .container)")
    ap.add_argument("--heading", help="heading selector counted as a section (default h2)")
    ap.add_argument("--alias", action="append", default=[],
                    help="token=value, e.g. paper=--card or accent=#5e5ce6")
    ap.add_argument("--check", action="store_true",
                    help="report install status and audit the narrative spine; changes nothing")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.target:
        ap.error("target is required unless --self-test is given")

    p = pathlib.Path(a.target)
    src = p.read_text()

    if a.check:
        installed = MARK in src or 'id="rnav"' in src
        print(f"{p.name}: report nav {'PRESENT' if installed else 'ABSENT'}")
        missing = audit_spine(src)
        if missing:
            print(f"{p.name}: spine audit, no signal found for: {', '.join(missing)}")
            print("  (heuristic and report-only; an unusual but valid report can trip it)")
        else:
            print(f"{p.name}: spine audit, all parts present")
        return 0

    code, msg = install(p, a.section_root, a.heading, a.alias)
    print(msg, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
