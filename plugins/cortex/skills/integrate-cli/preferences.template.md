# integrate-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/integrate-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## skills_dir
<!--
Directory where the generated `<tool>-cli/SKILL.md` is written.
Default: ~/.claude/skills
-->
skills_dir:

## hooks_dir
<!--
Directory where the generated `<tool>-permission-check.sh` hook script is written.
Default: ~/.claude/hooks
-->
hooks_dir:

## shell_rc
<!--
Shell startup file that should source a CLI's token dotfile when auth is env-var based.
Default: ~/.zshrc
-->
shell_rc:

## cli_inventory_file
<!--
Optional markdown file holding a "CLI integrations" table (Service | Skill | CLI tool),
for example your ~/.claude/CLAUDE.md. A row is appended for each new CLI.
Leave empty to skip the inventory step.
-->
cli_inventory_file:
