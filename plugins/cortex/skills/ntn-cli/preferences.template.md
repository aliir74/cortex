# ntn-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/ntn-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "ask me each time".

## default_parent
<!--
Parent for new pages when none is named, in ntn's form:
page:<id>, database:<id>, or data-source:<id>.
-->
default_parent:

## known_data_sources
<!--
Friendly names for data sources you query often, one per line, e.g.
tasks: <data-source-id>
Resolve a database id to its data-source ids with `ntn datasources resolve <database-id>`.
-->
known_data_sources:
