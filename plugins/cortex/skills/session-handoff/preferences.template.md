# session-handoff preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/session-handoff.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## output_method
<!--
Where the handoff document goes after user approval.
Valid values: clipboard, file, both.
Default: clipboard
-->
output_method:

## output_file_path
<!--
Absolute path pattern for saved handoff docs when output_method is file or both.
`$DATE` expands to YYYY-MM-DD, `$SLUG` to a short kebab-case title.
Default: ~/handoffs/$DATE-$SLUG.md
-->
output_file_path:

## extra_sections
<!--
Additional Markdown sections to append to the handoff template, one heading per
line (without the leading `##`). Leave empty to use the default template as-is.
Example:
  Related PRs
  Deploy Notes
-->
extra_sections:
