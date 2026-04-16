# bird-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/bird-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default" or "ask me each time."

## default_account
<!--
The account name (as shown by `bird account list`) used when bird is
configured for multi-account and the user does not specify which account
to act as. Leave empty to use whatever bird considers its current account.
-->
default_account:

## default_list
<!--
A Twitter/X list ID used by `bird list-timeline` when the user asks for
"my list" without naming one. Leave empty to require an explicit list ID.
-->
default_list:

## context_files
<!--
Absolute paths Claude should read for additional Twitter context — e.g.
a notes file mapping handles to people you follow, a list of accounts
you're tracking for a project, or your own posting style notes. One path
per line. Leave empty if none.
-->
context_files:
