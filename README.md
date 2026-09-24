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
| `helpers` | Shared stdlib-only scripts (adherence probes, corpus measurement, skill audit, safe description edits) used by other skills; not a workflow on its own | `python3 <plugin>/skills/helpers/<script> --help` |
| `make-slides` | Build an HTML slide deck from the MIT beautiful-html-templates library (by Zara Zhang) | `/cortex:make-slides pitch deck for X` |
| `session-handoff` | Generate structured handoff document for another agent/engineer | `/cortex:session-handoff` |

### Auto-Triggered

These skills activate automatically when Claude detects you're working in a relevant area:

| Skill | Triggers When |
|-------|---------------|
| `bird-cli` | Interacting with Twitter/X — reading, searching, posting, replies, bookmarks |
| `clickup-cli` | Running ClickUp operations — tasks, comments, search, sprints, time tracking |
| `compare-skillsets` | Weighing an external skillset or plugin against your installed skills |
| `convert-date` | Converting between Shamsi/Jalali and Gregorian calendars |
| `create-permission-hook` | Creating permission hooks for CLI tools |
| `create-plan-and-execute-md` | Planning and executing in one go (markdown plan) — "plan and execute markdown" |
| `create-plan-and-execute` | Planning and executing in one go (HTML plan) — "plan and execute", "plan and ship" |
| `create-plan-md` | Writing a plain markdown implementation plan — "create markdown plan" |
| `create-plan` | Writing a structured implementation plan to disk as interactive HTML — "create plan", "plan this" |
| `cut-clip` | Cutting a video/audio segment, with boundaries given as spoken phrases |
| `deep-research` | Researching topics — "what's the latest on X", "research X for me" |
| `execute-plan` | Executing an HTML plan task-by-task with per-step verification and commits — "execute plan", "run the plan" |
| `execute-plan-md` | Executing a markdown plan task-by-task — "execute markdown plan" |
| `fetch-raindrop-bookmarks` | Fetching and triaging Raindrop.io bookmarks |
| `fetch-twitter-bookmarks` | Fetching and triaging Twitter/X bookmarks |
| `generate-image` | Generating or editing an image (OpenAI GPT Image or Gemini Nano Banana) |
| `glab-cli` | Running GitLab operations — MRs, pipelines, issues, CI logs |
| `gws-cli` | Interacting with Google Workspace (Gmail, Calendar, Drive, Sheets) |
| `how-to-html` | Generating or substantially editing an HTML file — plans, reports, dashboards, custom-editor UIs, slides. Ships a diagram geometry verifier, a content density lint, and collapse-layer / report-nav installers |
| `integrate-cli` | Onboarding a new CLI end-to-end — research, install, auth, generate a `<tool>-cli` skill and permission hook |
| `learn-from` | Turning mistakes and corrections in the current conversation into edits to CLAUDE.md, memory, or skill files |
| `md-to-pdf` | Converting a markdown file (Obsidian-flavoured supported) to PDF |
| `post-mortem` | Writing a blameless postmortem / RCA |
| `python-project-setup` | Setting up new Python projects (uv + ruff + pyright + pytest) |
| `quick-search` | Fast single-fact web lookups: docs, syntax, versions |
| `refine-english` | Refining text to sound native, writing feedback, pronunciation help |
| `slack-cli` | Interacting with Slack — reading, searching, sending, reactions |
| `snow-cli` | Running Snowflake operations — SQL queries, schema inspection, stages, Cortex |
| `summarize-content` | Summarising a URL, YouTube video, podcast, or local media file |
| `tgcli` | Interacting with Telegram — reading chats, sending messages, searching |
| `update-cli` | Upgrading an installed CLI and syncing its `<tool>-cli` skill and permission hook with new/removed commands |
| `update-permissions` | Adding, removing, or changing Claude Code permission rules and hooks, with consolidation and a security review |
| `why-you-asked-me` | Diagnosing why Claude prompted for permission on a command that should have been auto-allowed |
| `writing-skills` | Creating or editing a skill or a CLAUDE.md rule — triggers-only descriptions, form-to-failure, probe-first testing |

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
| `cut-clip` | `yt-dlp`, `ffmpeg`, `curl`, ElevenLabs API key |
| `fetch-raindrop-bookmarks` | Raindrop.io API token |
| `how-to-html` | `python3` 3.9+ (stdlib only, for the bundled verifier, density lint and installers) |
| `fetch-twitter-bookmarks` | `bird` (Twitter/X CLI); optional `yt-dlp` for media |
| `generate-image` | `OPENAI_API_KEY` and/or `GEMINI_API_KEY` |
| `glab-cli` | `glab` (GitLab CLI) |
| `gws-cli` | `gws` (Google Workspace CLI) |
| `helpers` | `python3`; `claude` CLI on PATH for `adherence-probe.py` |
| `integrate-cli` | `jq` (for generated permission hooks) |
| `make-slides` | `git` |
| `md-to-pdf` | `pandoc`, Google Chrome or Chromium |
| `python-project-setup` | `uv` |
| `slack-cli` | `agent-slack` (Slack CLI) |
| `snow-cli` | `snow` (Snowflake CLI) |
| `summarize-content` | `summarize` CLI |
| `tgcli` | `tgcli` (Telegram CLI) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new skills and the PR process.

## License

MIT
