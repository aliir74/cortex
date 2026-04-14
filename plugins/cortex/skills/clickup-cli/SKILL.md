---
name: clickup-cli
description: Use when running ClickUp operations - creating/viewing/editing tasks, adding comments, searching, listing members, managing sprints, checklists, dependencies, time tracking, or any ClickUp CLI interaction.
model: sonnet
argument-hint: <task-id or search query>
---

# ClickUp with clickup CLI

## Overview

`clickup` is the ClickUp CLI. Use it for all ClickUp platform operations (tasks, comments, search, sprints).

## Quick Reference

| Task | Command |
|------|---------|
| View task | `clickup task view <id>` |
| View task (auto-detect from branch) | `clickup task view` |
| Create task | `clickup task create --list-id <LIST_ID> --name "..."` |
| Edit task | `clickup task edit <id> --status "in progress"` |
| List tasks | `clickup task list --list-id <LIST_ID>` |
| Search tasks | `clickup task search "query"` |
| Recent tasks | `clickup task recent` |
| Add comment | `clickup comment add <id> "message"` |
| List comments | `clickup comment list <id>` |
| List members | `clickup member list` |
| Current sprint | `clickup sprint current` |
| Check inbox | `clickup inbox` |
| Link PR | `clickup link pr` |
| View activity | `clickup task activity <id>` |

## Task Operations

### View

```bash
# View specific task
clickup task view 86a3xrwkp
clickup task view CU-abc123

# Auto-detect from git branch (CU-<id> pattern)
clickup task view

# JSON output (includes subtasks with IDs, dates, statuses)
clickup task view 86a3xrwkp --json
```

### Create

```bash
# Basic creation (get list ID from your workspace)
clickup task create --list-id <LIST_ID> --name "[Bug] Auth — Fix login timeout (API)"

# With markdown description
clickup task create --list-id <LIST_ID> \
  --name "[Feature] Deploy — Release v2" \
  --markdown-description "## Problem\n\nDescription here"

# With priority and due date
clickup task create --list-id <LIST_ID> \
  --name "Task name" --priority 2 --due-date 2026-03-15

# With custom field
clickup task create --list-id <LIST_ID> \
  --name "Task name" --field "Environment=staging"

# Create subtask
clickup task create --list-id <LIST_ID> \
  --name "Write tests" --parent 86abc123

# With tags
clickup task create --list-id <LIST_ID> \
  --name "Task name" --tags "security,urgent"

# Bulk create from JSON file
clickup task create --list-id <LIST_ID> --from-file tasks.json
```

**Creation rules:**
- Always use `--markdown-description` (not `--description`) for formatted content
- NEVER auto-assign to anyone unless explicitly asked
- Flag is `--list-id`, NOT `--list`
- **Tags flag is `--tags`** (not `--add-tags` — that's only for `task edit`)

### Edit

```bash
# Edit specific task
clickup task edit CU-abc123 --status "in progress" --priority 2

# Auto-detect from git branch
clickup task edit --status "in progress"

# Change assignees
clickup task edit <id> --assignee 12345 --remove-assignee 67890

# Set/clear custom fields
clickup task edit <id> --field "Environment=production"
clickup task edit <id> --clear-field "Environment"

# Due dates and time estimates
clickup task edit <id> --due-date 2026-03-15 --time-estimate 4h
clickup task edit <id> --due-date none  # clear due date

# Tags
clickup task edit <id> --add-tags "new-feature"
clickup task edit <id> --remove-tags "fix"

# Bulk edit (same changes to multiple tasks)
clickup task edit 86abc1 86abc2 86abc3 --status "Closed"
```

### List

```bash
# List tasks in a list
clickup task list --list-id <LIST_ID>

# Filter by assignee and status
clickup task list --list-id <LIST_ID> --assignee me --status "in progress"

# Filter by sprint
clickup task list --list-id <LIST_ID> --sprint "Sprint 12"

# Pagination
clickup task list --list-id <LIST_ID> --page 1
```

### Search

```bash
# Basic search (progressive drill-down: sprint > assigned > space > workspace)
clickup task search "payload"

# Search in specific space/folder
clickup task search "geozone" --space Development
clickup task search "nextjs" --folder "Engineering Sprint"

# Search including comments
clickup task search "migration issue" --comments

# Exact matches only
clickup task search "deploy" --exact

# Interactive pick (prints selected task ID)
clickup task search "geozone" --pick

# JSON output
clickup task search "query" --json
```

**If search returns nothing:** Use `clickup task recent` first to discover active folders/lists, then search with `--folder`.

### Recent Tasks

```bash
clickup task recent
```

### Delete

```bash
clickup task delete <id>
```

## Comments

```bash
# Add comment (keep brief, use full @mention usernames)
clickup comment add <task-id> "@Jane Doe code review done, approved."

# List comments
clickup comment list <task-id>

# Edit comment
clickup comment edit <comment-id> "Updated text"

# Delete comment
clickup comment delete <comment-id>
```

**Comment rules:**
- Always use full workspace username for @mentions (e.g., `@Jane Doe` not `@Jane`)
- Keep comments brief — signal the action, don't replicate PR details
- ClickUp comments don't render markdown. Use plain text with unicode bullets for lists and CAPS or spacing for emphasis.

## Custom Fields

```bash
# Discover available fields in a list
clickup field list --list-id <LIST_ID>

# Set field on task
clickup task edit <id> --field "Primary Developer=username"
clickup task create --list-id <LIST_ID> --name "Task" --field "Environment=staging"

# Clear field
clickup task edit <id> --clear-field "Environment"
```

## Members & Sprints

```bash
# List workspace members
clickup member list

# List sprints
clickup sprint list

# Current sprint tasks
clickup sprint current
```

## Checklists & Dependencies

### Checklists

```bash
# Add a checklist to a task
clickup task checklist add <task-id> --name "QA Checklist"

# Manage checklist items
clickup task checklist item  # see subcommands

# Remove a checklist
clickup task checklist remove <task-id> --checklist <checklist-id>

# Find checklist/item IDs
clickup task view <task-id> --json
```

### Dependencies

```bash
# Add dependency
clickup task dependency add <task-id> --depends-on <other-task-id>

# Remove dependency
clickup task dependency remove <task-id> --depends-on <other-task-id>
```

## Time Tracking

```bash
# Log time to a task
clickup task time log <task-id> --duration "2h30m"

# View time entries
clickup task time list <task-id>

# Delete a time entry
clickup task time delete <entry-id>
```

## Inbox (Mentions)

```bash
# Recent @mentions (last 7 days)
clickup inbox

# Look back further
clickup inbox --days 30

# JSON output
clickup inbox --json
```

## Git Integration

```bash
# Auto-detect task from branch name (CU-<id> pattern)
clickup task view
clickup task edit --status "in progress"

# Link current PR to task
clickup link pr

# Link branch to task
clickup link branch

# Link commit to task
clickup link commit

# Sync task info to GitHub PR
clickup link sync
```

## Tags & Statuses

```bash
# List tags in a space
clickup tag list --space <space-id>

# List available statuses
clickup status list --space <space-id>

# Set task status directly
clickup status set <task-id> "in review"
```

## Output Flags

| Flag | Description |
|------|-------------|
| `--json` | Structured JSON output (use when parsing results) |
| `--jq "<expr>"` | Filter JSON with jq expression |
| `--template "<go-tmpl>"` | Format with Go template |

**Always use `--json` when parsing results programmatically.**

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using `--list` instead of `--list-id` | Flag is `--list-id` |
| Using `--description` for formatted content | Use `--markdown-description` for markdown |
| Auto-assigning tasks on creation | NEVER auto-assign unless user explicitly asks |
| Using partial @mentions in comments | Always use full username (e.g., `@Jane Doe`) |
| Searching with no results and giving up | Use `clickup task recent` to find active folders first |
| `status set` fails for lists with custom statuses | Known CLI bug — lists with custom status overrides may fail. User must set status manually in ClickUp UI until fixed. |
| Bypassing CLI with raw API calls when a command fails | Investigate the CLI limitation first (docs/source code/GitHub issues). Only use raw API for confirmed CLI bugs. |
| Using markdown syntax in comments | ClickUp comments don't render markdown. Use plain text with unicode bullets and CAPS for emphasis. |
| Targeting a deployed/closed task when an active one exists | When search returns multiple tasks, prefer the active/open task over deployed/closed ones. |
