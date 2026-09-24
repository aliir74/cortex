#!/usr/bin/env python3
"""Exa AI search CLI. Invoked via the `exa` wrapper (uv run --with exa-py).

Subcommands:
  search   <query>   Find pages (neural/keyword auto). Contents nested under `contents`.
  answer   <question> Grounded answer with citations (/answer).
  contents <url...>  Extract content for URLs already in hand (/contents; params top-level).

Defaults: type=auto, contents=highlights (token-efficient).
Emits no deprecated Exa params (see exa-cli/SKILL.md for the blocklist). Reads EXA_API_KEY
from env (the wrapper self-sources ~/.exa.env). exa-py is loaded by the wrapper via uv, so
importing it here is expected.
"""
import argparse
import json
import os
import sys

SEARCH_TYPES = ["auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning"]


def get_client():
    key = os.environ.get("EXA_API_KEY")
    if not key:
        sys.stderr.write(
            "EXA_API_KEY not set. Add it to ~/.exa.env "
            "(echo 'export EXA_API_KEY=\"...\"' > ~/.exa.env && chmod 600 ~/.exa.env), "
            "then `source ~/.exa.env`.\n"
        )
        sys.exit(2)
    try:
        from exa_py import Exa
    except ImportError:
        sys.stderr.write("exa_py not importable — run via the `exa` wrapper (uv run --with exa-py).\n")
        sys.exit(2)
    return Exa(api_key=key)


def _attr(obj, name, default=None):
    """Read an attribute or dict key defensively across SDK versions."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def result_to_dict(r):
    return {
        "title": _attr(r, "title"),
        "url": _attr(r, "url"),
        "published_date": _attr(r, "published_date") or _attr(r, "publishedDate"),
        "author": _attr(r, "author"),
        "score": _attr(r, "score"),
        "highlights": _attr(r, "highlights"),
        "summary": _attr(r, "summary"),
        "text": _attr(r, "text"),
    }


def _clean(d):
    """Drop None/empty values so JSON output stays compact."""
    return {k: v for k, v in d.items() if v not in (None, [], "", {})}


def build_contents(mode, text_max, max_age_hours):
    """Contents block for /search — MUST be nested under `contents`."""
    contents = {}
    if mode == "highlights":
        contents["highlights"] = True
    elif mode == "text":
        contents["text"] = {"max_characters": text_max}
    elif mode == "summary":
        contents["summary"] = True
    if max_age_hours is not None:
        contents["max_age_hours"] = max_age_hours
    return contents


def cmd_search(args):
    exa = get_client()
    kwargs = {
        "type": "deep" if args.deep else args.type,
        "num_results": args.num,
        "contents": build_contents(args.content, args.text_max, args.max_age_hours),
    }
    if args.include_domains:
        kwargs["include_domains"] = args.include_domains
    if args.exclude_domains:
        kwargs["exclude_domains"] = args.exclude_domains
    if args.system_prompt:
        kwargs["system_prompt"] = args.system_prompt
    if args.schema:
        with open(args.schema) as fh:
            kwargs["output_schema"] = json.load(fh)

    try:
        res = exa.search(args.query, **kwargs)
    except TypeError:
        # Older SDKs put contents on a separate method; retry there.
        contents = kwargs.pop("contents", {})
        res = exa.search_and_contents(args.query, **{**kwargs, **contents})

    out = {"results": [_clean(result_to_dict(r)) for r in _attr(res, "results", [])]}
    output = _attr(res, "output")
    if output is not None:
        out["output"] = {
            "content": _attr(output, "content"),
            "grounding": _attr(output, "grounding"),
        }
    emit(out, args)


def cmd_answer(args):
    exa = get_client()
    kwargs = {"text": True}
    if args.schema:
        with open(args.schema) as fh:
            kwargs["output_schema"] = json.load(fh)
    res = exa.answer(args.question, **kwargs)
    out = {
        "answer": _attr(res, "answer"),
        "citations": [_clean(result_to_dict(c)) for c in (_attr(res, "citations", []) or [])],
    }
    emit(out, args)


def cmd_contents(args):
    exa = get_client()
    # On /contents the retrieval params are TOP-LEVEL (opposite of /search).
    kwargs = {}
    if args.content == "text":
        kwargs["text"] = {"max_characters": args.text_max}
    else:
        kwargs["highlights"] = True
    if args.max_age_hours is not None:
        kwargs["max_age_hours"] = args.max_age_hours
    res = exa.get_contents(args.urls, **kwargs)
    out = {"results": [_clean(result_to_dict(r)) for r in _attr(res, "results", [])]}
    emit(out, args)


def emit(out, args):
    if args.human:
        for r in out.get("results", []):
            print(f"{r.get('title') or '(no title)'}\n  {r.get('url')}")
            hl = r.get("highlights")
            if hl:
                print("  " + " … ".join(hl[:2])[:400])
        if out.get("answer"):
            print(out["answer"])
            for c in out.get("citations", []):
                print(f"  - {c.get('url')}")
    else:
        print(json.dumps(out, indent=2, default=str, ensure_ascii=False))


def build_parser():
    p = argparse.ArgumentParser(prog="exa", description="Exa AI search CLI")
    # Shared flags usable after the subcommand: `exa search q --json`.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--human", action="store_true", help="compact human output instead of JSON")
    common.add_argument("--json", action="store_true", help="JSON output (default; accepted for clarity)")
    p.add_argument("--human", action="store_true", help="compact human output instead of JSON")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="find pages (neural/keyword)", parents=[common])
    s.add_argument("query")
    s.add_argument("--type", default="auto", choices=SEARCH_TYPES)
    s.add_argument("--deep", action="store_true", help="shortcut for --type deep")
    s.add_argument("--num", type=int, default=10)
    s.add_argument("--content", default="highlights", choices=["highlights", "text", "summary"])
    s.add_argument("--text-max", type=int, default=8000, dest="text_max")
    s.add_argument("--include-domains", nargs="+", dest="include_domains")
    s.add_argument("--exclude-domains", nargs="+", dest="exclude_domains")
    s.add_argument("--max-age-hours", type=int, default=None, dest="max_age_hours")
    s.add_argument("--schema", help="path to a JSON file with an outputSchema")
    s.add_argument("--system-prompt", dest="system_prompt")
    s.set_defaults(func=cmd_search)

    a = sub.add_parser("answer", help="grounded answer with citations", parents=[common])
    a.add_argument("question")
    a.add_argument("--schema", help="path to a JSON file with an outputSchema")
    a.set_defaults(func=cmd_answer, content="highlights", text_max=8000, max_age_hours=None)

    c = sub.add_parser("contents", help="extract content for known URLs", parents=[common])
    c.add_argument("urls", nargs="+")
    c.add_argument("--content", default="highlights", choices=["highlights", "text"])
    c.add_argument("--text-max", type=int, default=8000, dest="text_max")
    c.add_argument("--max-age-hours", type=int, default=None, dest="max_age_hours")
    c.set_defaults(func=cmd_contents)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
