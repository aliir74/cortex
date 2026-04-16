---
name: gws-cli
description: Use when interacting with Google Workspace - Gmail, Calendar, Drive, Sheets, Docs, email, events, meetings, schedule, or any gws CLI operation. Triggers on "check email", "read gmail", "send email", "calendar", "agenda", "schedule meeting", "drive", "sheets", "google workspace", or any gws interaction.
model: sonnet
---

# Google Workspace with gws CLI

## Auth & Account Setup

gws uses OAuth2 credentials stored per-account. Multiple accounts can be registered simultaneously.

**Account switching:** Prefix any command with the env var for a non-default account:

```bash
GOOGLE_WORKSPACE_CLI_ACCOUNT=other@example.com gws gmail +triage
```

Verify auth: `gws auth status`
List accounts: `gws auth list`

**Config:** `~/.config/gws/`

## Quick Reference

| Task | Command |
|------|---------|
| Inbox summary | `gws gmail +triage` |
| Send email | `gws gmail +send --to EMAIL --subject "..." --body "..."` |
| Read message | `gws gmail users messages get --params '{"userId":"me","id":"MSG_ID"}'` |
| Search email | `gws gmail +triage --query "from:someone"` |
| Archive email | `gws gmail users messages batchModify --params '{"userId":"me"}' --json '{"ids":["ID"],"removeLabelIds":["INBOX"]}'` |
| Today's agenda | `gws calendar +agenda --today` |
| Week agenda | `gws calendar +agenda --week` |
| Create event | `gws calendar +insert --summary "..." --start ISO --end ISO` |
| Upload file | `gws drive +upload ./file.pdf` |
| Read sheet | `gws sheets +read --spreadsheet ID --range "Sheet1!A1:D10"` |
| Append to sheet | `gws sheets +append --spreadsheet ID --values "a,b,c"` |
| Check account | `gws gmail users getProfile --params '{"userId":"me"}'` |
| Schema inspect | `gws schema gmail.users.messages.list` |

## Read vs Write Operations

**Read (safe, no confirmation needed):** +triage, +agenda, +read, users messages list, users messages get, users threads list, users getProfile, events list, files list, files get, spreadsheets get, values get, auth status, auth list, schema

**Write (require user permission prompt):** +send, +insert, +upload, +append, users messages send, users messages modify, users messages batchModify, users messages trash, users messages delete, users drafts create, users drafts send, events insert, events update, events delete, files create, files update, files delete, permissions create, values update

## Gmail

### Helpers

```bash
# Inbox triage — read-only unread summary (table format by default)
gws gmail +triage
gws gmail +triage --max 5
gws gmail +triage --query "from:boss"
gws gmail +triage --labels        # include label names
gws gmail +triage --format json   # for parsing

# Send email — handles RFC 2822 encoding automatically
gws gmail +send --to alice@example.com --subject "Hello" --body "Hi Alice!"
```

**For HTML bodies, attachments, or CC/BCC**, use the raw API:

```bash
gws gmail users messages send --json '{"raw":"BASE64_RFC2822"}'
```

### Messages

```bash
# List messages (default: inbox)
gws gmail users messages list --params '{"userId":"me","maxResults":10}'

# Search with Gmail query operators
gws gmail users messages list --params '{"userId":"me","q":"from:hr@company.com after:2026/03/01"}'

# Read a specific message
gws gmail users messages get --params '{"userId":"me","id":"MSG_ID"}'

# Modify labels (archive = remove INBOX)
gws gmail users messages batchModify --params '{"userId":"me"}' --json '{"ids":["ID1","ID2"],"removeLabelIds":["INBOX","UNREAD"]}'

# Trash a message
gws gmail users messages trash --params '{"userId":"me","id":"MSG_ID"}'
```

### Gmail Search Operators

Use in the `q` parameter or `+triage --query`:
- `from:`, `to:`, `cc:`, `bcc:` — sender/recipients
- `subject:` — subject line
- `after:YYYY/MM/DD`, `before:YYYY/MM/DD` — date range
- `is:unread`, `is:starred`, `is:important`
- `has:attachment`, `filename:pdf`
- `label:` — filter by label
- `in:inbox`, `in:sent`, `in:trash`, `in:drafts`
- Combine with AND/OR: `from:alice OR from:bob`

### Threads

```bash
# List threads
gws gmail users threads list --params '{"userId":"me","maxResults":10}'

# Get full thread (all messages)
gws gmail users threads get --params '{"userId":"me","id":"THREAD_ID"}'
```

### Drafts

```bash
# List drafts
gws gmail users drafts list --params '{"userId":"me"}'

# Create draft
gws gmail users drafts create --params '{"userId":"me"}' --json '{"message":{"raw":"BASE64_RFC2822"}}'

# Send existing draft
gws gmail users drafts send --params '{"userId":"me"}' --json '{"id":"DRAFT_ID"}'
```

## Calendar

### Helpers

```bash
# Agenda — read-only, queries all calendars
gws calendar +agenda              # next 7 days
gws calendar +agenda --today
gws calendar +agenda --tomorrow
gws calendar +agenda --week
gws calendar +agenda --days 3
gws calendar +agenda --calendar "Work"    # filter to one calendar
gws calendar +agenda --format table

# Create event
gws calendar +insert --summary "Standup" --start "2026-03-11T09:00:00-07:00" --end "2026-03-11T09:30:00-07:00"
gws calendar +insert --summary "Review" --start ... --end ... --attendee alice@example.com
gws calendar +insert --summary "Lunch" --start ... --end ... --location "Downtown" --description "Team lunch"
```

**IMPORTANT: Attendee rule** — When creating events "with" someone, always add them via `--attendee EMAIL`. Always include the organizer themselves as an attendee too (organizer != attendee in Google Calendar). If the attendee's email is unknown, ask for it BEFORE creating the event. Use `--attendee` multiple times for multiple attendees.

**IMPORTANT: Account override rule** — The `+insert` helper ignores `GOOGLE_WORKSPACE_CLI_ACCOUNT` env var and always creates on the default account. When creating events on a non-default account, use the raw API instead: `GOOGLE_WORKSPACE_CLI_ACCOUNT=other@example.com gws calendar events insert --params '{"calendarId":"primary"}' --json '{...}'`

### Events (Raw API)

```bash
# List events
gws calendar events list --params '{"calendarId":"primary","maxResults":10,"timeMin":"2026-03-10T00:00:00Z","timeMax":"2026-03-17T23:59:59Z"}'

# Get single event
gws calendar events get --params '{"calendarId":"primary","eventId":"EVENT_ID"}'

# Update event
gws calendar events update --params '{"calendarId":"primary","eventId":"EVENT_ID"}' --json '{"summary":"Updated Title"}'

# Delete event
gws calendar events delete --params '{"calendarId":"primary","eventId":"EVENT_ID"}'
```

**IMPORTANT: Update replaces fields** — The `events update` API replaces the entire event resource. Always include ALL existing fields (`summary`, `start`, `end`, `attendees`, `location`, `description`) in the update payload, not just the fields you're changing. Omitted fields get wiped (e.g., missing `summary` causes "No Title").

**Date format:** Always use RFC 3339 with timezone offset (e.g., `2026-03-11T09:00:00-07:00`). Do not use bare dates.

### Freebusy

```bash
gws calendar freebusy query --json '{"timeMin":"2026-03-11T00:00:00Z","timeMax":"2026-03-11T23:59:59Z","items":[{"id":"primary"}]}'
```

## Drive

### Helper

```bash
# Upload file — MIME type auto-detected
gws drive +upload ./report.pdf
gws drive +upload ./report.pdf --parent FOLDER_ID
gws drive +upload ./data.csv --name "Sales Data.csv"
```

### Files (Raw API)

```bash
# List files
gws drive files list --params '{"pageSize":10}'

# Search files
gws drive files list --params '{"q":"name contains '\''report'\'' and mimeType='\''application/pdf'\''","pageSize":10}'

# Get file metadata
gws drive files get --params '{"fileId":"FILE_ID"}'

# Download/export file
gws drive files get --params '{"fileId":"FILE_ID","alt":"media"}' --output ./downloaded.pdf

# Export Google Doc as PDF
gws drive files export --params '{"fileId":"FILE_ID","mimeType":"application/pdf"}' --output ./doc.pdf

# Create folder
gws drive files create --json '{"name":"New Folder","mimeType":"application/vnd.google-apps.folder"}'
```

## Sheets

### Helpers

```bash
# Read values — read-only
gws sheets +read --spreadsheet SPREADSHEET_ID --range "Sheet1!A1:D10"
gws sheets +read --spreadsheet SPREADSHEET_ID --range Sheet1

# Append row (simple)
gws sheets +append --spreadsheet SPREADSHEET_ID --values "Alice,100,true"

# Append multiple rows (JSON)
gws sheets +append --spreadsheet SPREADSHEET_ID --json-values '[["Alice","100"],["Bob","200"]]'
```

### Raw API

```bash
# Get spreadsheet metadata
gws sheets spreadsheets get --params '{"spreadsheetId":"ID"}'

# Read values
gws sheets spreadsheets values get --params '{"spreadsheetId":"ID","range":"Sheet1!A1:D10"}'

# Update values
gws sheets spreadsheets values update --params '{"spreadsheetId":"ID","range":"Sheet1!A1","valueInputOption":"USER_ENTERED"}' --json '{"values":[["New Value"]]}'
```

## Global Flags

| Flag | Description |
|------|-------------|
| `--params '<JSON>'` | URL/query parameters (required for raw API calls). **Single-use only** — merge all query params into one JSON object. Never pass `--params` twice. |
| `--json '<JSON>'` | Request body for POST/PATCH/PUT |
| `--upload <PATH>` | Upload file as media content (multipart) |
| `--output <PATH>` | Save binary response to file |
| `--format <FMT>` | Output: `json` (default), `table`, `yaml`, `csv` |
| `--page-all` | Auto-paginate, one JSON line per page (NDJSON) |
| `--page-limit <N>` | Max pages with `--page-all` (default: 10) |
| `--page-delay <MS>` | Delay between pages in ms (default: 100) |
| `--dry-run` | Validate locally without sending to API |

## Common Patterns

### Multi-Account

```bash
# Default account
gws gmail +triage

# Non-default account
GOOGLE_WORKSPACE_CLI_ACCOUNT=other@example.com gws gmail +triage

# Verify which account is active
gws gmail users getProfile --params '{"userId":"me"}'
```

### Pagination

```bash
# Auto-paginate all pages (NDJSON output)
gws gmail users messages list --params '{"userId":"me"}' --page-all

# Limit pages
gws gmail users messages list --params '{"userId":"me"}' --page-all --page-limit 3
```

### Schema Inspection

When unsure about API parameters for a method:

```bash
gws schema gmail.users.messages.list
gws schema calendar.events.insert
gws schema drive.files.list
gws schema gmail.users.messages.list --resolve-refs   # expand $ref types
```

### Other Services

For less common services (Docs, Tasks, People, Chat, etc.):

```bash
gws <service> --help         # list resources and helpers
gws <service> <resource> --help   # list methods
gws schema <service.resource.method>   # inspect parameters
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Empty results from Gmail/Calendar | Verify account: `gws gmail users getProfile --params '{"userId":"me"}'` — may be querying wrong account |
| Auth fails / token expired | Re-authenticate: `gws auth login --account EMAIL` |
| Wrong account active | Set env var: `GOOGLE_WORKSPACE_CLI_ACCOUNT=email@domain.com` |
| Date format errors (Calendar) | Use RFC 3339 with timezone: `2026-03-11T09:00:00-07:00` |
| `--params` parse error | Ensure valid JSON with double quotes: `'{"key":"value"}'` |
| `--params` used twice | CLI rejects multiple `--params` flags. Merge all query params into one JSON object (e.g., `'{"calendarId":"primary","conferenceDataVersion":1}'`) |
| Binary file not downloading | Add `--output ./filename.ext` to the command |
| Need API method details | Inspect schema: `gws schema service.resource.method` |
| `+triage --query` misses some emails | `+triage` defaults to `is:unread`. The `--query` flag replaces that default, but the helper can still miss emails the raw API finds. For reliable search, use: `gws gmail users messages list --params '{"userId":"me","q":"..."}'` |

## Config

- Config/credentials: `~/.config/gws/`
- Accounts stored per-email, no switching needed
- Token cache managed automatically
