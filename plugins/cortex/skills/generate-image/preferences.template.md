# generate-image preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/generate-image.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

API keys do NOT go here; export `OPENAI_API_KEY` / `GEMINI_API_KEY` in your environment (see SETUP.md).

## output_dir
<!--
Folder where generated images are saved. Relative paths resolve against the current working directory.
Default: ./generated-images/
-->
output_dir:

## default_provider
<!-- openai | gemini. Default: openai -->
default_provider:

## default_model
<!-- Default: gpt-image-1.5 (openai) / gemini-2.5-flash-image (gemini) -->
default_model:

## default_quality
<!-- (openai) low | medium | high. Default: medium -->
default_quality:
