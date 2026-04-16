# fetch-twitter-bookmarks preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/fetch-twitter-bookmarks.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty falls back to the documented default.

## bird_account
<!--
Name of the bird account to use, as listed in `~/.config/bird/accounts.json`
(see the bird-cli skill for setup). When `bird` is configured with a single
account, leave this blank — the skill will use whatever account `bird auth current`
reports.

For multiple accounts, set this to the default. You can still override per-run
by saying "use my <other> account" before invoking the skill.
-->
bird_account:

## extra_accounts
<!--
Comma-separated list of additional bird accounts to fetch from on every run.
Useful when you bookmark from multiple personas and want a single combined triage.
The skill tags each bookmark with its source account so you know where it came from.
Leave empty for single-account use.
Example: tech_handle,personal_handle
-->
extra_accounts:

## output_dir
<!--
Absolute path to the directory where the skill saves bookmark markdown files
(and downloaded media under <output_dir>/_attachments/twitter/).
Default if empty: ${CLAUDE_PLUGIN_DATA}/twitter-bookmarks/
-->
output_dir:

## delete_after_save
<!--
When true, bookmarks saved or skipped are unbookmarked from Twitter/X afterwards
(useful for inbox-style workflows). When false (default), bookmarks stay on X
and the skill tracks "seen" tweet IDs locally to avoid re-listing them.
Accepted values: true, false. Default: false.
-->
delete_after_save:

## download_media
<!--
When true, the skill downloads images and videos referenced by saved tweets
into <output_dir>/_attachments/twitter/ and embeds them in the saved markdown.
Requires `yt-dlp` (videos) and `curl` (images) on PATH.
Accepted values: true, false. Default: false.
-->
download_media:
