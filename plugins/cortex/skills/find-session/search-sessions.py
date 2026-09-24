#!/usr/bin/env python3
"""Search Claude Code session JSONL files for conversations matching keywords."""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


CLAUDE_DIR = Path.home() / ".claude" / "projects"


def get_project_dirs():
    """Return all project directories under ~/.claude/projects."""
    if not CLAUDE_DIR.exists():
        return []
    return sorted(p for p in CLAUDE_DIR.iterdir() if p.is_dir())


def decode_project_name(dirname: str) -> str:
    """Convert an encoded project directory name to a readable path (approximate)."""
    return dirname.replace("-", "/")


def extract_messages(filepath: Path, role_filter=None):
    """Extract user/assistant text messages from a JSONL session file."""
    messages = []
    try:
        with open(filepath) as f:
            for line in f:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type", "")
                if msg_type not in ("user", "assistant"):
                    continue
                if role_filter and msg_type != role_filter:
                    continue

                inner = msg.get("message", {})
                content = inner.get("content", "") if isinstance(inner, dict) else ""
                texts = []

                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            t = c.get("text", "")
                            if "<system-reminder>" not in t and "<system>" not in t[:50]:
                                texts.append(t)
                elif isinstance(content, str):
                    if "<system-reminder>" not in content:
                        texts.append(content)

                if texts:
                    messages.append({"role": msg_type, "text": " ".join(texts)})
    except (OSError, PermissionError):
        pass
    return messages


def get_session_timestamp(filepath: Path) -> str:
    """Get session start timestamp from the first timestamped entry, else file mtime."""
    try:
        with open(filepath) as f:
            for line in f:
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = msg.get("timestamp") or msg.get("snapshot", {}).get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
                    except ValueError:
                        continue
    except (OSError, PermissionError):
        pass
    mtime = filepath.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")


def get_session_cwd(filepath: Path) -> str:
    """Get the working directory from session metadata."""
    try:
        with open(filepath) as f:
            for line in f:
                try:
                    cwd = json.loads(line).get("cwd", "")
                except json.JSONDecodeError:
                    continue
                if cwd:
                    return cwd
    except (OSError, PermissionError):
        pass
    return ""


def search_session(filepath: Path, patterns: list, role_filter=None, match_all=False):
    """Return the messages in a session that match the keyword patterns."""
    messages = extract_messages(filepath, role_filter)
    if not messages:
        return []

    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    check = all if match_all else any
    return [m for m in messages if check(p.search(m["text"]) for p in compiled)]


def first_user_message(filepath: Path) -> str:
    """Get the first user message as a session summary."""
    messages = extract_messages(filepath, role_filter="user")
    if messages:
        return messages[0]["text"][:200].replace("\n", " ").strip()
    return "(no user messages)"


def worktree_info(proj_dir: Path, cwd: str):
    """Return (is_worktree, worktree_name) for a session."""
    is_worktree = "worktree" in proj_dir.name.lower() or (cwd and ".claude/worktrees/" in cwd)
    name = ""
    if cwd and ".claude/worktrees/" in cwd:
        name = cwd.split(".claude/worktrees/", 1)[1].rstrip("/").split("/")[0]
    elif "worktrees-" in proj_dir.name:
        name = proj_dir.name.rsplit("worktrees-", 1)[-1]
    return bool(is_worktree), name


def main():
    parser = argparse.ArgumentParser(
        description="Search Claude Code sessions for conversations matching keywords.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s docker compose                # Sessions mentioning docker OR compose
  %(prog)s --all docker compose          # Sessions mentioning docker AND compose
  %(prog)s --project backend migration   # Only search sessions from matching projects
  %(prog)s --after YYYY-MM-DD deploy     # Sessions modified after a date
  %(prog)s --user-only deploy            # Only search user messages
  %(prog)s --context 3 terraform         # Show 3 surrounding messages for context
  %(prog)s --list-projects               # List all projects with session counts
        """,
    )
    parser.add_argument("keywords", nargs="*", help="Keywords to search for (regex supported)")
    parser.add_argument("--all", action="store_true", help="Require ALL keywords to match (default: any)")
    parser.add_argument("--project", "-p", help="Filter by project name (substring match)")
    parser.add_argument("--after", help="Only sessions modified after this date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only sessions modified before this date (YYYY-MM-DD)")
    parser.add_argument("--user-only", "-u", action="store_true", help="Only search user messages")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--context", "-c", type=int, default=0, help="Show N surrounding messages for context")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show matching message snippets")
    parser.add_argument("--list-projects", action="store_true", help="List all projects and session counts")

    args = parser.parse_args()

    if args.list_projects:
        for proj_dir in get_project_dirs():
            sessions = list(proj_dir.glob("*.jsonl"))
            if sessions:
                print(f"  {len(sessions):3d} sessions  {decode_project_name(proj_dir.name)}")
        return

    if not args.keywords:
        parser.print_help()
        return

    role_filter = "user" if args.user_only else None
    after_ts = datetime.strptime(args.after, "%Y-%m-%d").timestamp() if args.after else None
    before_ts = datetime.strptime(args.before, "%Y-%m-%d").timestamp() if args.before else None

    results = []
    for proj_dir in get_project_dirs():
        if args.project and args.project.lower() not in proj_dir.name.lower():
            continue

        # Top-level *.jsonl only; subagent transcripts live in nested folders.
        for session_file in proj_dir.glob("*.jsonl"):
            mtime = session_file.stat().st_mtime
            if after_ts and mtime < after_ts:
                continue
            if before_ts and mtime > before_ts:
                continue

            matches = search_session(session_file, args.keywords, role_filter, args.all)
            if not matches:
                continue

            cwd = get_session_cwd(session_file)
            is_worktree, worktree_name = worktree_info(proj_dir, cwd)
            results.append({
                "session_id": session_file.stem,
                "timestamp": get_session_timestamp(session_file),
                "project": decode_project_name(proj_dir.name),
                "cwd": cwd,
                "match_count": len(matches),
                "first_message": first_user_message(session_file),
                "matches": matches,
                "mtime": mtime,
                "file": str(session_file),
                "is_worktree": is_worktree,
                "worktree_name": worktree_name,
            })

    results.sort(key=lambda r: r["mtime"], reverse=True)

    if not results:
        print(f"No sessions found matching: {' '.join(args.keywords)}")
        return

    shown = results[: args.limit]
    print(f"Found {len(results)} sessions (showing {len(shown)}):\n")

    for i, r in enumerate(shown, 1):
        worktree_tag = " [worktree]" if r["is_worktree"] else ""
        print(f"{i}. [{r['timestamp']}] {r['match_count']} matches{worktree_tag}")
        print(f"   Session: {r['session_id']}")
        print(f"   Folder: {r['cwd'] or r['project']}")
        if r["is_worktree"] and r["worktree_name"]:
            print(f"   Worktree: {r['worktree_name']}")
        print(f"   First message: {r['first_message'][:120]}")

        if args.verbose:
            print("   Matching snippets:")
            for m in r["matches"][:3]:
                snippet = m["text"][:200].replace("\n", " ").strip()
                print(f"     [{m['role']}] {snippet}")

        if args.context > 0:
            all_msgs = extract_messages(Path(r["file"]))
            for idx, msg in enumerate(all_msgs):
                if any(re.search(k, msg["text"], re.IGNORECASE) for k in args.keywords):
                    start = max(0, idx - args.context)
                    end = min(len(all_msgs), idx + args.context + 1)
                    print("   Context around first match:")
                    for ci in range(start, end):
                        marker = ">>>" if ci == idx else "   "
                        snippet = all_msgs[ci]["text"][:150].replace("\n", " ")
                        print(f"   {marker} [{all_msgs[ci]['role']}] {snippet}")
                    break

        if r["cwd"]:
            print(f"   Resume: cd {r['cwd']} && claude --resume {r['session_id']}")
        else:
            print(f"   Resume: claude --resume {r['session_id']}")
        if r["is_worktree"]:
            print("   WARNING: worktree session, resume may fail if the worktree was cleaned up")
        print()


if __name__ == "__main__":
    main()
