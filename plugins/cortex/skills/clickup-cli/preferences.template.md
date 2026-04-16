# clickup-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/clickup-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default" or "ask me each time."

## default_list_id
<!--
The ClickUp list ID where new tasks land when you don't pass `--list-id`.
Find yours by running: `clickup list list` or copy from a task URL.
-->
default_list_id:

## default_assignee
<!--
Your ClickUp member ID (numeric) or username. The skill only auto-assigns
when you explicitly ask it to — this value is the default for those cases.
Leave empty to default to the current CLI-authenticated user.
-->
default_assignee:

## default_space
<!--
Space name used when searching without an explicit `--space` flag.
Leave empty to search across the whole workspace.
-->
default_space:

## default_folder
<!--
Folder name used when searching without an explicit `--folder` flag.
Leave empty to skip folder filtering.
-->
default_folder:

## context_files
<!--
Absolute paths Claude should read for additional context when creating
or updating tasks (e.g., a TODO.md in your notes vault, a project
tracking file). One path per line. Leave empty if none.
-->
context_files:
