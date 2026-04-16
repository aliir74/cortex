---
name: tgcli
description: Use when interacting with Telegram - reading chats, sending messages, searching, contacts, groups, media, or any Telegram operation. Triggers on "check telegram", "read telegram", "send telegram", "search telegram", "telegram messages", "telegram group", or any Telegram interaction.
model: sonnet
---

# Telegram with tgcli CLI

## Prerequisites

Requires the `tgcli` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **tgcli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/tgcli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/tgcli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/tgcli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/tgcli.md` — edit anytime to customize."
2. Read it. Use `default_chat_id` whenever the user says "send to my default chat" or doesn't specify a `--to` target. Use `default_channel` for read commands when the user says "check my main channel" or similar without naming one. Read each path under `context_files` for additional context (e.g., a tone reference, a contacts cheat sheet). Empty fields mean "ask the user."

## Auth Setup

tgcli uses MTProto user-account auth (phone + API credentials from https://my.telegram.org/apps).

Verify setup: `tgcli doctor`

**Config:** `~/Library/Application Support/tgcli/` (macOS) or platform-equivalent.

## Quick Reference

| Task | Command |
|------|---------|
| List chats/channels | `tgcli channels list --json` |
| Search channels | `tgcli channels list --query "name" --json` |
| Show channel info | `tgcli channels show --chat <id> --json` |
| Read messages | `tgcli messages list --chat <id> --json` |
| Show single message | `tgcli messages show --chat <id> --id <msg_id> --json` |
| Message context | `tgcli messages context --chat <id> --id <msg_id> --json` |
| Search messages | `tgcli messages search --query "keyword" --json` |
| Search in chat | `tgcli messages search --query "keyword" --chat <id> --json` |
| Send text | `tgcli send text --to <id> --message "text"` |
| Send file | `tgcli send file --to <id> --file <path>` |
| Search contacts | `tgcli contacts search <query> --json` |
| List groups | `tgcli groups list --json` |
| Group info | `tgcli groups info --chat <id> --json` |
| Download media | `tgcli media download --chat <id> --id <msg_id>` |
| Sync/backfill | `tgcli sync` |
| Diagnostics | `tgcli doctor` |

## Read vs Write Operations

**Read (safe, no confirmation needed):** channels list, channels show, messages list, messages show, messages context, messages search, contacts search, contacts show, groups list, groups info, media download, doctor, sync

**Write (require user permission prompt):** send text, send file, groups rename, groups join, groups leave, groups members, groups invite

## Message Operations

### Reading Messages

```bash
# List messages from a chat (by ID or username)
tgcli messages list --chat <id> --json
tgcli messages list --chat @username --json

# Limit results
tgcli messages list --chat <id> --limit 20 --json

# Date filters
tgcli messages list --chat <id> --after 2026-03-01 --before 2026-03-09 --json

# Show a specific message
tgcli messages show --chat <id> --id <msg_id> --json

# Show messages around a specific message
tgcli messages context --chat <id> --id <msg_id> --before 5 --after 5 --json

# Source: archive, live, or both
tgcli messages list --chat <id> --source both --json
```

### Searching Messages

```bash
# Global search
tgcli messages search --query "keyword" --json

# Search within a chat
tgcli messages search --query "keyword" --chat <id> --json

# Regex search
tgcli messages search --regex "pattern" --chat <id> --json

# Date-filtered search
tgcli messages search --query "keyword" --after 2026-03-01 --before 2026-03-09 --json

# Tag-filtered search
tgcli messages search --tag "important" --json

# Forum topic search
tgcli messages search --query "keyword" --chat <id> --topic <topic_id> --json
```

### Sending Messages

If `context_files` in preferences point to a tone/style reference, read it before drafting.

```bash
# Send text (by ID or username)
tgcli send text --to <id> --message "Hello!"
tgcli send text --to @username --message "Hello!"

# Send to forum topic
tgcli send text --to <id> --message "text" --topic <topic_id>

# Send file
tgcli send file --to <id> --file /path/to/document.pdf

# Send file with caption
tgcli send file --to <id> --file photo.jpg --caption "Check this out"

# Override filename
tgcli send file --to <id> --file report.pdf --filename "Q1-Report.pdf"
```

**Note:** tgcli does not support `--reply-to` threading. Messages are sent as new messages only.

**Draft confirmation:** Always show the user the full message text and ask for confirmation before sending. Never send without explicit approval.

## Channel Operations

```bash
# List all channels
tgcli channels list --json

# Search by name/username
tgcli channels list --query "tech" --json

# Limit results
tgcli channels list --limit 10 --json

# Show channel details
tgcli channels show --chat <id> --json
tgcli channels show --chat @username --json

# Enable/disable sync for a channel
tgcli channels sync --chat <id> --enable
tgcli channels sync --chat <id> --disable
```

## Contact Operations

```bash
# Search contacts
tgcli contacts search "name" --json

# Limit results
tgcli contacts search "name" --limit 5 --json

# Show contact profile
tgcli contacts show --chat <id> --json
```

## Group Operations

```bash
# List groups
tgcli groups list --json

# Group info
tgcli groups info --chat <id> --json

# Rename group (write)
tgcli groups rename --chat <id> --name "New Name"

# Join via invite code (write)
tgcli groups join --code "abc123"

# Leave group (write)
tgcli groups leave --chat <id>
```

## Media

```bash
# Download media from a message
tgcli media download --chat <id> --id <msg_id>
```

## Chat Identifiers

The `--chat` / `--to` arguments accept:
- **Numeric ID:** `-1001234567890`
- **Username:** `@channelname`

## Understanding Message Threading (topicId)

The `topicId` field in message JSON indicates which message a reply belongs to. When analyzing conversations:

- **`topicId: null`** = top-level message, not a reply
- **`topicId: <messageId>`** = this message is a reply to message `<messageId>`

**Always check `topicId` to understand reply chains before summarizing conversations.** Messages with the same `topicId` form a thread. Without checking this, you'll misattribute who said what to whom. When a message has a `topicId`, look up that parent message to understand what the user is responding to.

## Output Format

Use `--json` flag on all read commands for structured output when parsing results.

## Timeouts

For long-running operations (sync, large message fetches):

```bash
tgcli sync --timeout 5m
tgcli messages list --chat <id> --limit 500 --timeout 2m --json
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `command not found: tgcli` | Install via the SETUP.md instructions for **tgcli** |
| Auth fails / session expired | Re-run `tgcli auth` with phone + API credentials |
| Archived groups not listed | Unarchive in Telegram app first, then `tgcli groups list` |
| Slow first run | `tgcli sync` to backfill message archive |
| Timeout on large fetch | Add `--timeout 5m` to command |

## Config

- Config/data: `~/Library/Application Support/tgcli/` (or platform equivalent)
- Built-in MCP server available (`tgcli server`) but optional
