# create-plan-md preferences

Seeded to `${CLAUDE_PLUGIN_DATA}/preferences/create-plan-md.md` on first run. The skill reads that copy, not this template, so your values survive plugin updates. `execute-plan-md` and `create-plan-and-execute-md` read the same file.

Any field left empty means "use the default documented in SKILL.md."

## plans_dir
<!--
Where markdown plans are written. Absolute, ~/..., or relative to the repo root
(or the current directory outside a git repo). The $PLAN_DIR env var overrides it.
Default: docs/plans/ if that directory exists in the repo, otherwise plans/.
Example: docs/plans
-->
plans_dir:

## open_after_create
<!--
Open the written plan with the OS default opener (open / xdg-open) after writing.
Valid values: true, false. Default: true
-->
open_after_create:

## default_tdd
<!--
Skip the TDD question and use this answer. Valid values: yes, no.
Leave empty to ask (recommended: yes for code, no for docs/ops/config).
-->
default_tdd:

## draft_model
<!--
Model for the plan-drafting sub-agent. Valid values: haiku, sonnet, opus.
Default: opus
-->
draft_model:
