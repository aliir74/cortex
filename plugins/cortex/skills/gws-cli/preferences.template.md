# gws-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/gws-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

Note: gws also honors `GOOGLE_WORKSPACE_CLI_ACCOUNT` as an env var. Values here are used only when no env var is set.

## default_account
<!--
Email address used when the user does not specify one.
If empty, gws uses the account marked default in `gws auth list`.
-->
default_account:

## default_calendar
<!--
Calendar name used when the user does not pass `--calendar` to +agenda/+insert.
Default: (query all calendars for +agenda, use primary for +insert).
-->
default_calendar:

## default_triage_max
<!--
Max number of messages shown by `gws gmail +triage`. Default: (gws CLI default).
-->
default_triage_max:

## personal_email
<!--
Your personal email (used for CC'ing yourself on outgoing messages when asked).
Leave empty to never auto-CC.
-->
personal_email:
