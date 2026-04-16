# Contributing

## Adding a New Skill

1. Create a directory under `plugins/cortex/skills/`:

```
plugins/cortex/skills/my-skill/
└── SKILL.md
```

2. Write your `SKILL.md` with YAML frontmatter:

```yaml
---
description: Short description shown in /help
argument-hint: <optional-args>
disable-model-invocation: true  # set false if Claude should auto-trigger this skill
---

Detailed instructions for Claude Code to follow when this skill is invoked.
```

3. Open a PR and get at least one review.

### Skill Writing Guidelines

- **Keep skills generic** — they should work across different repos and teams
- **Reference CLAUDE.md** for repo-specific conventions instead of hardcoding them
- **Auto-detect the package manager** when running commands
- **Use clear step-by-step instructions** — Claude Code follows them literally
- **Specify `allowed-tools`** in frontmatter if the skill should only use certain tools

### Frontmatter Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `description` | What the skill does | `description: Monitor a GitHub PR` |
| `argument-hint` | Hint for expected arguments | `argument-hint: <pr-number-or-url>` |
| `disable-model-invocation` | Prevent Claude from auto-triggering | `disable-model-invocation: true` |
| `allowed-tools` | Limit which tools the skill can use | `allowed-tools: Read, Grep, Glob` |
| `model` | Override model for this skill | `model: sonnet` |

## User Preferences

Skills that need user-specific values (workspace IDs, default list IDs, account emails, local file paths) must NOT hardcode them. Instead, use the two-file preferences pattern so each user can customize without forking the skill.

### Why not a gitignored file inside the plugin?

Claude Code does not install plugins as live git clones. It copies them to a versioned cache at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`. Every update creates a new versioned directory and the old one is deleted after 7 days — any file a user drops inside the installed plugin dir is wiped on update. `.gitignore` is irrelevant because the user never has a git checkout.

Use `${CLAUDE_PLUGIN_DATA}` instead — it resolves to `~/.claude/plugins/data/cortex/` and is explicitly designed by Claude Code to persist across plugin updates.

### File layout

```
plugins/cortex/skills/<skill-name>/
├── SKILL.md                    # committed, references preferences
└── preferences.template.md     # committed, documents available fields + defaults
```

Both files are committed. The template is the canonical documentation of what the user can customize.

### SKILL.md preamble

Every skill includes this section near the top, with `<skill-name>` replaced by its actual name (e.g., `clickup-cli`):

```markdown
## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/<skill-name>.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/<skill-name>/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/<skill-name>.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/<skill-name>.md` — edit anytime to customize."
2. Read it. Empty fields fall back to the defaults documented in this SKILL.md; populated fields override them.
```

**Seed-and-continue, don't block.** The first run should not require the user to stop, edit, and re-run. Use sensible defaults documented elsewhere in the SKILL.md, and let the user customize on their own schedule.

### preferences.template.md format

Use markdown, not JSON. Fields are small sections with inline defaults and short descriptions. Partial/missing fields degrade gracefully and users can add comments explaining their choices.

Example:

```markdown
# <skill-name> preferences

## default_list_id
<!-- The ClickUp list where new tasks land when no list is specified -->
default_list_id:

## default_assignee
<!-- Leave empty to default to the current user -->
default_assignee:
```

### Rules for skill authors

- **Never hardcode** user paths, workspace IDs, email addresses, or personal file references in `SKILL.md` — put them in `preferences.template.md`.
- **Always commit** `preferences.template.md` — it IS the documentation of what fields exist.
- **Never commit** user-resolved preferences — those live in `${CLAUDE_PLUGIN_DATA}/preferences/` on each user's machine, outside the repo.
- **Reference the user's file** in SKILL.md as `${CLAUDE_PLUGIN_DATA}/preferences/<skill-name>.md`, not a relative path — there is no `$SKILL_DIR` env var, and CWD is the user's project.

## External CLI Dependencies

If your skill invokes an external CLI binary (e.g., `gh`, `clickup`, `gws`, `codex`):

1. Add a `## Prerequisites` section near the top of your SKILL.md (after the H1 title, before `## User Preferences`):

   ```markdown
   ## Prerequisites

   Requires the `<binary>` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **<skill-name>**) and stop until it's available.
   ```

2. Add a matching entry to the repo-root `SETUP.md` with the install command and any auth step.

Do not inline a full install walkthrough in SKILL.md — it's loaded on every skill invocation and becomes dead weight after first install. SETUP.md is the single source of truth for setup steps.

## Adding or Updating Hooks

Hooks live in `plugins/cortex/hooks/`. The `hooks.json` file registers them with Claude Code.

## PR Process

1. Branch from `main`
2. Add/modify your skill or hook
3. Open a PR
4. Get at least one review
5. Merge
