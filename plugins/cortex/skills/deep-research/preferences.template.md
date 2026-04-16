# deep-research preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/deep-research.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## default_depth
<!--
Skip the depth AskUserQuestion and use this default.
Valid values: quick, balanced, exhaustive.
Leave empty to always ask.
-->
default_depth:

## research_output_dir
<!--
Absolute directory where saved research files are written.
Default: (ask the user before saving).
Example: /Users/you/Obsidian/Research/
-->
research_output_dir:

## subagent_model
<!--
Model used by research sub-agents. Default: sonnet
Valid values: haiku, sonnet, opus.
-->
subagent_model:

## personal_context_files
<!--
Absolute paths Claude should read for additional personal context when the
research topic is personal (health, finance, immigration, etc.). One path per
line. Leave empty if none.
Example:
  /Users/you/notes/identity.md
  /Users/you/notes/life-situation.md
-->
personal_context_files:
