---
name: slack-cli
description: Use when interacting with Slack - reading messages, sending messages, searching, listing channels, user lookups, reactions, canvas reads, or any Slack operation. Triggers on "check slack", "read slack", "send message on slack", "search slack", "slack messages", "slack channel", or any Slack interaction.
model: sonnet
---

# Slack with agent-slack CLI

## Prerequisites

Requires the `agent-slack` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **slack-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/slack-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/slack-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/slack-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/slack-cli.md` — edit anytime to customize."
2. Read it. Use `default_workspace` whenever this doc shows a `--workspace` flag, `default_channel` when the user says "send to my default channel" or doesn't specify a target, append `signature` to outgoing messages when set, and read each path under `context_files` as additional context (e.g., a cached map of user IDs to display names). Empty fields mean "use the CLI's default" or "ask the user."

## Auth & Workspace Setup

agent-slack uses credentials imported from Slack Desktop. Verify auth: `agent-slack auth test`.

**Workspace flag:** When the user has multiple workspaces imported, always pass `--workspace "<substring>"` (use `default_workspace` from preferences when set) on **every** command (`message list`, `search`, `channel list`, etc.) to avoid "Ambiguous channel name" errors when channels overlap across workspaces.

**User identification:** Always look up user IDs via `agent-slack user get "@username"` before assuming who sent a message. Never guess the sender from context, channel name, or conversation topic.

**Attribution in drafts — common failure mode:** When drafting any response, document, or note that references a Slack message's sender by name, user ID lookup is **step 1, not step N**. Do NOT infer the sender from the topic, the channel, or seniority.

If `context_files` in preferences point to a cached map of user IDs to display names, read it first; only call `agent-slack user get` for IDs not already in the cache. After any successful new lookup, suggest updating the cache file so future sessions don't repeat the call.

## Quick Reference

| Task | Command |
|------|---------|
| Read channel messages | `agent-slack message list "#channel" --limit 10` |
| Read thread | `agent-slack message list "SLACK_URL" --limit 10` |
| Send message | `agent-slack message send "#channel" "text"` |
| Reply to thread | `agent-slack message send "#channel" "text" --thread-ts "1234567890.123456"` |
| Search messages | `agent-slack search messages "query" --limit 5` |
| Search in channel | `agent-slack search messages "query" --channel "#channel"` |
| List channels | `agent-slack channel list --limit 20` |
| Get user | `agent-slack user get "@username"` |
| List users | `agent-slack user list --limit 20` |
| Add reaction | `agent-slack message react add "URL" "emoji-name"` |
| Remove reaction | `agent-slack message react remove "URL" "emoji-name"` |
| Read canvas | `agent-slack canvas get <canvas-id>` |
| Auth check | `agent-slack auth test` |

## Read vs Write Operations

**Read (safe, no confirmation needed):** message list, message get, search messages, search files, search all, channel list, user list, user get, canvas get, auth test, auth whoami

**Write (require user permission prompt):** message send, message edit, message delete, message react add, message react remove, channel new, channel invite

## Message Operations

### Reading Messages

```bash
# Channel history (default 25 messages, max 200)
agent-slack message list "#general" --limit 10

# Read a specific thread by URL
agent-slack message list "https://workspace.slack.com/archives/C123/p456"

# Read thread by channel + thread timestamp
agent-slack message list "#channel" --thread-ts "1234567890.123456"

# Get a single message (with thread summary if any)
agent-slack message get "https://workspace.slack.com/archives/C123/p456"

# Filter by reaction
agent-slack message list "#channel" --oldest "1700000000.000000" --with-reaction "eyes"
agent-slack message list "#channel" --oldest "1700000000.000000" --without-reaction "white_check_mark"

# Control content length
agent-slack message list "#channel" --max-body-chars 2000
agent-slack message list "#channel" --max-body-chars -1  # unlimited

# Include reactions and reacting users
agent-slack message list "#channel" --include-reactions
```

### @Mentions in Messages

**CRITICAL:** Plain text `@Name` does NOT create clickable mentions in Slack API. You MUST use `<@USER_ID>` format.

1. Look up the user ID with `agent-slack user get "@username"` (or read it from a cached map listed in `context_files`).
2. Use `<@USER_ID>` in the message text: `"Hey <@U09CW4AUXSP>, great work!"`

### Behavioral Rules

- **Language matching**: Match reply language to the conversation language, not the participant's nationality. If the thread is in English, reply in English. If in another language or transliteration, reply in the appropriate native script — never transliterated.
- **Tone accuracy**: When sending messages on behalf of the user, accurately reflect what they did (e.g., "found and fixed an issue") — don't just state the outcome.
- **Draft confirmation**: Always show the user the full message text and ask for confirmation before sending any Slack message. Never send without explicit approval, even when the user asked you to send it.

### Sending Messages

**Always include `--workspace "<substring>"`** (from preferences) to avoid ambiguity errors when channel names overlap across workspaces.

**Emojis:** Slack shortcodes (`:thumbsup:`, `:bar_chart:`, `:one:`) are NOT parsed by the API and render as plain text. Always use Unicode emojis (👍, 📊, 1️⃣) in message text. Shortcodes only work for reactions (`message react add`).

**Lists:** Slack does not render markdown numbered lists (`1.`, `2.`) correctly via the API — they all show as `1.`. Use Unicode bullets (`•`) for lists instead.

**Links:** Slack's `<url|text>` mrkdwn format does NOT reliably render as clickable links via the API. Instead, put URLs on their own line — Slack will auto-detect and unfurl them.

**Channel IDs vs names:** When using a channel ID (e.g., `C0AH6NYSNBZ`), pass it bare — do NOT prefix with `#`. The `#` prefix only works with channel names like `#general`. Using `#C0AH6NYSNBZ` will fail with "Could not resolve channel name."

**Broadcast replies (thread + channel):** Not supported in current agent-slack. There is no `--reply-broadcast` flag. To post in both thread and channel, send two separate messages or send a channel-only message.

```bash
# Send to channel
agent-slack message send "#general" "Hello team!" --workspace "<substring>"

# Reply to thread
agent-slack message send "#general" "Noted, thanks!" --thread-ts "1234567890.123456"

# Send with file attachment
agent-slack message send "#channel" "Here's the report" --attach report.pdf

# Multiple attachments
agent-slack message send "#channel" "Screenshots" --attach shot1.png --attach shot2.png
```

### Editing & Deleting

```bash
# Edit a message (target is the message URL or channel+ts)
agent-slack message edit "SLACK_URL" "Updated text"

# Delete a message
agent-slack message delete "SLACK_URL"
```

### Reactions

```bash
agent-slack message react add "SLACK_URL" "thumbsup"
agent-slack message react remove "SLACK_URL" "thumbsup"
```

## Channel Operations

```bash
# List your channels (default workspace)
agent-slack channel list --limit 20

# List all workspace channels
agent-slack channel list --all

# List channels for a specific user
agent-slack channel list --user "@username"

# Paginate
agent-slack channel list --cursor "next_page_cursor"

# Create a new channel
agent-slack channel new --name "project-alpha"

# Invite users to a channel
agent-slack channel invite --channel "#project-alpha" --user "@username"
```

## Search

```bash
# Search messages
agent-slack search messages "deployment issue" --limit 10

# Search in specific channel
agent-slack search messages "bug report" --channel "#engineering"

# Search by user
agent-slack search messages "review" --user "@username"

# Date filters
agent-slack search messages "migration" --after 2026-03-01 --before 2026-03-09

# Content type filter
agent-slack search messages "screenshot" --content-type image

# Search files
agent-slack search files "architecture diagram"

# Search everything (messages + files)
agent-slack search all "quarterly report"

# Control content length in results
agent-slack search messages "query" --max-content-chars 2000
```

## User Operations

```bash
# List workspace users
agent-slack user list --limit 20

# Get user by handle or ID
agent-slack user get "@username"
agent-slack user get "U0123456789"
```

## Canvas

```bash
# Fetch canvas as markdown
agent-slack canvas get <canvas-id-or-url>
```

## Target Formats

The `<target>` argument accepts:
- **Slack URL:** `https://<workspace>.slack.com/archives/C123ABC/p1234567890123456`
- **Channel name:** `#general` or `general`
- **Channel ID:** `C0123456789` (bare ID only — do NOT prefix with `#`, it will fail to resolve)

For thread replies, use `--thread-ts` with the root message timestamp.

## Workspace Selection

When operating across workspaces, use `--workspace`:

```bash
# Full URL
agent-slack message list "#general" --workspace "workspace.slack.com"

# Substring match
agent-slack message list "#general" --workspace "workspace"
```

Use `default_workspace` from preferences as the default. Override only when the user explicitly targets a different workspace.

## Output Format

All output is **token-efficient JSON** by default (null/empty fields pruned). No `--json` flag needed.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `command not found: agent-slack` | Verify the install (see SETUP.md). On Bun installs, ensure `BUN_INSTALL` and `PATH` are set. |
| Auth fails / token expired | Re-import from Slack Desktop: `agent-slack auth import-desktop` |
| Wrong workspace | Add `--workspace "<substring>"` to target the correct workspace |
| Archived channels not found | Unarchive in Slack app first, then `agent-slack channel list` |

## Task Creation from Slack

When creating tasks from Slack conversations, focus on the user's own pending action items, not what was already done or what others need to do. Always include the source Slack message URL as a `[link]` in the task.

## Follow-up Behavior

When following up on Slack with additional questions for the same person, **edit the previous message** instead of sending a new one. Avoid spamming people with multiple separate messages when they haven't replied yet.
