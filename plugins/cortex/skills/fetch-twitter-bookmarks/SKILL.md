---
name: fetch-twitter-bookmarks
description: Use when user wants to fetch Twitter/X bookmarks and triage them, or when user says "fetch twitter bookmarks", "import twitter bookmarks", "sync twitter", "triage twitter bookmarks", "twitter bookmarks".
---

# Fetch Twitter/X Bookmarks

Fetches bookmarks from Twitter/X via the `bird` CLI, presents them for triage, and (optionally) saves selections to disk as markdown — with downloaded media when requested.

This skill stands alone: it does not depend on any vault layout, "curate", or "read-later" workflow. Decide where to move the saved files yourself after the skill finishes.

## Prerequisites

- The `bird` CLI installed and authenticated. If `bird` is not on `PATH` (or under `~/.bun/bin/bird`), point the user to `SETUP.md` at the plugin root (section: **bird-cli**) and stop. The companion `bird-cli` skill in this plugin documents account setup and the explicit-credentials pattern that avoids macOS Keychain prompts.
- Optional: `yt-dlp` for video downloads (only if `download_media=true` is set).

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/fetch-twitter-bookmarks.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/fetch-twitter-bookmarks/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/fetch-twitter-bookmarks.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/fetch-twitter-bookmarks.md` — edit anytime to customize."
2. Read it. Resolve values:
   - **accounts**: build the list = `[bird_account]` + `extra_accounts.split(',')`, dropping empties. If the result is empty, fall back to `bird auth current` (or whatever single account `~/.config/bird/accounts.json` exposes).
   - **output_dir**: `output_dir` from preferences, else `${CLAUDE_PLUGIN_DATA}/twitter-bookmarks/`. Create with `mkdir -p` before saving.
   - **delete_after_save**: `delete_after_save` from preferences, else `false`.
   - **download_media**: `download_media` from preferences, else `false`.

## Bird Credentials Pattern

Always pass `--ct0` and `--auth-token` explicitly. Without them, bird may try to read browser cookies via the macOS Keychain and trigger password prompts. For each account `$ACCOUNT` you intend to use:

```bash
CT0=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.config/bird/accounts.json'))); print(d['accounts']['$ACCOUNT']['ct0'])")
AUTH=$(python3 -c "import json,os; d=json.load(open(os.path.expanduser('~/.config/bird/accounts.json'))); print(d['accounts']['$ACCOUNT']['auth_token'])")
BIRD=$(command -v bird || echo "$HOME/.bun/bin/bird")
```

Then call `"$BIRD" <subcommand> --ct0 "$CT0" --auth-token "$AUTH"`.

If reading credentials fails (missing account, malformed file), tell the user to run the `bird-cli` skill's setup steps and stop.

## State File

Track which bookmark tweet IDs have already been shown so reruns don't re-list them:

```
${CLAUDE_PLUGIN_DATA}/twitter-bookmarks/.seen.json
```

Format: `{"seen": ["1234567890", ...]}`. Tweet IDs are strings (they exceed JS number range). Create it on first run if missing. Add IDs after every action.

## Steps

### 1. Fetch bookmarks from each configured account

For each `$ACCOUNT` in the resolved list:

```bash
"$BIRD" bookmarks --ct0 "$CT0" --auth-token "$AUTH" --json
```

(Adjust the bookmarks subcommand if your bird version differs — see `bird --help` and the `bird-cli` skill.) Parse the JSON. Tag each tweet with `source_account: <name>`.

Filter out tweet IDs already in `.seen.json`. If the combined filtered list is empty across all accounts, tell the user "No new bookmarks to process." and stop.

### 2. Present bookmarks

Group by account so the user sees provenance, then number across the whole list. Always include the tweet URL as a clickable link:

```
## @<account_handle> — N bookmarks

**1/N: @author — first ~100 chars of tweet text...**
[link](https://x.com/<author>/status/<id>) | <likes> likes, <retweets> RTs
Links: <expanded_url> (if present)
```

Then prompt:

```
For each, choose: **save** | **skip** | **open**
(e.g. "save 1 3, skip 2, open 4" or "save all", "skip all")
```

- **save** — Write a markdown file to `$OUTPUT_DIR` and mark seen.
- **skip** — Mark seen, take no further action.
- **open** — Use WebFetch on the expanded URL (if any) or `bird read <id>` for full text, then re-prompt for that item.

### 3. Save selected bookmarks

For each "save" item:

1. **Fetch the full thread** if the tweet is part of one (same author replying to themselves):
   ```bash
   "$BIRD" thread <tweet_id> --ct0 "$CT0" --auth-token "$AUTH" 2>/dev/null
   ```
   Use the credentials of the bookmark's `source_account`. If `bird thread` returns nothing, fall back to `bird read <tweet_id>`.

   **Preserve verbatim text — do not summarize.** Copy each tweet's exact wording into the markdown body. Summaries lose nuance and are not acceptable.

2. **Download media (only if `download_media=true`)** to `$OUTPUT_DIR/_attachments/twitter/`:
   ```bash
   mkdir -p "$OUTPUT_DIR/_attachments/twitter"
   # Video:
   yt-dlp -o "$OUTPUT_DIR/_attachments/twitter/%(id)s.%(ext)s" --no-warnings "https://x.com/<author>/status/<tweet_id>" 2>/dev/null
   # Images (URLs from bird read --json):
   curl -sL "<image_url>" -o "$OUTPUT_DIR/_attachments/twitter/<tweet_id>-1.jpg"
   ```
   Embed each downloaded asset relatively in the markdown body using a simple `![alt](_attachments/twitter/<file>)` link. If a download fails, write `[Media unavailable]` and continue.

3. **If a screenshot is downloaded**, use the Read tool on the image and transcribe any visible text into the markdown body under a `## Screenshot Content` section. Screenshots often contain the actual evidence the bookmarked tweet is reacting to.

4. **Write the file** at `$OUTPUT_DIR/<author>-<tweet_id>.md`:

   ```markdown
   ---
   author: <handle>
   url: https://x.com/<author>/status/<tweet_id>
   date: <YYYY-MM-DD>
   tags: []
   tweet_id: <id>
   source_account: <bird_account_name>
   ---

   <verbatim tweet text — full thread if applicable>

   ## Links
   - <expanded_url_1>
   ```

### 4. Unbookmark from Twitter (only if `delete_after_save=true`)

For each saved or skipped tweet, using the bookmark's source-account credentials:

```bash
"$BIRD" unbookmark <tweet_id> --ct0 "$CT0" --auth-token "$AUTH"
```

If the call fails, keep the local file (if any) but warn the user — the next run will re-list the bookmark unless its ID lands in `.seen.json`.

### 5. Update state

Append every processed ID to `.seen.json` (write atomically via tmp + `mv`).

### 6. Report results

Summarize:
- How many saved (with absolute file paths)
- How many skipped
- How many unbookmarked (if applicable)
- Any errors (auth, media download, etc.)

## Error Handling

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `bird: command not found` | bird not installed | Point user to `SETUP.md` -> bird-cli |
| Empty bookmarks list | Account has no bookmarks, or cookies expired | Tell user to refresh bird auth (see `bird-cli` skill) |
| macOS keychain prompt | `--ct0`/`--auth-token` not passed | Always use the explicit-credentials pattern above |
| 401 from Twitter | Auth tokens expired | Re-grab cookies for the account in `~/.config/bird/accounts.json` |
| Unbookmark fails but file saved | Non-fatal | Keep the file, warn the user, ID still goes into `.seen.json` |

## Notes

- The skill never unbookmarks unless `delete_after_save=true` is explicitly set.
- The "seen" state is local to this machine.
- For multi-account use, each call uses its own credentials — don't cross-pollinate (a bookmark from account A must be unbookmarked using A's tokens).
