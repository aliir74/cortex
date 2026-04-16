---
name: bird-cli
description: Use when interacting with Twitter/X - reading tweets, searching, checking timelines, bookmarks, mentions, posting tweets, or replying. Triggers on tweet URLs, "check twitter", "read tweet", "search twitter", "my timeline", "twitter bookmarks", "post tweet", "reply to tweet", or any X/Twitter operation.
model: sonnet
---

# Twitter/X with bird CLI

## Prerequisites

Requires the `bird` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **bird-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/bird-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/bird-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/bird-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/bird-cli.md` — edit anytime to customize."
2. Read it. Use `default_account` when bird is configured for multi-account and the user does not specify which account to act as. Use `default_list` when listing/timelining without an explicit list ID. Read each path under `context_files` for additional context (e.g., a notes file about people the user follows).

## Auth Setup

bird reads X cookies/tokens. If a shell alias for `bird` is not available in your Bash sessions, use the binary path returned by `which bird` (commonly `~/.bun/bin/bird` on Bun installs).

Verify auth: `bird whoami`

### Multi-Account (optional)

bird supports multiple accounts via `~/.config/bird/accounts.json`. Switch with:

```bash
bird account use <account-name>
bird account list
bird account current
```

When the user has multiple accounts configured, default to the account named in `default_account` from preferences. Switch only when the user explicitly names another account.

If bird is configured to require explicit credentials (`cookieSource: []` in `~/.config/bird/config.json5`), pass them on the command line:

```bash
bird <command> --ct0 "$CT0" --auth-token "$AUTH"
```

Source `CT0` and `AUTH` from your account file or environment — the exact mechanism is user-specific. The skill assumes default auth flow unless the user mentions custom credential handling.

## Quick Reference

| Task | Command |
|------|---------|
| Read a tweet | `bird read <id-or-url>` or `bird <id-or-url>` |
| Read thread | `bird thread <id-or-url> [--all]` |
| Replies to tweet | `bird replies <id-or-url> -n 20` |
| Search | `bird search "query" -n 10` |
| Home timeline | `bird home -n 10 [--following]` |
| Bookmarks | `bird bookmarks -n 20 [--all]` |
| Mentions | `bird mentions -n 10` |
| User's tweets | `bird user-tweets @handle -n 10` |
| Likes | `bird likes -n 10` |
| User info | `bird about @handle` |
| Trending/news | `bird news [--ai-only]` |
| Lists | `bird lists` |
| List timeline | `bird list-timeline <list-id>` |
| Followers | `bird followers -n 20` |
| Following | `bird following -n 20` |
| **Post tweet** | `bird tweet "text"` |
| **Reply** | `bird reply <id-or-url> "text"` |
| **Attach media** | `bird tweet "text" --media photo.jpg --alt "description"` |
| Unfollow | `bird unfollow @handle` |
| Unbookmark | `bird unbookmark <id-or-url>` |

## Read vs Write Operations

**Read (safe, no confirmation needed):** read, replies, thread, search, mentions, bookmarks, likes, home, user-tweets, about, news, lists, list-timeline, followers, following, whoami, check

**Write (require user permission prompt):** tweet, reply, follow, unfollow, unbookmark

## Output Flags

- `--json` — structured JSON (use when parsing results programmatically)
- `--json-full` — JSON with raw API response in `_raw` field
- `--plain` — no emoji, no color (stable for scripting)
- `--no-emoji` / `--no-color` — individual control

**Always use `--json` when parsing results.** Use `--plain` for human-readable CLI output piped to other tools.

## Pagination

Most list commands support pagination:

```bash
bird bookmarks --all                    # Fetch everything
bird search "query" --max-pages 3       # Limit pages
bird bookmarks --cursor "abc123..."     # Resume from cursor
```

Flags: `--all` (fetch all), `--max-pages N` (limit), `--cursor` (resume)

## Search Syntax

bird search uses Twitter's search operators:

```bash
bird search "from:elonmusk AI"          # Tweets from specific user
bird search "@anthropic"                # Mentions of user
bird search "claude lang:en"            # Language filter
bird search "AI since:2026-03-01"       # Date filter
bird search "kubernetes -docker"        # Exclude term
```

## Bookmarks (Advanced)

```bash
bird bookmarks -n 50 --json                    # Basic fetch
bird bookmarks --all --sort-chronological      # All, sorted
bird bookmarks --folder-id <id>                # Specific folder
bird bookmarks --author-chain                  # Author self-reply chains
bird bookmarks --full-chain-only               # Full reply chains
bird bookmarks --include-parent                # Include parent tweet
bird bookmarks --thread-meta                   # Add thread metadata
```

## Home Timeline

```bash
bird home -n 20                    # "For You" algorithm feed
bird home -n 20 --following        # Chronological following feed
```

## News/Trending

```bash
bird news                          # All explore tabs
bird news --ai-only                # AI-curated news only
bird news --for-you                # For You tab
bird news --news-only              # News tab
bird news --sports                 # Sports tab
bird news --with-tweets            # Include related tweets
```

## Media Attachments (Write)

```bash
bird tweet "Check this out" --media photo.jpg
bird tweet "Photos" --media a.jpg --media b.jpg --alt "First" --alt "Second"
# Up to 4 images or 1 video
```

## Common Patterns

### Read a tweet from a URL
```bash
bird read https://x.com/user/status/1234567890
# or shorthand:
bird https://x.com/user/status/1234567890
```

### Get full context of a conversation
```bash
bird thread <tweet-id> --all --json
```

### Research what someone has been posting
```bash
bird user-tweets @handle -n 20 --json
```

### Check engagement on own tweets
```bash
bird mentions -n 20 --json
bird likes -n 10 --json
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `command not found: bird` | Use the full path returned by `which bird`, or re-source your shell init |
| Auth fails / 401 | Cookies expired — refresh via your usual auth flow (browser cookie sync or re-login) |
| GraphQL 404 | Run `bird query-ids --fresh` to refresh cached query IDs |
| Rate limited | Wait 15 min. Limit: ~1000 requests per 15-minute window |

## Config

- Config file: `~/.config/bird/config.json5` (optional, zero-config by default)
- Multi-account file: `~/.config/bird/accounts.json` (when configured)
- Env vars: `NO_COLOR`, `BIRD_TIMEOUT_MS`, `BIRD_COOKIE_TIMEOUT_MS`, `BIRD_QUOTE_DEPTH`
