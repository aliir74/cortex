---
name: exa-cli
description: Runs Exa AI neural/semantic web search, grounded cited answers, or clean content extraction for known URLs. Use for 'exa search', 'neural search', 'semantic search', 'exa answer', or research that needs many high-quality sources. Not for single-fact or syntax lookups (use plain web search).
---

# Exa CLI

Thin wrapper over the Exa AI search API (`exa-py` loaded ephemerally via `uv`), exposing three subcommands. It ships inside this skill:

```bash
EXA="${CLAUDE_PLUGIN_ROOT}/skills/exa-cli/exa"
"$EXA" search "query" --num 5
```

Every `exa ...` example below means `"${CLAUDE_PLUGIN_ROOT}/skills/exa-cli/exa" ...`.

## Prerequisites

Requires `uv` and an Exa API key. If either is missing, point the user to `SETUP.md` at the plugin root (section: **exa-cli**) and stop until it's available.

## Auth

The wrapper reads `EXA_API_KEY` from the environment and, when it is unset, self-sources `~/.exa.env` (a `chmod 600` file containing `export EXA_API_KEY="..."`). That way sub-agents inherit the key without a shell restart. Never put the key inline on a command line or commit it.

## Subcommands

### `exa search <query>` — find pages
Neural + keyword search. Default `--type auto`, `--content highlights` (token-efficient).

```bash
exa search "vercel edge middleware streaming" --num 5 --json
exa search "companies hiring senior backend engineers in Berlin" --deep --content text --text-max 8000
exa search "gpu makers" --schema schema.json --system-prompt "Prefer official sources; dedupe."
```

Flags: `--type {auto,fast,instant,deep-lite,deep,deep-reasoning}` (default `auto`), `--deep` (= `--type deep`), `--num N`, `--content {highlights,text,summary}`, `--text-max N`, `--include-domains …`, `--exclude-domains …`, `--max-age-hours N`, `--schema <file.json>`, `--system-prompt "…"`.

### `exa answer <question>` — grounded answer + citations

```bash
exa answer "current stable version of exa-py on pypi" --json
```

### `exa contents <url...>` — extract content for known URLs
For URLs already in hand (from search results, a feed, the user).

```bash
exa contents https://example.com/article --content text --text-max 8000 --json
```

Flags: `--content {highlights,text}`, `--text-max N`, `--max-age-hours N`.

`--human` on any subcommand prints a compact summary instead of JSON.

## Search-type reference

| Type | Best for | Latency |
|------|----------|---------|
| `auto` (default) | most queries, balanced | ~1s |
| `fast` | latency-sensitive, still good relevance | ~450ms |
| `instant` | quick lookups | ~250ms |
| `deep-lite` | cheaper synthesis | ~4s |
| `deep` | research, enrichment, thorough results | 4–15s |
| `deep-reasoning` | hard multi-step synthesis | 12–40s |

## Content nesting rule

- **`/search`** → contents params NEST under `contents`: `{"contents": {"highlights": true}}`.
- **`/contents`** → params are TOP-LEVEL: `{"highlights": true}`.

The CLI handles this per subcommand; it only matters if you hand-craft raw API JSON.

## Deprecated params — never emit

`useAutoprompt` (does nothing), `livecrawl:"always"` (use `--max-age-hours 0`), `numSentences` / `highlightsPerUrl` (use `highlights`), `tokensNum` (use `--text-max`), `includeUrls` / `excludeUrls` (use `--include-domains` / `--exclude-domains`). Also: `--exclude-domains` combined with a company/people category returns 400.

## Cost — Exa is metered

Searches and content pages are billed per request (check current pricing on the Exa dashboard). So:
- Prefer `--type auto` + `highlights` (the defaults) for most work.
- Reserve `deep` / `deep-reasoning` for genuinely hard synthesis.
- Keep single-fact, doc-page and syntax lookups on the built-in web search; Exa's neural search buys nothing there.
