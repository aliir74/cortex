# fetch-raindrop-bookmarks preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/fetch-raindrop-bookmarks.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty falls back to the documented default.

## raindrop_api_token
<!--
Personal API token from https://app.raindrop.io/settings/integrations
(create a "Test token" — it grants access to your own collections only).

Recommended: leave this blank here and export the token as the
RAINDROP_API_TOKEN environment variable instead, so it isn't stored
on disk in plain text. The skill checks the env var first, then this field.
-->
raindrop_api_token:

## collection_id
<!--
Numeric ID of the Raindrop collection to fetch from.
- Use `0` for "Unsorted" (default if left empty)
- Use `-1` for "All bookmarks"
- Use `-99` for "Trash"
- For a specific collection, open it in Raindrop and copy the trailing
  number from the URL (e.g., https://app.raindrop.io/my/12345678 -> 12345678).
-->
collection_id:

## output_dir
<!--
Absolute path to the directory where the skill saves bookmark markdown files.
Default if empty: ${CLAUDE_PLUGIN_DATA}/raindrop-bookmarks/
-->
output_dir:

## delete_after_save
<!--
When true, bookmarks saved to disk are deleted from Raindrop afterwards
(useful for "inbox-style" workflows). When false (default), bookmarks stay
in Raindrop and the skill tracks "seen" IDs locally to avoid re-listing
them on the next run.
Accepted values: true, false. Default: false.
-->
delete_after_save:

## curate_dir
<!--
Optional absolute path for a "curate" bucket — a second destination for
bookmarks you want to star/keep as interesting finds rather than just file
to an inbox. When set, the skill shows an extra triage option ("curate")
alongside save/skip/open. Curated items are written to this directory with
`starred: true` in frontmatter plus a short `why` recall hook you provide
(or that's inferred from title/excerpt when `curate_auto_why: true` is set).

Leave empty to keep the default 3-option triage (save/skip/open) — no
curate bucket.

Example: /Users/you/notes/Knowledge/Curated/
-->
curate_dir:

## curate_auto_why
<!--
When true and `curate_dir` is set, the skill auto-generates the `why`
recall hook from the bookmark's title/excerpt instead of prompting for it
per-item (faster, but less personal). When false (default), the skill asks
you "what made this interesting?" before saving each curated item.
Accepted values: true, false. Default: false.
-->
curate_auto_why:

## extract_full_content
<!--
When true, the skill automatically extracts the full article body for
saved and curated items (not just the excerpt) and appends it under a
`## Content` heading in the saved markdown file.

Extraction strategy (first available wins):
1. `trafilatura` CLI if on PATH (best quality, requires `pipx install trafilatura`
   or `uv tool install trafilatura`).
2. Otherwise, WebFetch with a "extract the article body as markdown" prompt.
3. If both fail (paywall, JS-only render, network error), save just the
   excerpt and emit a one-line warning — never block the save.

When false (default), only the excerpt is saved; the user can still say
"save with full content" per-item to trigger WebFetch extraction.
Accepted values: true, false. Default: false.
-->
extract_full_content:

## extra_frontmatter
<!--
Optional YAML block merged into the frontmatter of every saved/curated
markdown file. Lets you extend the default schema (title, url, date, tags,
raindrop_id) without forking this skill — useful if you have a downstream
tool (inbox triage, dashboard, etc.) that expects specific keys.

Provide a valid YAML mapping. Keys in `extra_frontmatter` are MERGED into
the default frontmatter; if a key here conflicts with a default key, the
default wins (the skill won't let you overwrite `url` or `raindrop_id`).

Leave empty to use just the default frontmatter.

Example (for Obsidian-style inbox triage):
  interest: null
  overflow: false
  triaged_at: null
-->
extra_frontmatter:
