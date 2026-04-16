# slack-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/slack-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default" or "ask me each time."

## default_workspace
<!--
Substring (or full URL) of the Slack workspace the skill should target by
default — e.g. `acme` to match `acme.slack.com`. The skill passes this as
`--workspace` on every command. Leave empty if you only have one workspace
imported.
-->
default_workspace:

## default_channel
<!--
Channel name (e.g. `#general`) or channel ID used when the user says
"send to my default channel" or doesn't specify a target. Leave empty to
require an explicit target every time.
-->
default_channel:

## signature
<!--
Optional sign-off appended to outgoing messages (e.g. `— Sent by Claude`).
Leave empty for no signature.
-->
signature:

## context_files
<!--
Absolute paths Claude should read for additional Slack context — e.g. a
cached map of user IDs to display names so we don't re-look up the same
people, or notes about specific channels. One path per line. Leave empty
if none.
-->
context_files:
