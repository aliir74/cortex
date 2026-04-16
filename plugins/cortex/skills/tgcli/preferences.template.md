# tgcli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/tgcli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default" or "ask me each time."

## default_chat_id
<!--
Chat/user ID (numeric like `-1001234567890` or `@username`) used when the
user says "send to my default chat" without specifying `--to`. Leave empty
to require an explicit target every time.
-->
default_chat_id:

## default_channel
<!--
Channel ID or username used by read commands when the user says "check my
main channel" without naming one. Leave empty to require an explicit
target.
-->
default_channel:

## context_files
<!--
Absolute paths Claude should read for additional Telegram context — e.g.
a tone/style reference for drafting messages, or a cheat sheet of
chat IDs to friendly names. One path per line. Leave empty if none.
-->
context_files:
