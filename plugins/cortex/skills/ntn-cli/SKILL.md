---
name: ntn-cli
description: Use when interacting with Notion via the official `ntn` CLI — reading/writing pages as Markdown, querying data sources, calling raw API endpoints, managing file uploads, or deploying Notion Workers. Triggers on "ntn", "notion cli", "notion api", "create notion page", "update notion page", "query notion database", "notion worker", "deploy worker".
model: sonnet
---

# Notion with `ntn` CLI

Official Notion CLI from Notion. Prefer it over a Notion MCP server for scripted/bulk ops, raw API calls and Workers deployment.

## Prerequisites

Requires the `ntn` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **ntn-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/ntn-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/ntn-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/ntn-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/ntn-cli.md` — edit anytime to customize."
2. Read it. When `default_parent` is set, use it as `--parent` for `ntn pages create` when the user names no parent. Use the ids in `known_data_sources` to resolve names like "the tasks database". Empty fields mean "ask the user".

## Auth & Setup

Two ways to authenticate:

- **Integration token (recommended for agents):** create an internal integration at `notion.so/profile/integrations` (or `notion.so/developers/connections`), then export its secret as `NOTION_API_TOKEN`, ideally from a `chmod 600` file such as `~/.notion.env` that your shell sources. The token bypasses `ntn login`. The integration only sees pages it has been connected to (page menu → Connections).
- **`ntn login`** (OAuth in a browser; `ntn login --no-browser` for headless/SSH sessions). Some workspaces block this via governance settings; fall back to an integration token.

**Workers caveat:** `ntn workers *` commands require a full `ntn login` session; `NOTION_API_TOKEN` alone is not enough.

Verify auth: `ntn whoami` or `ntn api v1/users | head -c 200`.

## Quick Reference

| Task | Command |
|------|---------|
| List API endpoints | `ntn api ls` |
| Endpoint spec / docs | `ntn api v1/pages --spec` / `--docs` |
| List users | `ntn api v1/users` |
| Search workspace content | `ntn api v1/search -d '{"query":"foo"}'` |
| Get page as Markdown | `ntn pages get <page-id>` |
| Get page raw JSON | `ntn pages get <page-id> --json` |
| Create page from file | `ntn pages create --parent page:<parent-id> < page.md` |
| Update page | `ntn pages update <page-id> --content '# New body'` |
| Trash page | `ntn pages trash <page-id>` |
| Query a data source | `ntn datasources query <data-source-id> --limit 50 --json` |
| Resolve DB ID → data source IDs | `ntn datasources resolve <database-id>` |
| Upload file from stdin | `ntn files create < photo.png` |
| Upload from URL | `ntn files create --external-url https://...` |
| List file uploads | `ntn files list` |
| Health check | `ntn doctor` |
| Show authenticated user | `ntn whoami` |

## Read vs Write Operations

**Read (the bundled permission hook allows these):**
- `ntn api ls`, `ntn api <path> --spec/--docs/--help`
- `ntn api <path>` with default GET: no `-d`, no `-X POST/PATCH/DELETE/PUT`, no inline body fields (`key=value`)
- `ntn api v1/search` and `ntn api v1/databases/<id>/query` (POST-but-read endpoints)
- `ntn datasources query/resolve`, `ntn files get/list`, `ntn pages get`
- `ntn workers list/ls/get/capabilities/usage`
- `ntn doctor`, `ntn completions`, `ntn whoami`, `ntn --help`, `ntn --version`

**Write (the hook prompts):**
- `ntn api` with `-X POST/PATCH/DELETE/PUT`, `-d/--data`, `--file`, or inline body fields
- `ntn files create`, `ntn pages create/update/trash`
- `ntn workers create/delete/rm/deploy/new/env/exec/oauth/sync/webhooks/tui`
- `ntn logout`, `ntn update`
- `ntn auth token` — not a mutation, but prints the live token in plaintext, so it is gated like a secret exposure
- `ntn notion-as-code *` (alpha) — `new`/`apply` mutate the workspace, `state rm` deletes saved state

## Subcommand Reference

### `ntn api` — raw Notion API
Default method is GET. Inline syntax:

| Syntax | Meaning |
|--------|---------|
| `key=value` | String body field (switches method to POST) |
| `key:=value` | Typed JSON body field (boolean, number, array, object) |
| `key==value` | Query parameter |
| `Header:value` | Custom request header |
| `-d '{...}'` | Raw JSON body |
| `-X METHOD` | Override HTTP method |
| `--spec` | OpenAPI fragment for the endpoint (no API call) |
| `--docs` | Full Notion API docs for the endpoint |
| `--file <path>` | Multipart upload field |

```bash
ntn api v1/pages/<id>                                # GET page
ntn api v1/pages -d '{"parent":{"page_id":"<id>"},"properties":{"title":[{"text":{"content":"hi"}}]}}'  # POST
ntn api v1/pages/<id> -X PATCH archived:=true        # PATCH typed
ntn api v1/databases/<id>/query page_size==10        # query param
```

Output is raw Notion API JSON; pipe to `jq` for shaping.

### `ntn pages` — Markdown read/write
Optimized for round-tripping page content as Markdown. For property updates or templates, drop down to `ntn api v1/pages`.

```bash
ntn pages get <page-id>                              # Markdown + frontmatter (page properties)
ntn pages get <page-id> --json                       # raw JSON (use if Markdown is truncated → unknown_block_ids)
ntn pages create --parent data-source:<id> < page.md
ntn pages update <page-id> --content '# Body'
```

Parent forms: `page:<id>`, `database:<id>`, `data-source:<id>`.

### `ntn datasources` — query Notion databases
A database can hold multiple data sources. `query` needs a data-source ID, NOT a database ID; resolve first.

```bash
ntn datasources resolve <database-id>
ntn datasources query <data-source-id> --limit 50 --json
ntn datasources query <id> --filter '{"property":"Done","checkbox":{"equals":true}}'
ntn datasources query <id> --start-cursor <cursor>
```

### `ntn files` — file uploads
```bash
ntn files create < /path/to/file.png
ntn files create --filename photo.png --content-type image/png < blob
ntn files create --external-url https://example.com/img.png
ntn files get <upload-id>
ntn files list                                       # first page only
```

Use the returned `id` as a file reference when creating/updating pages via `ntn api`.

### `ntn workers` — Notion Workers (beta)
Requires an `ntn login` session and a plan that allows Workers.

```bash
ntn workers new <name>        # scaffold a TS project
ntn workers deploy            # build + push from CWD
ntn workers list | get <id> | capabilities <id> | usage
ntn workers exec <capability> [args]
ntn workers env list/set/unset
ntn workers runs list/get
ntn workers delete <id>
```

### `ntn doctor`, `ntn whoami`, `ntn auth`
`ntn doctor` reports keychain vs file auth, config dir and version status; run it first when auth feels off. `ntn whoami [--json|--plain]` shows the authenticated user. `ntn auth token` prints the active token; only use it to confirm which token is live, never paste its output anywhere.

### `ntn notion-as-code` (alpha)
Marked alpha and "not publicly available" in `--help`. Don't reach for it unless the user asks about Notion-as-Code specifically.

## Behavioral Rules

- **Pages format:** prefer `ntn pages get/update` (Markdown) for body edits; use `ntn api` for property mutations.
- **Confirm before writes:** state the target page/data source and the change in chat before any `pages create/update/trash`, `api` mutation or worker op (the hook also prompts).
- If OAuth login is blocked in the workspace, don't keep retrying `ntn login`; rotate or recreate the integration token instead.

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `ntn pages get` returns truncated Markdown | Re-run with `--json`, inspect `unknown_block_ids`; fall back to `ntn api v1/blocks/<id>/children` |
| `ntn datasources query <db-id>` fails | DB ID ≠ data-source ID. Run `ntn datasources resolve <db-id>` first |
| Workers deploy fails 403 | Workspace doesn't allow Workers, or you're on `NOTION_API_TOKEN` instead of `ntn login` |
| Permission denied on page | The integration isn't connected to that page. Add it via the page menu → Connections |
| `--spec` returns nothing | Endpoint path is wrong. Check `ntn api ls` |

## Self-Update

```bash
ntn --version
brew upgrade --cask notion-cli   # or: ntn update (for non-brew installs)
```

After upgrading, run `/cortex:update-cli ntn` to capture new commands or flags.
