#!/usr/bin/env python3
"""adherence-probe.py: deterministic adherence probes for the instruction corpus.

Token counts prove cost, not adherence. This asks a fresh headless Claude Code
session (`claude -p`) a question whose correct answer is fixed by a rule in your
corpus, then asserts over the answer with a regex. No model judges another model:
every check is a grep.

Usage:
    adherence-probe.py                          # run all probes, print a table
    adherence-probe.py --probes my-probes.json  # use a specific probes file
    adherence-probe.py --json out.json          # also write machine-readable results
    adherence-probe.py --only id_a,id_b         # run a subset
    adherence-probe.py --repeat 3               # N runs per probe, report a pass rate
    adherence-probe.py --cwd path/to/repo       # run from a project directory
    adherence-probe.py --model sonnet           # default is haiku (cost)
    adherence-probe.py --list                   # print probe ids and rules

Default probes file: $CLAUDE_PLUGIN_DATA/adherence-probes.json (falling back to
the Cortex dir under ~/.claude/plugins/data/, e.g. cortex-cortex/adherence-probes.json). Start from
probes.example.json next to this script. Each probe:

    {"id": "short_id",
     "rule": "where the rule lives and what it says",
     "scope": "user",                  # optional label, e.g. user / project
     "prompt": "question whose correct answer the rule fixes",
     "want":  "regex that MUST appear in the answer",
     "avoid": "regex that must NOT appear"}   # at least one of want/avoid

The rule for a good probe: THE INTUITIVE ANSWER MUST BE WRONG. If a model with no
access to your corpus would land on the right answer by default, the probe proves
nothing about adherence. If you cannot write a regex that separates right from
wrong, the probe does not belong here.

Exit 0 if every probe passes, 1 otherwise, 2 on bad input. Requires the `claude`
CLI on PATH. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
def _data_dir() -> str:
    """$CLAUDE_PLUGIN_DATA when set (it is, inside a Cortex skill run); otherwise the
    first existing Cortex plugin data dir, defaulting to the marketplace-qualified name."""
    env = os.environ.get("CLAUDE_PLUGIN_DATA")
    if env:
        return env
    base = os.path.expanduser("~/.claude/plugins/data")
    for name in ("cortex-cortex", "cortex"):
        if os.path.isdir(os.path.join(base, name)):
            return os.path.join(base, name)
    return os.path.join(base, "cortex-cortex")


DATA_DIR = _data_dir()
DEFAULT_PROBES = os.path.join(DATA_DIR, "adherence-probes.json")
EXAMPLE_PROBES = os.path.join(HERE, "probes.example.json")

# An unauthenticated child answers nothing useful and would score FAIL on every
# `want` regex. That silently inverts a control run: a broken control always
# "fails", and a failing control reads as "the rule is needed". Score it ERROR.
AUTH_FAILURE_RE = re.compile(
    r"(not logged in|please run /login|invalid api key|no credentials found|"
    r"authentication (failed|required)|oauth token (has been )?revoked)",
    re.IGNORECASE,
)


def load_probes(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("probes file must hold a JSON list")
    seen = set()
    for i, p in enumerate(data):
        for key in ("id", "rule", "prompt"):
            if key not in p:
                raise ValueError(f"probe {i} lacks '{key}'")
        if not (p.get("want") or p.get("avoid")):
            raise ValueError(f"probe {p['id']} needs at least one of want/avoid")
        if p["id"] in seen:
            raise ValueError(f"duplicate probe id {p['id']}")
        seen.add(p["id"])
        for key in ("want", "avoid"):
            if p.get(key):
                re.compile(p[key])
    return data


def _result(probe: dict, status: str, detail: str, answer: str) -> dict:
    return {"id": probe["id"], "scope": probe.get("scope", "user"), "rule": probe["rule"],
            "status": status, "detail": detail, "answer": answer}


def run_probe(probe: dict, model: str, cwd: str | None, config_dir: str | None,
              timeout: int) -> dict:
    env = dict(os.environ)
    if config_dir:
        env["CLAUDE_CONFIG_DIR"] = os.path.expanduser(config_dir)
    cmd = ["claude", "-p", probe["prompt"], "--model", model]
    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser(cwd) if cwd else None,
            env=env,
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return _result(probe, "ERROR", f"timeout after {timeout}s", "")
    except FileNotFoundError:
        return _result(probe, "ERROR", "`claude` CLI not found on PATH", "")

    if not out:
        return _result(probe, "ERROR", f"empty answer (stderr: {err[:120]})", "")

    if AUTH_FAILURE_RE.search(out):
        return _result(
            probe, "ERROR",
            "child could not authenticate, so this result is not a behavioural signal. "
            "If you passed --config-dir, that directory has no usable credentials: control "
            "by temporarily reverting the rule in the live corpus instead.",
            out[:200])

    problems = []
    want = probe.get("want")
    if want and not re.search(want, out, re.IGNORECASE):
        problems.append(f"missing /{want}/")
    avoid = probe.get("avoid")
    if avoid:
        m = re.search(avoid, out, re.IGNORECASE)
        if m:
            problems.append(f"found forbidden /{avoid}/ at {m.start()}")

    return _result(probe, "PASS" if not problems else "FAIL", "; ".join(problems), out[:400])


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic adherence probes for Claude Code instructions.")
    ap.add_argument("--probes", default=DEFAULT_PROBES, help=f"probes JSON file (default {DEFAULT_PROBES})")
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--cwd", default=None, help="run probes from this directory")
    ap.add_argument("--config-dir", default=None,
                    help="CLAUDE_CONFIG_DIR override. Only valid if that dir can authenticate; "
                         "see the warning printed when it cannot")
    ap.add_argument("--only", default=None, help="comma-separated probe ids")
    ap.add_argument("--list", action="store_true", help="print probe ids and rules, then exit")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--repeat", type=int, default=1,
                    help="run each probe N times and report a pass RATE. Model answers "
                         "are not deterministic even though the assertions are, so a "
                         "single run cannot separate 'rule missing' from 'lucky guess'. "
                         "Use 3+ when treating this as a regression gate.")
    ap.add_argument("--label", default="current", help="label recorded in the JSON")
    args = ap.parse_args()

    path = os.path.expanduser(args.probes)
    if not os.path.isfile(path):
        print(f"no probes file at {path}. Copy {EXAMPLE_PROBES} there (or pass --probes) "
              f"and write probes for your own rules.", file=sys.stderr)
        return 2
    try:
        all_probes = load_probes(path)
    except (OSError, ValueError, re.error) as e:
        print(f"cannot load probes: {e}", file=sys.stderr)
        return 2

    if args.list:
        for p in all_probes:
            print(f"{p['id']:28} {p.get('scope', 'user'):8} {p['rule']}")
        return 0

    probes = all_probes
    if args.only:
        keep = {x.strip() for x in args.only.split(",")}
        probes = [p for p in all_probes if p["id"] in keep]
        missing = keep - {p["id"] for p in probes}
        if missing:
            print(f"unknown probe id(s): {', '.join(sorted(missing))}", file=sys.stderr)
            return 2

    if args.config_dir:
        cd = os.path.expanduser(args.config_dir)
        if not any(os.path.exists(os.path.join(cd, f))
                   for f in (".credentials.json", "credentials.json")):
            print(f"WARNING: {cd} has no credentials file. Where the login credential lives "
                  f"in the OS keychain (e.g. macOS), a copied config dir cannot authenticate "
                  f"and every probe will score ERROR, so it is not a valid control.\n"
                  f"         Control by temporarily reverting the rule in the LIVE corpus "
                  f"instead, then restore it.", file=sys.stderr)

    results = []
    for p in probes:
        runs = [run_probe(p, args.model, args.cwd, args.config_dir, args.timeout)
                for _ in range(max(1, args.repeat))]
        n = len(runs)
        npass_runs = sum(1 for r in runs if r["status"] == "PASS")
        nerr_runs = sum(1 for r in runs if r["status"] == "ERROR")
        # PASS only if every run passed. Anything in between is FLAKY: the rule is
        # present but not reliably followed. An ERROR run is not evidence about the
        # rule, so it is surfaced as itself rather than folded into FAIL.
        if nerr_runs == n:
            status = "ERROR"
        elif npass_runs == n:
            status = "PASS"
        elif npass_runs == 0:
            status = "FAIL"
        else:
            status = "FLAKY"
        r0 = dict(runs[0])
        r0.update({"status": status, "pass_rate": f"{npass_runs}/{n}",
                   "runs": [{"status": x["status"], "detail": x["detail"],
                             "answer": x["answer"][:200]} for x in runs]})
        results.append(r0)
        mark = {"PASS": "PASS", "FAIL": "FAIL", "FLAKY": "FLAK", "ERROR": "ERR "}[status]
        rate = f"{npass_runs}/{n}" if n > 1 else ""
        print(f"  [{mark}] {r0['scope']:7} {r0['id']:24} {rate:6} {r0['detail']}")

    npass = sum(1 for r in results if r["status"] == "PASS")
    nfail = sum(1 for r in results if r["status"] == "FAIL")
    nflaky = sum(1 for r in results if r["status"] == "FLAKY")
    nerr = sum(1 for r in results if r["status"] == "ERROR")
    print(f"\n{npass}/{len(results)} passed"
          + (f", {nflaky} flaky" if nflaky else "")
          + (f", {nfail} failed" if nfail else "")
          + (f", {nerr} errored" if nerr else ""))
    print("Hand-read the answers of anything flagged; template echoes and quoted "
          "counter-examples can masquerade as hits in both directions.")

    if args.json_out:
        payload = {
            "label": args.label,
            "model": args.model,
            "cwd": args.cwd or os.getcwd(),
            "config_dir": args.config_dir,
            "repeat": args.repeat,
            "passed": npass, "flaky": nflaky, "failed": nfail, "errored": nerr,
            "results": results,
        }
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"wrote {args.json_out}")

    return 0 if (nfail == 0 and nerr == 0 and nflaky == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
