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
   - **curate_dir**: `curate_dir` from preferences, else unset. When set, the triage step offers a 4th "curate" option and writes curated items here (created with `mkdir -p` on demand).
   - **curate_auto_why**: `curate_auto_why` from preferences, else `false`. Only consulted when `curate_dir` is set.
   - **extract_full_content**: `extract_full_content` from preferences, else `false`.
   - **extra_frontmatter**: parse `extra_frontmatter` from preferences as a YAML mapping, else empty `{}`.

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

Then ask once. When `curate_dir` is **unset** (default), use the 3-option prompt:

```
For each, choose: **save** | **skip** | **open**
(e.g. "save 1 3, skip 2, open 4" or "save all", "skip all")
```

When `curate_dir` is **set**, include the extra option:

```
For each, choose: **save** | **curate** | **skip** | **open**
(e.g. "curate 1, save 2 3, skip 4" or "curate all")
```

- **save** — Write a markdown file to `$OUTPUT_DIR` and mark seen.
- **curate** (only if `curate_dir` is set) — Write a markdown file to `$CURATE_DIR` with `starred: true` plus a `why` recall hook (see Step 3 for how `why` is resolved), then mark seen.
- **skip** — Mark seen, take no further action.
- **open** — Use WebFetch to fetch the URL and show a brief preview, then re-prompt for that item.

If `delete_after_save` is true, also delete the bookmark from Raindrop (see step 4). This applies to both save and curate decisions.

### 3. Save / curate selected bookmarks

For each selected item, write a markdown file at `$DEST/<slug>-<id>.md` where `$DEST` is `$OUTPUT_DIR` for **save** items and `$CURATE_DIR` for **curate** items. Use a slug derived from the title (lowercase, hyphenated, ASCII-safe, max 60 chars). If the title is empty, use the domain.

**Default frontmatter (all items):**

```yaml
title: <title>
url: <link>
date: <YYYY-MM-DD>
tags: [tag1, tag2]
raindrop_id: <id>
```

**Curate-only frontmatter additions** (when `$DEST == $CURATE_DIR`):

```yaml
starred: true
why: <one-sentence recall hook>
```

Resolve `why` for curate items as follows:
- If `curate_auto_why: true`, auto-generate a one-sentence hook from the bookmark's title + excerpt (pattern: what the reader will recognize it by later — the novel claim, counter-intuitive point, or specific utility).
- Otherwise, ask the user "What made this interesting?" once per curate item (batch up to 4 per `AskUserQuestion` when available) and use the free-text response verbatim.

**Extra frontmatter merge:** If `extra_frontmatter` is non-empty, merge its keys into the frontmatter AFTER the defaults. Skip any key that would overwrite a default (`title`, `url`, `date`, `tags`, `raindrop_id`, and for curate items `starred`, `why`) — defaults win. Emit a one-line warning for each skipped conflict.

**Body:** Start with the excerpt. If `extract_full_content: true`, append a `## Content` section with the extracted article body:

1. Check if `trafilatura` is on PATH (`command -v trafilatura`). If yes:
   ```bash
   trafilatura --output-format markdown --url "<link>" 2>/dev/null
   ```
   Use the output as the content.
2. Otherwise, use WebFetch with a prompt like `"Extract the main article body as clean markdown. Drop navigation, ads, footers, comments."` and use the result.
3. If both fail (non-zero exit, empty output, paywall, network error), emit a one-line warning (`"full-content extraction failed for <url> — saving excerpt only"`) and skip the `## Content` section. **Never block the save on extraction failure.**

The user may also explicitly ask for full content per-item even when `extract_full_content` is false — in that case run the same extraction flow for just those items.

### 4. Delete from Raindrop (only if `delete_after_save=true`)

Applies to both **save** and **curate** items (skip items are handled via `.seen.json` only):

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
- How many curated (with absolute file paths) — only when `curate_dir` is set
- How many skipped
- How many deleted from Raindrop (if applicable)
- How many full-content extractions succeeded / fell back to excerpt (when `extract_full_content: true`)
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
- **Curate** is an opt-in second bucket — enable it by setting `curate_dir` in preferences. If unset, the skill falls back to the original 3-option triage and behaves exactly as it did before `curate_dir` existed.
- **Full-content extraction** via `trafilatura` requires a one-time install (`pipx install trafilatura` or `uv tool install trafilatura`). The skill degrades gracefully to WebFetch and then to excerpt-only if neither works — extraction failures never block a save.
- **`extra_frontmatter`** is merged key-by-key AFTER defaults; it cannot overwrite skill-managed keys (`url`, `raindrop_id`, etc.). Use it to add downstream-tool keys like `interest`, `status`, or custom tags.
