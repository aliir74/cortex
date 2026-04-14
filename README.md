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
| `clickup-cli` | ClickUp CLI operations — tasks, comments, search, sprints, time tracking | `/cortex:clickup-cli` |
| `deploy-preview` | Trigger preview deployment and monitor for deploy URL | `/cortex:deploy-preview` |
| `codex-ask` | Get a second opinion from OpenAI Codex CLI | `/cortex:codex-ask Is this approach correct?` |
| `session-handoff` | Generate structured handoff document for another agent/engineer | `/cortex:session-handoff` |

### Auto-Triggered

These skills activate automatically when Claude detects you're working in a relevant area:

| Skill | Triggers When |
|-------|---------------|
| `deep-research` | Researching topics — "what's the latest on X", "research X for me" |
| `create-permission-hook` | Creating permission hooks for CLI tools |
| `gws-cli` | Interacting with Google Workspace (Gmail, Calendar, Drive, Sheets) |

## Shared Hooks

### ClickUp Permission Gate

Auto-allows read-only ClickUp commands (`task view`, `task list`, `task search`, etc.). Write operations (`task edit`, `comment add`, `status set`) prompt for user confirmation.

### Google Workspace Permission Gate

Auto-allows read-only Google Workspace commands (`+triage`, `+agenda`, `+read`, message list/get). Write operations (`+send`, `+insert`, event create/update/delete) prompt for user confirmation.

## Prerequisites

Some skills require external CLI tools. See [SETUP.md](SETUP.md) for installation instructions.

| Skill | Requires |
|-------|----------|
| `babysit-pr` | `gh` (GitHub CLI) |
| `clickup-cli` | `clickup` (ClickUp CLI) |
| `deploy-preview` | `gh` (GitHub CLI) |
| `gws-cli` | `gws` (Google Workspace CLI) |
| `codex-ask` | `codex` (OpenAI Codex CLI) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add new skills and the PR process.

## License

MIT
