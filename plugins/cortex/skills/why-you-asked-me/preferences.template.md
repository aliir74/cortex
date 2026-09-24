# why-you-asked-me preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/why-you-asked-me.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## hooks_dir
<!--
Directory holding your PreToolUse permission hook scripts.
Default: ~/.claude/hooks
-->
hooks_dir:

## permissions_toml_path
<!--
Path to a regex-rules permissions TOML evaluated by a PreToolUse hook, if you use one
(the same file create-permission-hook can append allow rules to, e.g.
~/.config/claude-permissions.toml). Leave empty if you only use settings.json rules.
-->
permissions_toml_path:
