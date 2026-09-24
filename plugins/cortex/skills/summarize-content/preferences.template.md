# summarize-content preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/summarize-content.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## save_dir
<!--
Absolute path of the folder where summary notes are saved (e.g. a notes vault folder).
Default: (empty, answer inline only; save only when asked)
-->
save_dir:

## youtube_subdir
<!-- Subfolder of save_dir for YouTube summaries. Default: YouTube -->
youtube_subdir:

## podcasts_subdir
<!-- Subfolder of save_dir for podcast summaries. Default: Podcasts -->
podcasts_subdir:

## urls_subdir
<!-- Subfolder of save_dir for web article summaries. Default: URLs -->
urls_subdir:

## default_length
<!-- short | medium | long | xl. Default: medium -->
default_length:

## default_language
<!-- Output language passed to --language. Default: (empty, source language) -->
default_language:
