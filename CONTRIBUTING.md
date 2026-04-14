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

## Adding or Updating Hooks

Hooks live in `plugins/cortex/hooks/`. The `hooks.json` file registers them with Claude Code.

## PR Process

1. Branch from `master`
2. Add/modify your skill or hook
3. Open a PR
4. Get at least one review
5. Merge
