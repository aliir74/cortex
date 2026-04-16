---
name: fetch-raindrop-bookmarks
description: Use when user wants to fetch bookmarks from Raindrop.io and review them, or when user says "fetch raindrop", "import raindrop bookmarks", "sync raindrop", "list raindrop bookmarks".
---

# Fetch Raindrop.io Bookmarks

Fetches bookmarks from a Raindrop.io collection via the public API, presents them for triage, and (optionally) saves selections to disk as markdown.

This skill stands alone: it does not depend on any vault layout, "curate", or "read-later" workflow. If you have a personal note-taking system, decide where to move the saved files yourself after the skill finishes.

## Prerequisites

- A Raindrop.io API token. If missing, point the user to `SETUP.md` at the plugin root (section: **fetch-raindrop-bookmarks**) and stop.
- `curl` (preinstalled on macOS/Linux) and Python 3 (used to parse the JSON response).

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/fetch-raindrop-bookmarks.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/fetch-raindrop-bookmarks/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/fetch-raindrop-bookmarks.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/fetch-raindrop-bookmarks.md` — fill it in (at minimum, set `collection_id` and either `raindrop_api_token` or the `RAINDROP_API_TOKEN` env var) and re-run."
2. Read it. Resolve values in this order:
   - **token**: `RAINDROP_API_TOKEN` env var, else `raindrop_api_token` from preferences. If both are empty, stop and tell the user to set one.
   - **collection_id**: `collection_id` from preferences, else `0` (Unsorted).
   - **output_dir**: `output_dir` from preferences, else `${CLAUDE_PLUGIN_DATA}/raindrop-bookmarks/`. Create it with `mkdir -p` before saving.
   - **delete_after_save**: `delete_after_save` from preferences, else `false`.

## State File

Track which bookmark IDs have already been shown to the user so reruns don't re-list them:

```
${CLAUDE_PLUGIN_DATA}/raindrop-bookmarks/.seen.json
```

Format: `{"seen": [12345, 67890, ...]}`. Create it on first run if missing. Add IDs after every action (save, skip, delete).

## Steps

### 1. Fetch bookmarks

Use the Raindrop REST API. Page through results until exhausted or you have enough new (unseen) items:

```bash
curl -sS \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.raindrop.io/rest/v1/raindrops/$COLLECTION_ID?perpage=50&page=0"
```

The response shape:
```json
{
  "result": true,
  "items": [
    {"_id": 123, "title": "...", "link": "https://...", "excerpt": "...", "tags": ["tag1"]}
  ],
  "count": 42
}
```

Filter out IDs already in `.seen.json`. If the filtered list is empty, tell the user "No new bookmarks to process." and stop.

### 2. Present bookmarks

Show all new bookmarks in a numbered list:

```
**1/N: Title Here**
URL: https://example.com/...
Excerpt: First ~150 chars of excerpt...
Tags: tag1, tag2
```

Then ask once:

```
For each, choose: **save** | **skip** | **open**
(e.g. "save 1 3, skip 2, open 4" or "save all", "skip all")
```

- **save** — Write a markdown file to `$OUTPUT_DIR` and mark seen.
- **skip** — Mark seen, take no further action.
- **open** — Use WebFetch to fetch the URL and show a brief preview, then re-prompt for that item.

If `delete_after_save` is true, also delete the bookmark from Raindrop (see step 4).

### 3. Save selected bookmarks

For each "save" item, write a markdown file at `$OUTPUT_DIR/<slug>-<id>.md` with simple frontmatter:

```markdown
---
title: <title>
url: <link>
date: <YYYY-MM-DD>
tags: [tag1, tag2]
raindrop_id: <id>
---

<excerpt>
```

Use a slug derived from the title (lowercase, hyphenated, ASCII-safe, max 60 chars). If the title is empty, use the domain.

Optionally, when the user explicitly asks for full content, use WebFetch to grab the article body and append it under a `## Content` heading.

### 4. Delete from Raindrop (only if `delete_after_save=true`)

```bash
curl -sS -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.raindrop.io/rest/v1/raindrop/$ID"
```

Check the response (`{"result": true}`). If deletion fails, keep the file but warn the user — the next run will re-list it unless it's added to `.seen.json`.

### 5. Update state

Append every processed ID (saved, skipped, opened-then-decided) to `.seen.json`. Write the file atomically (write to `.seen.json.tmp` then `mv`).

### 6. Report results

Summarize:
- How many saved (with absolute file paths)
- How many skipped
- How many deleted from Raindrop (if applicable)
- Any API errors

## API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/rest/v1/raindrops/<collection_id>` | GET | List bookmarks (supports `?perpage=`, `?page=`, `?search=`) |
| `/rest/v1/raindrop/<id>` | GET | Get a single bookmark |
| `/rest/v1/raindrop/<id>` | DELETE | Delete a bookmark |
| `/rest/v1/collections` | GET | List your collections (use to discover IDs) |

All endpoints require `Authorization: Bearer <token>`.

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Missing/invalid token | Tell user to refresh `RAINDROP_API_TOKEN` (link to `https://app.raindrop.io/settings/integrations`) |
| 403 | Token lacks scope or collection not yours | Verify the token owner matches the collection owner |
| 404 | Collection ID not found | Run `GET /rest/v1/collections` and tell the user their available IDs |
| 429 | Rate-limited | Back off (sleep 5s) and retry once |

## Notes

- The skill never deletes bookmarks unless `delete_after_save=true` is explicitly set.
- The "seen" state is local to this machine. Re-listing on a fresh machine will surface every bookmark again until they're seen or deleted.
- For "Unsorted" use `collection_id: 0`. For "All" use `-1`. For "Trash" use `-99`.
