# make-slides preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/make-slides.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## templates_dir
<!--
Absolute path to a local clone of github.com/zarazhangrui/beautiful-html-templates.
Cloned automatically on first run if missing.
Default: ${CLAUDE_PLUGIN_DATA}/beautiful-html-templates
-->
templates_dir:

## output_dir
<!--
Folder where previews and final decks are written (one <YYYY-MM-DD>-<slug>/ subfolder per deck).
Relative paths resolve against the current working directory.
Default: ./decks
-->
output_dir:
