---
name: glab-cli
description: Use when running GitLab operations beyond simple git commands - creating merge requests, viewing CI/CD pipelines, managing issues, checking pipeline logs, or any glab CLI interaction.
model: sonnet
---

# GitLab with glab CLI

## Prerequisites

Requires the `glab` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **glab-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/glab-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/glab-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/glab-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/glab-cli.md` — edit anytime to customize."
2. Read it. When `default_host` is set, use it as the GitLab host (`glab` honors `GITLAB_HOST` env var or `glab config set -g host <host>`); only override when the user names a different instance. Use `default_group` and `default_project` to scope `glab issue`/`glab mr`/`glab api` calls when the current directory is not a GitLab clone. Read each path under `context_files` for additional context (e.g., MR description boilerplate). Empty fields mean "use the CLI's auto-detection or ask the user."

## Overview

`glab` is the GitLab CLI. Use it for all GitLab platform operations (MRs, CI/CD, issues). Use plain `git` for commits, branches, push, pull, and other core git operations.

## Quick Reference

| Task | Command |
|------|---------|
| Create MR | `glab mr create -t "title" -d "description" --remove-source-branch --squash-before-merge` |
| List MRs | `glab mr list` / `glab mr ls` |
| View MR | `glab mr view <id>` |
| View MR in browser | `glab mr view <id> --web` |
| View MR comments | `glab mr view <id> --comments` |
| Merge MR | `glab mr merge <id> -s -d` (squash + delete branch) |
| Approve MR | `glab mr approve <id>` |
| MR diff | `glab mr diff <id>` |
| Checkout MR | `glab mr checkout <id>` |
| Update MR | `glab mr update <id> -t "new title" -l "label1,label2"` |
| CI status | `glab ci status` |
| CI status (live) | `glab ci status --live` |
| CI view (interactive) | `glab ci view` |
| CI pipeline list | `glab ci list` |
| CI trace job log | `glab ci trace <job_id>` |
| CI retry job | `glab ci retry <job_id>` |
| CI cancel | `glab ci cancel <job_id>` |
| Run pipeline | `glab ci run` |
| Create issue | `glab issue create -t "title" -d "description"` |
| List issues | `glab issue list` / `glab issue ls` |
| View issue | `glab issue view <id>` |
| API call | `glab api <endpoint>` |

## Merge Request Creation

When project conventions require it, include these flags on `glab mr create`:

```bash
glab mr create \
  -t "mr title" \
  -d "$(cat <<'EOF'
## Summary
- Description of changes

## Test plan
- [ ] Test steps
EOF
)" \
  --remove-source-branch \
  --squash-before-merge
```

Check the target repo's `CONTRIBUTING.md` or `CLAUDE.md` for any required MR description checkboxes (security/test/docs assessments) and add them to the body.

### Useful MR create flags

| Flag | Short | Description |
|------|-------|-------------|
| `--title` | `-t` | MR title |
| `--description` | `-d` | MR body |
| `--assignee` | `-a` | Assign by username |
| `--reviewer` | | Request review by username |
| `--label` | `-l` | Comma-separated labels |
| `--target-branch` | `-b` | Target branch (default: project default) |
| `--source-branch` | `-s` | Source branch (default: current) |
| `--draft` | | Mark as draft |
| `--remove-source-branch` | | Delete branch on merge |
| `--squash-before-merge` | | Squash commits |
| `--fill` | `-f` | Auto-fill from commits, push, skip prompts |
| `--related-issue` | `-i` | Link to issue |
| `--web` | `-w` | Open in browser to finish |
| `--yes` | `-y` | Skip confirmation prompt |

## CI/CD Operations

### Viewing pipeline status

```bash
# Current branch status
glab ci status

# Live-updating status
glab ci status --live

# Compact view
glab ci status --compact

# Specific branch
glab ci status -b main
```

### Interactive pipeline viewer

```bash
glab ci view          # Current branch
glab ci view main     # Specific branch
glab ci view --web    # Open in browser
```

**Keybindings in interactive view:**
- `Enter` — toggle job logs/traces
- `Esc`/`q` — close logs, go back
- `Ctrl+R`/`Ctrl+P` — run/retry/play a job
- `Ctrl+D` — cancel a job
- `Ctrl+Q` — quit
- `Ctrl+Space` — suspend and view logs

### Tracing job logs

```bash
glab ci trace              # Interactive job selection
glab ci trace <job_id>     # Specific job by ID
glab ci trace lint         # Specific job by name
glab ci trace -b main      # Job from specific branch
```

### Pipeline list with filters

```bash
glab ci list                          # All pipelines
glab ci list --status=failed          # Failed only
glab ci list -s running               # Running only
glab ci list -u username              # By user
glab ci list --sort asc               # Oldest first
glab ci list -F json                  # JSON output
```

## Issue Operations

### Create issue

```bash
glab issue create -t "Bug: login fails" -d "Steps to reproduce..." -l "bug,priority::high"
glab issue create -t "title" -m "milestone-name" -a username
```

### List/filter issues

```bash
glab issue list                          # Open issues
glab issue list --all                    # All issues
glab issue list --assignee=@me           # Assigned to me
glab issue list -l "bug" -c              # Closed bugs
glab issue list --search "login"         # Search
glab issue list --milestone release-2.0  # By milestone
```

## API Access

For anything not covered by built-in commands:

```bash
glab api projects/:id/pipelines
glab api projects/:id/merge_requests
```

When operating outside a GitLab clone, scope the call with `--repo`:

```bash
glab mr list --repo <group>/<project>
glab api projects/<group>%2F<project>/merge_requests
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `gh` instead of `glab` | This is a GitLab repo — always use `glab` |
| Missing `--remove-source-branch` / `--squash-before-merge` when project requires them | Check the repo's `CONTRIBUTING.md` and add when required |
| Missing required MR description checkboxes | Check the repo's `CONTRIBUTING.md` and add the required assessment checkboxes |
| Using `glab` for git commit/push | Use plain `git` for core git operations |
| Using `--no-verify` on push | Never use unless the user explicitly requests |

## Multi-Host

If you work against multiple GitLab instances (e.g., gitlab.com plus self-hosted), set the host per-command:

```bash
GITLAB_HOST=gitlab.example.com glab mr list
```

Or persist via `glab config set -g host gitlab.example.com` and use `default_host` in preferences for the most-common host.
