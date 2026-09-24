#!/usr/bin/env python3
"""Convert a markdown file (Obsidian-flavoured supported) to PDF via pandoc + Chrome headless.

Strips YAML frontmatter, resolves Obsidian wikilinks, and adds hard breaks
to top-block metadata lines so the output renders cleanly without a
duplicate title block or smushed header.

Usage:
    md-to-pdf.py INPUT.md [OUTPUT.pdf]
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SKILL_DIR = Path(__file__).resolve().parent
CSS_PATH = SKILL_DIR / "style.css"


def find_chrome() -> str | None:
    """Resolve a Chrome/Chromium binary: $CHROME_PATH, then PATH, then the macOS app."""
    env = os.environ.get("CHROME_PATH")
    if env:
        return env if Path(env).exists() else None
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return MAC_CHROME if Path(MAC_CHROME).exists() else None


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :].lstrip()


def clean_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", lambda m: m.group(1).split("/")[-1], text)
    return text


def add_metadata_breaks(text: str) -> str:
    # Lines like `**Label:** value` at the top of the body (before the first H2)
    # become single-line paragraphs — append two trailing spaces so pandoc
    # renders them with hard breaks.
    lines = text.split("\n")
    out = []
    seen_h2 = False
    for line in lines:
        if line.startswith("## "):
            seen_h2 = True
        if not seen_h2 and re.match(r"^\*\*[^*]+:\*\*\s.+\S$", line):
            out.append(line + "  ")
        else:
            out.append(line)
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1]).expanduser().resolve()
    if not input_path.exists():
        print(f"Not found: {input_path}", file=sys.stderr)
        return 1
    output_path = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) > 2
        else input_path.with_suffix(".pdf")
    )

    if not shutil.which("pandoc"):
        print("pandoc not found on PATH", file=sys.stderr)
        return 1
    chrome = find_chrome()
    if not chrome:
        print("Chrome/Chromium not found. Set CHROME_PATH to the browser binary.", file=sys.stderr)
        return 1

    text = input_path.read_text()
    text = strip_frontmatter(text)
    text = clean_wikilinks(text)
    text = add_metadata_breaks(text)

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        md_tmp = tmp / "input.md"
        html_tmp = tmp / "output.html"
        md_tmp.write_text(text)
        subprocess.run(
            [
                "pandoc",
                str(md_tmp),
                "-s",
                "-o",
                str(html_tmp),
                "-c",
                str(CSS_PATH),
                # The markdown is copied to a temp dir, so image paths written
                # relative to the SOURCE file cannot be resolved from there.
                # Resolve them against the source directory, then base64-inline
                # them so the Chrome step is path-independent too.
                f"--resource-path={input_path.parent}",
                "--embed-resources",
            ],
            check=True,
        )
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={output_path}",
                f"file://{html_tmp}",
            ],
            check=True,
            capture_output=True,
        )
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
