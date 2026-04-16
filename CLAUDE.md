# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Cortex is a **Claude Code plugin** — a collection of skills (markdown-based automation instructions) and hooks (permission gates) distributed via the Claude Code plugin marketplace. There is no build system, no compiled code, and no test suite. The artifacts are SKILL.md files and hook configurations.

## Repository Structure

```
plugins/cortex/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata (name, version, author)
├── hooks/
│   └── hooks.json           # Hook registrations (array of hook definitions)
└── skills/
    └── <skill-name>/
        └── SKILL.md          # Skill definition (frontmatter + instructions)
```

Each skill lives on its own `skill/<name>` branch during development and merges to `main` when ready.

## Skill Anatomy

Every SKILL.md has YAML frontmatter followed by markdown instructions:

```yaml
---
name: skill-name
description: When/how Claude should trigger this skill
disable-model-invocation: true   # true = manual only (/cortex:skill-name), false = auto-triggered
argument-hint: <expected-args>   # shown in /help
model: sonnet                    # optional model override
allowed-tools: Read, Grep, Glob  # optional tool whitelist
---

# Instructions Claude follows when the skill is invoked
```

Key frontmatter fields:
- `description` — doubles as the trigger condition for auto-invoked skills; be specific
- `disable-model-invocation` — set `true` for user-invoked skills, `false` for auto-triggered
- `allowed-tools` — restricts which tools the skill can call; omit to allow all

## Development Workflow

1. Branch from `main`: `git checkout -b skill/<skill-name>`
2. Create `plugins/cortex/skills/<skill-name>/SKILL.md`
3. Open PR, get review, merge

## Skill Writing Rules

- **Keep skills generic** — they run across different repos. Reference the target repo's CLAUDE.md for project-specific conventions instead of hardcoding
- **Auto-detect context** — detect package managers, resolve file paths from user arguments, use repo clues
- **Instructions are literal** — Claude Code follows the markdown steps exactly; be explicit about edge cases and error handling
- **Use sub-agents for parallel work** — complex skills (like deep-research) spawn agents with cost-optimized models (sonnet) while the main session orchestrates
- **Pipe stdin for context** — when skills need to pass file contents to external CLIs, concatenate and pipe rather than using temp files

## External CLI Dependencies

Skills invoke external CLIs via Bash — there are no SDK integrations:
- `gh` — GitHub CLI (babysit-pr)
- `clickup` — ClickUp CLI (clickup-cli)
- `gws` — Google Workspace CLI (gws-cli)
- `codex` — OpenAI Codex CLI (codex-ask)

Install commands for every CLI live in the repo-root `SETUP.md`. Each CLI-dependent SKILL.md carries a short `## Prerequisites` section pointing users to the matching section of `SETUP.md` when the binary is missing — do not inline install walkthroughs in SKILL.md (dead weight on every invocation; progressive disclosure via SETUP.md is the convention).

## Hooks

Hooks in `hooks.json` register permission gates that auto-allow read-only CLI operations and prompt for writes. Each hook entry specifies the tool pattern to match and the allow/deny logic.
