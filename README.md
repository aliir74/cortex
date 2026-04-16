# Cortex

Claude Code skills for developer productivity, research, communication, and workflow automation.

## Setup

### 1. Add the marketplace

```bash
claude plugin marketplace add aliir74/cortex
```

### 2. Install the plugin

```bash
claude plugin install cortex
```

After this, updates pull automatically at Claude Code startup.

## Available Skills

Invoke skills with `/cortex:<skill-name>`.

### User-Invoked

| Skill | Description | Usage |
|-------|-------------|-------|
| `babysit-pr` | Monitor a PR — auto-fix CI failures, address review feedback, track deploys | `/loop 5m /cortex:babysit-pr #123` |
| `codex-ask` | Get a second opinion from OpenAI Codex CLI | `/cortex:codex-ask Is this approach correct?` |
| `commit-push-pr` | Stage, commit, push, and open a PR/MR in one flow (auto-detects GitHub vs GitLab) | `/cortex:commit-push-pr` |
| `session-handoff` | Generate structured handoff document for another agent/engineer | `/cortex:session-handoff` |

### Auto-Triggered

These skills activate automatically when Claude detects you're working in a relevant area:

| Skill | Triggers When |
|-------|---------------|
| `bird-cli` | Interacting with Twitter/X — reading, searching, posting, replies, bookmarks |
| `clickup-cli` | Running ClickUp operations — tasks, comments, search, sprints, time tracking |
| `convert-date` | Converting between Shamsi/Jalali and Gregorian calendars |
| `create-permission-hook` | Creating permission hooks for CLI tools |
| `deep-research` | Researching topics — "what's the latest on X", "research X for me" |
| `fetch-raindrop-bookmarks` | Fetching and triaging Raindrop.io bookmarks |
| `fetch-twitter-bookmarks` | Fetching and triaging Twitter/X bookmarks |
| `glab-cli` | Running GitLab operations — MRs, pipelines, issues, CI logs |
| `gws-cli` | Interacting with Google Workspace (Gmail, Calendar, Drive, Sheets) |
| `python-project-setup` | Setting up new Python projects (uv + ruff + pyright + pytest) |
| `slack-cli` | Interacting with Slack — reading, searching, sending, reactions |
| `snow-cli` | Running Snowflake operations — SQL queries, schema inspection, stages, Cortex |
| `tgcli` | Interacting with Telegram — reading chats, sending messages, searching |

## Shared Hooks

### ClickUp Permission Gate

Auto-allows read-only ClickUp commands (`task view`, `task list`, `task search`, etc.). Write operations (`task edit`, `comment add`, `status set`) prompt for user confirmation.

### Google Workspace Permission Gate

Auto-allows read-only Google Workspace commands (`+triage`, `+agenda`, `+read`, message list/get). Write operations (`+send`, `+insert`, event create/update/delete) prompt for user confirmation.

### Snowflake Permission Gate

Auto-allows read-only Snowflake commands (`snow connection`, `snow object list/describe`, `snow stage list`, `snow cortex`, `snow logs`). Write/execute operations (`snow sql`, `create`, `drop`, `deploy`, `copy`) prompt for user confirmation.

## Prerequisites

Some skills require external CLI tools. See [SETUP.md](SETUP.md) for installation instructions.

| Skill | Requires |
|-------|----------|
| `babysit-pr` | `gh` (GitHub CLI) |
| `bird-cli` | `bird` (Twitter/X CLI) |
| `clickup-cli` | `clickup` (ClickUp CLI) |
| `codex-ask` | `codex` (OpenAI Codex CLI) |
| `commit-push-pr` | `gh` and/or `glab` (matches the remote) |
| `convert-date` | `python3` with `jdatetime` |
| `fetch-raindrop-bookmarks` | Raindrop.io API token |
| `fetch-twitter-bookmarks` | `bird` (Twitter/X CLI); optional `yt-dlp` for media |
| `glab-cli` | `glab` (GitLab CLI) |
| `gws-cli` | `gws` (Google Workspace CLI) |
| `python-project-setup` | `uv` |
| `slack-cli` | `agent-slack` (Slack CLI) |
| `snow-cli` | `snow` (Snowflake CLI) |
| `tgcli` | `tgcli` (Telegram CLI) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new skills and the PR process.

## License

MIT
