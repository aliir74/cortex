# gemini-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/gemini-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "check the live model list and choose".

## default_model
<!--
Model id passed as `-m <value>` for quick prompts (e.g. a flash tier).
List what your key exposes with:
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY" | jq -r '.models[].name'
-->
default_model:

## quality_model
<!--
Model id used for prose, reasoning, non-English writing and creative work (a pro tier).
-->
quality_model:
