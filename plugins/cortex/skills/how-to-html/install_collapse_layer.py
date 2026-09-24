#!/usr/bin/env python3
"""Install, upgrade or remove the canonical collapse layer in an HTML artifact.

The collapse layer makes every section and card in a read-mostly artifact collapsible, and
collapsed by default, so the file opens as an index of itself rather than as a scroll. Like
the report nav it must never be hand-copied: a copy drifts from the template and quietly
loses whichever behaviour was added last (find-in-page reveal, print expansion, the docked
Expand-all control).

  python3 install_collapse_layer.py report.html \
      --collapsible "section, .card" --default collapsed \
      --alias paper=--card --alias rule=--line --alias accent=--indigo

  python3 install_collapse_layer.py report.html --check      # report version, change nothing
  python3 install_collapse_layer.py report.html --upgrade    # replace an older layer in place
  python3 install_collapse_layer.py report.html --uninstall  # take it back out
  python3 install_collapse_layer.py --self-test              # exercise install + upgrade

Aliases exist because the layer expects the scaffold
section 1 token names (--paper, --rule, --rule-2, --accent, --ink, --ink-2, --mono, --sans).
An artifact using its own names needs them mapped, or var() falls back to literals and dark
mode breaks.

--default expanded is for an artifact genuinely read top-to-bottom in one pass (a deck, a
one-screen dashboard). It still installs the affordance; it only changes the initial state.
--keep-first-open/--no-keep-first-open control whether the opening section (a report's
orientation line and answer) stays open regardless. Default: keep it open.
"""
import argparse, re, sys, pathlib, tempfile

CANON = pathlib.Path(__file__).parent / "templates/collapse-layer.html"
MARK = "collapse-layer:installed"
VERSION = 1                      # bump when the template gains behaviour worth upgrading to
VMARK = f"{MARK}:v{VERSION}"
VMARK_RE = re.compile(re.escape(MARK) + r"(?::v(\d+))?")

DEFAULT_ALIASES = {
    "mono": "ui-monospace, SFMono-Regular, Menlo, monospace",
    "sans": '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
}


def blocks():
    s = CANON.read_text()
    style = re.search(r"<style>(.*?)</style>", s[s.index("1. STYLE"):], re.S).group(1)
    script = re.search(r"<script>(.*?)</script>", s[s.index("2. SCRIPT"):], re.S).group(1)
    return style, script


def alias_css(pairs):
    if not pairs:
        return ""
    out = ["/* Collapse layer token aliases: the layer expects the scaffold section 1 names. */",
           ":root {"]
    for name, value in pairs.items():
        val = f"var({value})" if value.startswith("--") else value
        out.append(f"  --{name}: {val};")
    out.append("}")
    return "\n".join(out) + "\n"


def installed_version(src):
    """None if absent, else the installed version."""
    m = VMARK_RE.search(src)
    return (int(m.group(1)) if m.group(1) else 1) if m else None


def settings_from(src):
    """Recover the artifact's own constants so an upgrade is not a silent reconfigure."""
    out = {}
    m = re.search(r'var COLLAPSIBLE = "([^"]*)";', src)
    if m:
        out["collapsible"] = m.group(1)
    m = re.search(r'var COLLAPSE_DEFAULT = "([^"]*)";', src)
    if m:
        out["default"] = m.group(1)
    m = re.search(r"var KEEP_FIRST_OPEN = (true|false);", src)
    if m:
        out["keep_first_open"] = m.group(1) == "true"
    return out


def strip_layer(src):
    """Remove a previously installed layer. Returns new_src, or raises ValueError.

    Anchored only on the markers this installer wrote, on both sides of both regions. There
    is no structural fallback on purpose: v1 is the first release, so an unmarked file has
    no layer of ours in it and guessing could only delete the artifact's own markup.
    """
    css = re.compile(r"\n?/\* " + re.escape(MARK) + r":v\d+ \*/.*?/\* end " + re.escape(MARK) + r" \*/\n?", re.S)
    body = re.compile(r"\n?<!-- " + re.escape(MARK) + r":v\d+ -->.*?<!-- end " + re.escape(MARK) + r" -->\n?", re.S)
    if len(css.findall(src)) != 1 or len(body.findall(src)) != 1:
        raise ValueError("expected exactly one marked collapse-layer region of each kind; refusing to guess")
    return body.sub("\n", css.sub("\n", src, count=1), count=1)


def do_install(p, collapsible=None, default=None, keep_first_open=None, aliases_in=(),
               upgrade=False):
    src = p.read_text()
    have = installed_version(src)

    if have is not None and not upgrade:
        return 1, f"{p.name}: already has a collapse layer (v{have}), refusing to double-install"
    if have is None and upgrade:
        return 1, f"{p.name}: no collapse layer to upgrade"
    if "</body>" not in src:
        return 1, f"{p.name}: no </body>, cannot install"

    if upgrade:
        keep = settings_from(src)
        collapsible = collapsible or keep.get("collapsible")
        default = default or keep.get("default")
        if keep_first_open is None:
            keep_first_open = keep.get("keep_first_open")
        try:
            src = strip_layer(src)
        except ValueError as e:
            return 1, f"{p.name}: cannot upgrade safely, {e}"
        if installed_version(src) is not None:
            return 1, f"{p.name}: strip left collapse-layer traces behind, aborting without writing"

    style, script = blocks()
    if collapsible:
        script = re.sub(r'var COLLAPSIBLE = "[^"]*";',
                        'var COLLAPSIBLE = "%s";' % collapsible, script, count=1)
    if default:
        script = re.sub(r'var COLLAPSE_DEFAULT = "[^"]*";',
                        'var COLLAPSE_DEFAULT = "%s";' % default, script, count=1)
    if keep_first_open is not None:
        script = re.sub(r"var KEEP_FIRST_OPEN = (?:true|false);",
                        "var KEEP_FIRST_OPEN = %s;" % ("true" if keep_first_open else "false"),
                        script, count=1)

    aliases = dict(DEFAULT_ALIASES)
    for item in aliases_in:
        if "=" not in item:
            return 1, f"bad --alias {item!r}, expected token=value"
        k, v = item.split("=", 1)
        aliases[k.lstrip("-")] = v

    css = f"\n/* {VMARK} */\n" + alias_css(aliases) + style + f"\n/* end {MARK} */\n"
    if "</style>" in src:
        i = src.rindex("</style>")
        src = src[:i] + css + src[i:]
    else:
        i = src.index("</head>") if "</head>" in src else src.index("<body>")
        src = src[:i] + f"<style>{css}</style>\n" + src[i:]

    # The collapse layer moves content into .cx-body wrappers, so the report nav must run
    # after it and see the final structure. The nav skips .cx-chevron / .cx-hint when
    # it builds a key, which is what keeps "§ Findings" from becoming "§ Findings 4 items".
    i = src.rindex("</body>")
    src = (src[:i] + f"\n<!-- {VMARK} -->\n<script>\n" + script
           + f"</script>\n<!-- end {MARK} -->\n" + src[i:])
    p.write_text(src)
    verb = f"upgraded to v{VERSION}" if upgrade else "installed"
    return 0, (f"{p.name}: collapse layer {verb} "
               f"(collapsible={collapsible or 'default'}, default={default or 'collapsed'})")


def do_uninstall(p):
    src = p.read_text()
    if installed_version(src) is None:
        return 1, f"{p.name}: no collapse layer to remove"
    try:
        src = strip_layer(src)
    except ValueError as e:
        return 1, f"{p.name}: cannot remove safely, {e}"
    p.write_text(src)
    return 0, f"{p.name}: collapse layer removed"


FIXTURE = """<!doctype html><html><head><style>body{color:#111}</style></head><body>
<div class="container">
<section><h2>Answer</h2><p>The short version.</p></section>
<section><h2>Detail</h2><p>Long tail.</p><div class="card"><h3>A card</h3><p>Inside.</p></div></section>
</div>
<style>.after-layer{color:red}</style>
</body></html>"""


def self_test():
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + name)
        ok = ok and bool(cond)

    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        f = d / "report.html"
        f.write_text(FIXTURE)

        code, msg = do_install(f, collapsible="section, .card", default="collapsed")
        s = f.read_text()
        check("install exits 0", code == 0)
        check("version marker present", VMARK in s)
        # rindex: the layer's CSS goes into the LAST style block so
        # it wins the cascade against the artifact's own rules.
        check("style spliced into the last style block", s.index(VMARK) < s.rindex("</style>"))
        check("script spliced before </body>", "<!-- end %s -->" % MARK in s)
        check("COLLAPSIBLE written", 'var COLLAPSIBLE = "section, .card";' in s)
        check("COLLAPSE_DEFAULT written", 'var COLLAPSE_DEFAULT = "collapsed";' in s)
        check("detected as current version", installed_version(s) == VERSION)
        check("host content preserved", "The short version." in s and "Long tail." in s)
        check("CSS after the layer preserved", ".after-layer" in s)

        code2, _ = do_install(f, collapsible="section")
        check("double install refuses", code2 == 1)

        code3, _ = do_install(f, upgrade=True)
        s3 = f.read_text()
        check("upgrade exits 0", code3 == 0)
        check("upgrade leaves one marked region", s3.count("/* %s */" % VMARK) == 1)
        check("upgrade preserved COLLAPSIBLE", 'var COLLAPSIBLE = "section, .card";' in s3)
        check("upgrade preserved content", "Long tail." in s3 and ".after-layer" in s3)
        check("upgrade did not duplicate script", s3.count("cx-chevron") == s.count("cx-chevron"))

        code4, _ = do_uninstall(f)
        s4 = f.read_text()
        check("uninstall exits 0", code4 == 0)
        check("uninstall removes every marker", installed_version(s4) is None)
        check("uninstall leaves no cx- trace", "cx-chevron" not in s4)
        # Whitespace-insensitive: the strip leaves the newline that separated the spliced
        # region from its neighbour, which changes no byte of the artifact's own content.
        norm = lambda t: re.sub(r"\s+", "", t)
        check("uninstall restores the original", norm(s4) == norm(FIXTURE))

        code5, _ = do_uninstall(f)
        check("uninstall on a bare file refuses", code5 == 1)

        code6, _ = do_install(f, default="expanded", keep_first_open=False)
        s6 = f.read_text()
        check("--default expanded written", 'var COLLAPSE_DEFAULT = "expanded";' in s6)
        check("--no-keep-first-open written", "var KEEP_FIRST_OPEN = false;" in s6)

        # Namespace guard: a bare class here would
        # collide with whatever the host artifact happens to define, silently.
        style, script = blocks()
        created = set(re.findall(r'className = "([a-z0-9 \-]+)"', script))
        created |= set(re.findall(r'classList\.add\("([a-z0-9\-]+)"\)', script))
        created |= set(re.findall(r'class="([a-z0-9 \-]+)"', style))
        bad = sorted(c for blob in created for c in blob.split()
                     if not c.startswith("cx-"))
        check("layer creates no unprefixed class (%s)" % (", ".join(bad) or "none"), not bad)
        check("collision guard present", ".cx-head > span" in style)
        # The guard must not reach the layer's own spans: it out-specifies a bare .cx-*
        # rule and silently zeroed the chevron border and the count chip's auto margin.
        check("collision guard excludes cx- classes",
              '.cx-head > span:not([class*="cx-"])' in style)
        check("print rule forces open", "@media print" in style and "display: block !important" in style)
        check("uses hidden=until-found", 'hidden = "until-found"' in script)

    print("self-test: " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Install the canonical collapse layer.")
    ap.add_argument("file", nargs="?", type=pathlib.Path)
    ap.add_argument("--collapsible", help='selector list, e.g. "section, .card"')
    ap.add_argument("--default", choices=("collapsed", "expanded"),
                    help="initial state (default: collapsed)")
    ap.add_argument("--keep-first-open", dest="keep_first_open", action="store_true", default=None)
    ap.add_argument("--no-keep-first-open", dest="keep_first_open", action="store_false")
    ap.add_argument("--alias", action="append", default=[], metavar="token=value")
    ap.add_argument("--check", action="store_true", help="report status, change nothing")
    ap.add_argument("--upgrade", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.file:
        ap.error("a file is required unless --self-test")
    if not a.file.exists():
        print(f"{a.file}: no such file", file=sys.stderr)
        return 1
    if a.check:
        have = installed_version(a.file.read_text())
        print(f"{a.file.name}: " + (f"collapse layer v{have}" if have else "no collapse layer"))
        return 0
    if a.uninstall:
        code, msg = do_uninstall(a.file)
    else:
        code, msg = do_install(a.file, a.collapsible, a.default, a.keep_first_open,
                               a.alias, upgrade=a.upgrade)
    print(msg, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == "__main__":
    sys.exit(main())
