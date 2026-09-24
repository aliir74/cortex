# compare-skillsets preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/compare-skillsets.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## skills_dirs
<!--
Your installed skills directories, one per line. These are what a shared skillset is
compared against, and what the capability-gap grep searches.
Default: ~/.claude/skills plus each installed plugin's skills/ folder under ~/.claude/plugins/cache/
-->
skills_dirs:

## extra_search_paths
<!--
Other files or directories to include in the capability-gap grep (e.g. your CLAUDE.md,
a folder of convention docs, a scripts directory). One per line.
Default: ~/.claude/CLAUDE.md
-->
extra_search_paths:

## report_dir
<!--
Directory where the audit report is saved. Leave empty to be asked each time.
-->
report_dir:
