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
