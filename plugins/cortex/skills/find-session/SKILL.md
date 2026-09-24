---
name: find-session
description: Use when user wants to find, search, or locate a previous Claude Code conversation or session by topic, keyword, or content - triggers on "find session", "find chat", "search sessions", "which session", "previous conversation about", or explicit /find-session command
---

# Find Session

Search Claude Code session history (JSONL files in `~/.claude/projects/`) for past conversations by keyword.

## Prerequisites

Requires `python3` (stdlib only, no packages). If it's not installed, point the user to `SETUP.md` at the plugin root (section: **find-session**) and stop until it's available.

## Usage

Run the bundled search script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/find-session/search-sessions.py" [OPTIONS] KEYWORD [KEYWORD...]
```

Key flags (run with `--help` for all):
- `--all`: require ALL keywords (default: any match)
- `-p PROJECT`: filter by project name substring
- `--after YYYY-MM-DD` / `--before YYYY-MM-DD`: date range (by file modification time)
- `-u`: search only user messages (skip assistant)
- `-v`: show matching message snippets
- `-c N`: show N surrounding messages for context
- `-n N`: limit results (default: 10)
- `--list-projects`: list all projects with session counts

Keywords are case-insensitive regexes.

## Examples

```bash
# Find sessions about a topic
python3 "${CLAUDE_PLUGIN_ROOT}/skills/find-session/search-sessions.py" docker compose

# Require both keywords
python3 "${CLAUDE_PLUGIN_ROOT}/skills/find-session/search-sessions.py" --all oauth refresh

# Search only one project, with snippets
python3 "${CLAUDE_PLUGIN_ROOT}/skills/find-session/search-sessions.py" -p backend -v deploy

# Recent sessions only
python3 "${CLAUDE_PLUGIN_ROOT}/skills/find-session/search-sessions.py" --after YYYY-MM-DD migration
```

## Output Fields

Each result includes:
- **Folder**: the working directory where the session ran
- **Worktree**: if the session ran inside a `.claude/worktrees/` directory, the worktree name is shown and the header is tagged `[worktree]`
- **Resume command**: `cd <folder> && claude --resume <session-id>` (sessions are scoped to the directory they ran in)

## Worktree Session Limitations

Worktree sessions are stored under a separate project path (e.g. `~/.claude/projects/...-worktrees-<name>/`). After the worktree is deleted, `claude --resume <id>` fails with "No conversation found" because the session is not discoverable from the main project directory. To recover, either:
1. Re-create the worktree directory so the path matches again, or
2. Copy the `.jsonl` session file into the main project's session directory.

Prevention: commit work to a branch before allowing worktree cleanup (the branch survives deletion), and `/rename` sessions early so they are easy to find.

## When Invoked as Skill

Run the script with the user's keywords and present the results (most recent first). If nothing matches, retry once with broader or alternative keywords before reporting no results. If they want to resume, give them the resume command. For worktree sessions, warn that resume will NOT work if the worktree no longer exists and explain the recovery options above.
