# stripe-cli preferences

Copy this file to `${CLAUDE_PLUGIN_DATA}/preferences/stripe-cli.md` and fill in your values. The skill reads that copy, not this template, so your values survive plugin updates.

Any field left empty means "use the CLI's default".

## account_label
<!--
Human name for the test-mode account the CLI should target, used in the
pre-write confirmation (e.g. "Acme US sandbox").
-->
account_label:

## account_id
<!--
The expected Stripe account id (acct_...). The skill compares it against
`stripe whoami --format json` before writes and warns on a mismatch.
-->
account_id:

## default_limit
<!-- Page size for list commands when the user gives none. Empty = 10. -->
default_limit:
