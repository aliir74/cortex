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

## curate_dir
<!--
Optional absolute path for a "curate" bucket — a second destination for
tweets you want to star/keep as interesting finds rather than just file to
an inbox. When set, the skill shows two extra triage options ("curate
(auto-why)" and "curate (custom why)") alongside save/skip/open. Curated
items are written to this directory with `starred: true` in frontmatter
plus a short `why` recall hook (auto-inferred from the tweet text or
free-text from you, depending on which curate option you pick).

Leave empty to keep the default 3-option triage (save/skip/open) — no
curate bucket.

Example: /Users/you/notes/Knowledge/Curated/
-->
curate_dir:

## curate_auto_why
<!--
When true and `curate_dir` is set, the "curate" option auto-generates the
`why` recall hook from the tweet text and skips prompting (fastest path).
When false (default), the skill shows both options — "curate (auto-why)"
with a preview of the inferred hook, and "curate (custom why)" which lets
you type your own reason.
Accepted values: true, false. Default: false.
-->
curate_auto_why:

## extract_full_content
<!--
When true, the skill automatically extracts the full article body for any
saved/curated tweet that has an expanded URL (t.co-unwrapped link) and
appends it under a `## Linked Article Content` heading in the saved file.

Extraction strategy (first available wins):
1. `trafilatura` CLI if on PATH (best quality, requires `pipx install trafilatura`
   or `uv tool install trafilatura`).
2. Otherwise, WebFetch with a "extract the article body as markdown" prompt.
3. If both fail (paywall, JS-only render, network error), skip extraction
   and emit a one-line warning — never block the save.

Tweets without expanded URLs are unaffected.

Accepted values: true, false. Default: false.
-->
extract_full_content:

## extra_frontmatter
<!--
Optional YAML block merged into the frontmatter of every saved/curated
markdown file. Lets you extend the default schema (author, url, date,
tags, tweet_id, source_account) without forking this skill — useful if
you have a downstream tool (inbox triage, dashboard, etc.) that expects
specific keys.

Provide a valid YAML mapping. Keys here are MERGED into the default
frontmatter; if a key conflicts with a skill-managed key, the default
wins (the skill won't let you overwrite `url`, `tweet_id`, etc.).

Leave empty to use just the default frontmatter.

Example (for Obsidian-style inbox triage):
  interest: null
  overflow: false
  triaged_at: null
-->
extra_frontmatter:
