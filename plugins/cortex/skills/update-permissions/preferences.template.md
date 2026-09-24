# update-permissions preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/update-permissions.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## default_scope
<!--
Where new permission rules go when you don't say: `user` (~/.claude/settings.json),
`project` (.claude/settings.json, committed) or `local` (.claude/settings.local.json).
Leave empty to be asked each time.
-->
default_scope:

## permissions_toml_path
<!--
Path to a regex-rules permissions TOML evaluated by a PreToolUse hook, if you use one
(e.g. ~/.config/claude-permissions.toml). Leave empty if you only use settings.json rules.
-->
permissions_toml_path:
