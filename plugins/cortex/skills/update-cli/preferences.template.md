# update-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/update-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## skills_dir
<!--
Directory holding your `<tool>-cli` skills.
Default: ~/.claude/skills
-->
skills_dir:

## hooks_dir
<!--
Directory holding your `<tool>-permission-check.sh` hook scripts.
Default: ~/.claude/hooks
-->
hooks_dir:

## cli_map
<!--
Optional fast-path table for CLIs whose skill folder, binary name, or update command
is not obvious. One line per CLI: `skill-folder | binary | update command | quirks`.
The skill still verifies each entry against the installed binary on every run.
Example:
  foo-cli | foo | brew upgrade foo | version probe is `foo version`, not --version
Leave empty to resolve everything from the installed binary's path.
-->
cli_map:
