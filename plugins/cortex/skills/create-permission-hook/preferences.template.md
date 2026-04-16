# create-permission-hook preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/create-permission-hook.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## default_hook_dir
<!--
Where newly generated hook scripts should be written by default.
Default: ~/.claude/hooks/
Plugin-scoped hooks should live inside the plugin's hooks/ directory instead.
-->
default_hook_dir:

## default_permissions_toml_path
<!--
Path to the global permissions TOML file where new allow rules get appended.
Default: ~/.config/claude-permissions.toml
-->
default_permissions_toml_path:

## default_settings_json_path
<!--
Path to the settings.json file where PreToolUse hooks get registered.
Default: ~/.claude/settings.json
-->
default_settings_json_path:
