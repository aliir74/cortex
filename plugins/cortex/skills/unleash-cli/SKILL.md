---
name: unleash-cli
description: Use when working with Unleash feature flags - listing flags, checking a flag's state per environment, toggling flags on/off, setting gradual rollout percentages, creating or archiving flags, and reading the audit log. Triggers on "check the flag", "is X enabled", "toggle flag", "feature flag", "unleash", "rollout percentage", "flag state in production", "list feature flags".
model: sonnet
---

# Unleash feature flags with the `unleash` CLI

`unleash` is a stdlib-only Python wrapper over the Unleash **Admin REST API** that ships inside this skill (there is no official Unleash management CLI). It is non-interactive and JSON-capable, so it is safe to script and to drive from an agent. Verified against Unleash API 8.1.0.

```bash
"${CLAUDE_PLUGIN_ROOT}/skills/unleash-cli/unleash" whoami
```

Every `unleash ...` example below means `"${CLAUDE_PLUGIN_ROOT}/skills/unleash-cli/unleash" ...`. The bundled permission hook recognises both forms.

## Prerequisites

Requires `python3` and an Unleash Admin API token. If `unleash whoami` fails with "no base URL" or "no token", point the user to `SETUP.md` at the plugin root (section: **unleash-cli**) and stop until it's configured.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/unleash-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/unleash-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/unleash-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/unleash-cli.md` — edit anytime to customize."
2. Read it. When `default_profile` is set, pass `--profile <value>` on every call. When `default_project` is set, pass `--project <value>` to `flag` subcommands. `production_environments` lists environment names that count as production for the confirmation rule below (default: `production`). Empty fields fall back to the CLI defaults (profile `default`, project `default`).

## Auth & Setup

Credentials live in `~/.unleash.env` (chmod 600), read automatically:

```
UNLEASH_URL=https://unleash.example.com
UNLEASH_PAT=<personal access token>
UNLEASH_URL_STAGING=https://unleash-staging.example.com
UNLEASH_PAT_STAGING=<personal access token>
```

Profile `default` reads the unsuffixed pair; `--profile <name>` reads `UNLEASH_URL_<NAME>` / `UNLEASH_PAT_<NAME>`. `$UNLEASH_PROFILE` sets the default profile; `--base-url` overrides the URL for one call.

**The token must be a Personal Access Token or a service account token.** An SDK *client/server* token returns 401 against `/api/admin`. The user creates a PAT in the Unleash UI under **Profile > Personal API tokens**; never generate or rotate one unasked, and never print a token.

Verify auth: `unleash whoami`

## Quick Reference

| Task | Command |
|------|---------|
| Confirm the token works | `unleash whoami` |
| List projects | `unleash projects list` |
| List environments | `unleash envs list` |
| List flags (newest first) | `unleash flags list` |
| Search flags by name/tag | `unleash flags list --query checkout` |
| Flags in one project | `unleash flags list --project default` |
| Filter by flag type | `unleash flags list --type kill-switch` |
| Show one flag + all env states | `unleash flag get my-flag` |
| Show a flag's strategies in an env | `unleash flag strategies my-flag --env production` |
| Create a flag | `unleash flag create my-flag --type release --description "..."` |
| Turn a flag on | `unleash flag toggle my-flag --env production --on` |
| Turn a flag off | `unleash flag toggle my-flag --env production --off` |
| Set gradual rollout | `unleash flag rollout my-flag --env production --percent 25` |
| Archive a flag | `unleash flag archive my-flag` |
| Recent audit events | `unleash events --limit 25` (client-side; `--limit 0` for all) |
| Anything not wrapped | `unleash api GET /api/admin/projects` |
| Target another instance | `unleash --profile staging flags list` |
| Raw JSON for parsing | `--json` (valid before OR after the subcommand) |

## Read vs Write Operations

**Read (safe):** `whoami`, `projects list`, `envs list`, `strategies list`, `flags list`, `flag get`, `flag strategies`, `events`, and `api GET`.

**Write (gated by the bundled `unleash-permission-check.sh` hook):** `flag create`, `flag toggle`, `flag rollout`, `flag archive`, and `api` with POST/PUT/PATCH/DELETE. The hook returns `allow` for reads and `ask` for every write, so do not add a blanket `unleash` allow rule to your permission settings: it would approve a production toggle before the hook is consulted.

## Command Notes

### `flags list`
Uses the Admin search endpoint, so it spans projects by default. Prints a compact `environments` column like `production=on, development=off`. Filters: `--query`, `--project`, `--type`, `--tag`, `--limit`, `--sort-by`, `--sort-order`.

### `flag toggle`
Only flips the environment's enabled switch. A flag that is on but has no strategy, or a `flexibleRollout` at 0%, still serves nothing. When asked "is X live in production", check `flag get` **and** `flag strategies`, not just the on/off state.

### `flag rollout`
Sets the `rollout` parameter on the environment's `flexibleRollout` strategy. Updates the existing one when there is exactly one, adds one when there are none, and **refuses to guess** when several exist (edit those in the UI or via `unleash api`). Defaults `groupId` to the flag name and `stickiness` to `default`.

### `flag archive`
Archives rather than deletes; recoverable from the Unleash archive. There is deliberately no hard-delete command.

### `events`
`/api/admin/events` accepts **only** a `project` param and has no server-side limit, so `--limit` is applied client-side (it prints `showing N of M` to stderr). Do not add `limit` as a query param: the API ignores it silently.

### `whoami`
`/api/admin/user` does not return `rootRole`, so the `ACCESS` column is derived from the permissions list: an `ADMIN` entry means a root admin token that can write to every project.

### `api`
Escape hatch for the admin operations not wrapped here (segments, tags, api-tokens, project access, context fields, addons). Always emits raw JSON.

```bash
unleash api GET /api/admin/projects/default/features/my-flag/tags
unleash api POST /api/admin/tag-types -d '{"name":"team","description":"owning team"}'
```

## Behavioral Rules

- **Say which instance you hit.** State the profile (and its URL host) in any answer about flag state.
- **"On in Unleash" does not prove the app sees it.** An application may read flags from a different Unleash instance or a cached/proxied source. Confirm the app's flag source before concluding anything about its runtime behaviour.
- **Never toggle, roll out, create or archive a flag in a production environment without the user confirming** the flag name and environment in chat, even though the hook also prompts.
- **Read before writing.** Run `flag get` first so you can report what actually changed.
- **Prefer `--json` when parsing**, table output when reporting. Global flags (`--json`, `--profile`, `--base-url`) work before or after the subcommand.
- A DNS failure on an internal-only instance usually means you are off-network, not that the CLI is broken.

## Extending

Endpoint shapes come from the instance's own OpenAPI spec (`<instance>/docs/openapi.json`); verify there before adding a command.
