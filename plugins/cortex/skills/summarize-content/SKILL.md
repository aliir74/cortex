---
name: summarize-content
description: Use when user wants to summarize a URL, YouTube video, podcast, or local audio/video file - triggers on "summarize this", "get summary of", YouTube/podcast URLs, or explicit /summarize command
---

# Summarize Content

Use the `summarize` CLI to extract and summarise content from URLs, YouTube videos, podcasts, and local media files. Answer inline, and optionally save a note with frontmatter.

## Prerequisites

Requires the `summarize` CLI (<https://summarize.sh>). If it's not installed, point the user to `SETUP.md` at the plugin root (section: **summarize-content**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/summarize-content.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/summarize-content/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/summarize-content.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/summarize-content.md` — edit anytime to customize."
2. Read it. Empty fields fall back to the defaults below:
   - `save_dir` (default empty): base folder for saved notes. Empty = answer inline only, don't write a file unless the user asks (then ask where).
   - `youtube_subdir` / `podcasts_subdir` / `urls_subdir` (defaults `YouTube`, `Podcasts`, `URLs`): subfolders of `save_dir` per content type.
   - `default_length` (default `medium`): value for `--length`.
   - `default_language` (default empty = the source's language): value for `--language`.

## Quick Reference

| Input Type | Command |
|------------|---------|
| Web URL | `summarize "https://example.com"` |
| YouTube | `summarize "https://youtube.com/watch?v=..." --youtube auto` |
| Podcast RSS | `summarize "https://feeds.example.com/podcast.xml"` |
| Apple Podcasts | `summarize "https://podcasts.apple.com/..."` |
| Local audio/video | `summarize "/path/to/file.mp3"` |

## Key Flags

| Flag | Purpose |
|------|---------|
| `--youtube auto` | Extract YouTube transcript |
| `--length short\|medium\|long\|xl` | Control summary length |
| `--language <lang>` | Set output language |
| `--extract` | Print extracted content only (no summary) |
| `--slides` | Extract screenshots from video |
| `--slides-ocr` | Run OCR on extracted slides |
| `--json` | Machine-readable output |

Run `summarize --help` if a flag is rejected; the CLI evolves.

## Workflow

1. Run `summarize` with the appropriate flags.
2. Review the output and give the user the summary inline.
3. If `save_dir` is set (or the user asks to save), write `<save_dir>/<type_subdir>/<kebab-title>.md` with the matching frontmatter below.

## Frontmatter Templates

**YouTube:**
```yaml
---
title: "Video Title"
channel: "Channel Name"
url: https://youtube.com/watch?v=...
date_watched: YYYY-MM-DD
duration: "00:00:00"
tags: [topic1, topic2]
summary: |
  Brief summary here.
---
```

**Podcasts:**
```yaml
---
title: "Episode Title"
podcast: "Podcast Name"
url: https://podcasts.apple.com/...
date_listened: YYYY-MM-DD
duration: "00:00:00"
tags: [topic1, topic2]
summary: |
  Brief summary here.
---
```

**URLs:**
```yaml
---
title: "Article Title"
source: "Website/Publication Name"
url: https://example.com/article
date_read: YYYY-MM-DD
tags: [topic1, topic2]
summary: |
  Brief summary here.
---
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| YouTube without `--youtube auto` | Always add `--youtube auto` for YouTube URLs |
| Wrong language output | Use `--language <lang>` |
| Summary too short/long | Use `--length` |
| Writing a file when `save_dir` is empty and the user didn't ask | Answer inline only |
