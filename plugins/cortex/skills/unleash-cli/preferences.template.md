# unleash-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/unleash-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default".

## default_profile
<!--
Profile name from ~/.unleash.env passed as `--profile <value>` on every call.
"default" (or empty) reads UNLEASH_URL / UNLEASH_PAT; any other name, e.g. "staging",
reads UNLEASH_URL_STAGING / UNLEASH_PAT_STAGING.
-->
default_profile:

## default_project
<!--
Unleash project id passed as `--project <value>` to `flag` subcommands.
Empty means the Unleash built-in project "default".
-->
default_project:

## production_environments
<!--
Comma-separated environment names that count as production, so writes to them
always get an explicit confirmation in chat. Empty means "production".
-->
production_environments:
