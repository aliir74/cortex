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
| `create-plan` | Writing a structured implementation plan to disk as interactive HTML — "create plan", "plan this" |
| `create-plan-and-execute` | Planning and executing in one go (HTML plan) — "plan and execute", "plan and ship" |
| `create-plan-and-execute-md` | Planning and executing in one go (markdown plan) — "plan and execute markdown" |
| `create-plan-md` | Writing a plain markdown implementation plan — "create markdown plan" |
| `deep-research` | Researching topics — "what's the latest on X", "research X for me" |
| `elevenlabs-voice` | Transcribing audio (with speaker diarization) or generating speech via ElevenLabs |
| `exa-cli` | Exa AI neural search, grounded cited answers, clean content extraction for URLs |
| `execute-plan-md` | Executing a markdown plan task-by-task — "execute markdown plan" |
| `execute-plan` | Executing an HTML plan task-by-task with per-step verification and commits — "execute plan", "run the plan" |
| `fetch-raindrop-bookmarks` | Fetching and triaging Raindrop.io bookmarks |
| `fetch-twitter-bookmarks` | Fetching and triaging Twitter/X bookmarks |
| `figma-cli` | Reading Figma files — node trees, copy, rendering frames to PNG/SVG (read-only) |
| `gemini-cli` | Asking Google Gemini, second opinions, managing Gemini CLI extensions/MCP servers |
| `glab-cli` | Running GitLab operations — MRs, pipelines, issues, CI logs |
| `gws-cli` | Interacting with Google Workspace (Gmail, Calendar, Drive, Sheets) |
| `how-to-html` | Generating or substantially editing an HTML file — plans, reports, dashboards, custom-editor UIs, slides. Ships a diagram geometry verifier, a content density lint, and collapse-layer / report-nav installers |
| `imsg-cli` | Reading and sending iMessage/SMS on a Mac — chats, history, search |
| `ntn-cli` | Notion via the official `ntn` CLI — pages as Markdown, data sources, raw API, Workers |
| `python-project-setup` | Setting up new Python projects (uv + ruff + pyright + pytest) |
| `signal-cli` | Interacting with Signal — receiving, contacts, groups, sending messages |
| `slack-cli` | Interacting with Slack — reading, searching, sending, reactions |
| `snow-cli` | Running Snowflake operations — SQL queries, schema inspection, stages, Cortex |
| `stripe-cli` | Stripe in test mode — customers, charges, subscriptions, invoices, webhooks |
| `tgcli` | Interacting with Telegram — reading chats, sending messages, searching |
| `unleash-cli` | Unleash feature flags — state per environment, toggles, rollouts, audit log |

## Shared Hooks

### ClickUp Permission Gate

Auto-allows read-only ClickUp commands (`task view`, `task list`, `task search`, etc.). Write operations (`task edit`, `comment add`, `status set`) prompt for user confirmation.

### Google Workspace Permission Gate

Auto-allows read-only Google Workspace commands (`+triage`, `+agenda`, `+read`, message list/get). Write operations (`+send`, `+insert`, event create/update/delete) prompt for user confirmation.

### Snowflake Permission Gate

Auto-allows read-only Snowflake commands (`snow connection`, `snow object list/describe`, `snow stage list`, `snow cortex`, `snow logs`). Write/execute operations (`snow sql`, `create`, `drop`, `deploy`, `copy`) prompt for user confirmation.

### Gemini Permission Gate

Auto-allows headless `gemini -p` prompts and read-only listings (`mcp/extensions/skills list`, `gemma status/logs`). Yolo mode (`-y`, `--approval-mode yolo`), `--skip-trust`, and config changes (`mcp add`, `extensions install`, `gemma setup`) prompt for confirmation.

### iMessage Permission Gate

Auto-allows read-only `imsg` commands (`chats`, `history`, `search`, `watch`, `account`, `status`). Sends, reactions, edits, deletes and chat changes prompt for confirmation.

### Notion (ntn) Permission Gate

Auto-allows read-only `ntn` commands (GET-style `ntn api`, `v1/search`, database queries, `pages get`, `datasources query`, `whoami`, `doctor`). Page writes, `ntn api` calls with a body or mutating method, file uploads, Workers ops and `ntn auth token` prompt for confirmation.

### Signal Permission Gate

Auto-allows read-only `signal-cli` commands (`list*`, `get*`, `receive`, `version`). Every send, group/profile/device change, trust change and account operation prompts for confirmation.

### Stripe Permission Gate

Hard-blocks anything touching live mode (`--live`, `sk_live_`/`rk_live_`/`pk_live_` keys, a live `STRIPE_API_KEY`). Auto-allows test-mode reads (`list`, `retrieve`, `search`, `get`, `logs`, `listen`, `whoami`). Test-mode writes prompt for confirmation.

### Unleash Permission Gate

Auto-allows read-only `unleash` wrapper commands (`whoami`, `events`, `flags list`, `flag get/strategies`, `api GET`). Flag create/toggle/rollout/archive and mutating `api` calls prompt for confirmation.

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
| `elevenlabs-voice` | `curl`, `jq`, `python3`, ElevenLabs API key |
| `exa-cli` | `uv`, Exa API key |
| `fetch-raindrop-bookmarks` | Raindrop.io API token |
| `how-to-html` | `python3` 3.9+ (stdlib only, for the bundled verifier, density lint and installers) |
| `fetch-twitter-bookmarks` | `bird` (Twitter/X CLI); optional `yt-dlp` for media |
| `figma-cli` | `python3`, Figma personal access token |
| `gemini-cli` | `gemini` (Google Gemini CLI), `GEMINI_API_KEY` |
| `glab-cli` | `glab` (GitLab CLI) |
| `gws-cli` | `gws` (Google Workspace CLI) |
| `imsg-cli` | `imsg` (iMessage CLI, macOS only) |
| `ntn-cli` | `ntn` (Notion CLI) |
| `python-project-setup` | `uv` |
| `signal-cli` | `signal-cli`; `qrencode` for device linking |
| `slack-cli` | `agent-slack` (Slack CLI) |
| `snow-cli` | `snow` (Snowflake CLI) |
| `stripe-cli` | `stripe` (Stripe CLI) |
| `tgcli` | `tgcli` (Telegram CLI) |
| `unleash-cli` | `python3`, Unleash Admin API token |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new skills and the PR process.

## License

MIT
