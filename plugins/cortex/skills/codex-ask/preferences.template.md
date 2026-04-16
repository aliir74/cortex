# codex-ask preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/codex-ask.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the default documented in SKILL.md."

## default_model
<!--
Codex model used when the user does not pass `--model`.
Default: gpt-5.4
-->
default_model:

## default_effort
<!--
Reasoning effort used when the user does not pass `--effort`.
Valid values: none, minimal, low, medium, high, xhigh.
Default: (codex CLI default)
-->
default_effort:

## default_timeout_ms
<!--
Timeout for the codex exec Bash call, in milliseconds. Default: 300000 (5 minutes).
-->
default_timeout_ms:

## result_file
<!--
Absolute path where `codex exec -o` writes results. Default: /tmp/codex-ask-result.md
-->
result_file:
