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
   - **curate_dir**: `curate_dir` from preferences, else unset. When set, the triage step offers extra "curate" option(s) and writes curated items here (created with `mkdir -p` on demand).
   - **curate_auto_why**: `curate_auto_why` from preferences, else `false`. Only consulted when `curate_dir` is set.
   - **extract_full_content**: `extract_full_content` from preferences, else `false`.
   - **extra_frontmatter**: parse `extra_frontmatter` from preferences as a YAML mapping, else empty `{}`.

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

Then prompt. When `curate_dir` is **unset** (default), use the 3-option prompt:

```
For each, choose: **save** | **skip** | **open**
(e.g. "save 1 3, skip 2, open 4" or "save all", "skip all")
```

When `curate_dir` is **set**, prefer `AskUserQuestion` (batched up to 4 items per call) with these options:

- **Save** — Write to `$OUTPUT_DIR`, mark seen.
- **Curate (auto-why)** — Write to `$CURATE_DIR` with `starred: true` plus an auto-generated `why` recall hook inferred from the tweet text. Show the inferred hook in the option description so the user can preview before selecting.
- **Curate (custom why)** — Same destination, but prompt the user (via free-text "Other" input) for a one-sentence `why`. When `curate_auto_why: true`, this option is omitted and the auto-why path is used unconditionally.
- **Skip** — Mark seen.
- **Open** — Use WebFetch on the expanded URL (if any) or `bird read <id>` for full text, then re-prompt for that item.

If `AskUserQuestion` is unavailable, fall back to a text prompt with the same choices (e.g. `"curate-auto 1, curate-custom 2, save 3, skip 4"`).

### 3. Save / curate selected bookmarks

For each selected item (save or curate), the destination is `$DEST = $OUTPUT_DIR` for **save** and `$DEST = $CURATE_DIR` for **curate**. All steps below apply regardless of bucket unless noted.

1. **Fetch the full thread** if the tweet is part of one (same author replying to themselves):
   ```bash
   "$BIRD" thread <tweet_id> --ct0 "$CT0" --auth-token "$AUTH" 2>/dev/null
   ```
   Use the credentials of the bookmark's `source_account`. If `bird thread` returns nothing, fall back to `bird read <tweet_id>`.

   **Preserve verbatim text — do not summarize.** Copy each tweet's exact wording into the markdown body. Summaries lose nuance and are not acceptable.

2. **Download media (only if `download_media=true`)** to `$DEST/_attachments/twitter/`:
   ```bash
   mkdir -p "$DEST/_attachments/twitter"
   # Video:
   yt-dlp -o "$DEST/_attachments/twitter/%(id)s.%(ext)s" --no-warnings "https://x.com/<author>/status/<tweet_id>" 2>/dev/null
   # Images (URLs from bird read --json):
   curl -sL "<image_url>" -o "$DEST/_attachments/twitter/<tweet_id>-1.jpg"
   ```
   Embed each downloaded asset relatively in the markdown body using a simple `![alt](_attachments/twitter/<file>)` link. If a download fails, write `[Media unavailable]` and continue.

3. **If a screenshot is downloaded**, use the Read tool on the image and transcribe any visible text into the markdown body under a `## Screenshot Content` section. Screenshots often contain the actual evidence the bookmarked tweet is reacting to.

4. **Write the file** at `$DEST/<author>-<tweet_id>.md`.

   **Default frontmatter (all items):**

   ```yaml
   author: <handle>
   url: https://x.com/<author>/status/<tweet_id>
   date: <YYYY-MM-DD>
   tags: []
   tweet_id: <id>
   source_account: <bird_account_name>
   ```

   **Curate-only frontmatter additions** (when `$DEST == $CURATE_DIR`):

   ```yaml
   starred: true
   why: <one-sentence recall hook>
   ```

   Resolve `why` based on the triage choice:
   - "Curate (auto-why)" or `curate_auto_why: true` → infer a one-sentence hook from the tweet text (the novel claim, the counter-intuitive point, or what the reader will want to find it by later).
   - "Curate (custom why)" → use the user's free-text response verbatim.

   **Extra frontmatter merge:** If `extra_frontmatter` is non-empty, merge its keys into the frontmatter AFTER the defaults. Skip any key that would overwrite a skill-managed key (`author`, `url`, `date`, `tags`, `tweet_id`, `source_account`, and for curate items `starred`, `why`) — defaults win. Emit a one-line warning for each skipped conflict.

   **Body structure:**

   ```markdown
   <verbatim tweet text — full thread if applicable>

   ## Links
   - <expanded_url_1>

   ## Linked Article Content   # only when extract_full_content=true AND there's an expanded URL
   <extracted article body>
   ```

5. **Extract full linked-article content (only if `extract_full_content=true` and the tweet has an expanded URL):**
   1. Check `command -v trafilatura`. If available: `trafilatura --output-format markdown --url "<expanded_url>" 2>/dev/null`. Use output as the content.
   2. Otherwise, use WebFetch with prompt `"Extract the main article body as clean markdown. Drop navigation, ads, footers, comments."` and use the result.
   3. If both fail (non-zero exit, empty output, paywall, network error), skip this section and emit a one-line warning (`"full-content extraction failed for <expanded_url> — skipped"`). **Never block the save on extraction failure.**

### 4. Unbookmark from Twitter (only if `delete_after_save=true`)

For each saved, curated, or skipped tweet, using the bookmark's source-account credentials:

```bash
"$BIRD" unbookmark <tweet_id> --ct0 "$CT0" --auth-token "$AUTH"
```

If the call fails, keep the local file (if any) but warn the user — the next run will re-list the bookmark unless its ID lands in `.seen.json`.

### 5. Update state

Append every processed ID to `.seen.json` (write atomically via tmp + `mv`).

### 6. Report results

Summarize:
- How many saved (with absolute file paths)
- How many curated (with absolute file paths) — only when `curate_dir` is set
- How many skipped
- How many unbookmarked (if applicable)
- How many full-content extractions succeeded / failed (when `extract_full_content: true`)
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
- **Curate** is an opt-in second bucket — enable it by setting `curate_dir` in preferences. If unset, the skill falls back to the original 3-option triage (save/skip/open) and behaves exactly as it did before `curate_dir` existed.
- **Full-content extraction** (for expanded URLs only) via `trafilatura` requires a one-time install (`pipx install trafilatura` or `uv tool install trafilatura`). The skill degrades gracefully to WebFetch and then to skipping the section if neither works — extraction failures never block a save.
- **`extra_frontmatter`** is merged key-by-key AFTER defaults; it cannot overwrite skill-managed keys (`url`, `tweet_id`, etc.). Use it to add downstream-tool keys like `interest`, `status`, or custom tags.
