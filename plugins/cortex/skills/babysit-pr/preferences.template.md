# babysit-pr preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/babysit-pr.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## notification_command
<!--
Shell command template fired on each event. `$MSG` is the event message.
Default (macOS): osascript -e 'display notification "$MSG" with title "Babysit PR" sound name "Glass"'
Linux example: notify-send "Babysit PR" "$MSG"
Leave empty to suppress notifications entirely.
-->
notification_command:

## max_retries
<!--
How many times to auto-push a fix before giving up. Default: 6.
-->
max_retries:

## max_idle_streak
<!--
How many consecutive "no progress" check cycles before giving up. Default: 5.
-->
max_idle_streak:

## state_dir
<!--
Where to store the PR state JSON file. Default: /tmp
-->
state_dir:

## worktree_dir
<!--
Parent directory for temporary worktrees when the PR branch isn't checked out. Default: /tmp
-->
worktree_dir:

## extra_notification_command
<!--
Additional command fired alongside the main notification — useful for sending to Telegram, Slack, etc.
`$MSG` is the event message. Leave empty to skip.
Example: tgcli send --chat-id 123456 "$MSG"
-->
extra_notification_command:
