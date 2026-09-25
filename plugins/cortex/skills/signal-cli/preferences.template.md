# signal-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/signal-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty falls back to the default noted in the comment.

## account
<!--
Your Signal number in E.164 form, passed as `-a <value>`. Only needed when more
than one account is registered locally (`signal-cli listAccounts`). Empty = no -a.
-->
account:

## device_name
<!-- Name shown under Linked Devices on your phone. Empty = claude-code. -->
device_name:

## receive_archive
<!--
Absolute path of a JSONL file that every `receive` result is appended to before
parsing, since each event arrives only once. Empty = ./signal-receive.jsonl.
-->
receive_archive:
