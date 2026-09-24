# learn-from preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/learn-from.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## near_miss_log
<!--
File where first-occurrence mistakes are recorded as one-line near-misses, so a second
occurrence can be recognized and promoted to a rule.
Default: the project's auto-memory MEMORY.md, or ${CLAUDE_PLUGIN_DATA}/learn-from-near-misses.md
when auto-memory is off.
-->
near_miss_log:

## extra_target_files
<!--
Additional instruction or context files learn-from should consider as edit targets,
one absolute path per line (for example a notes file of personal preferences, or a
directory of domain convention files). Leave empty for none.
-->
extra_target_files:

## skills_dirs
<!--
Directories holding skills that may be edited, one per line.
Default: ~/.claude/skills (plus the skill folder of any plugin skill invoked in the session).
-->
skills_dirs:
