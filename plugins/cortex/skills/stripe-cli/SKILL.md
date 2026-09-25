---
name: stripe-cli
description: Use when interacting with Stripe — querying customers, charges, subscriptions, invoices, products, events, and webhook testing. Triggers on "check stripe", "stripe customer", "stripe charge", "stripe subscription", "stripe invoice", "stripe product", "stripe event", "list stripe", "create stripe", "stripe webhook", "trigger stripe", or any Stripe operation.
model: sonnet
---

# Stripe with stripe CLI

## Prerequisites

Requires the `stripe` CLI. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **stripe-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/stripe-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/stripe-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/stripe-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/stripe-cli.md` — edit anytime to customize."
2. Read it. `account_label` / `account_id` name the test-mode account the CLI is expected to target (used in the pre-write confirmation and to sanity-check `stripe whoami`). `default_limit` overrides the default `--limit 10` on list commands. Empty fields mean "whatever `stripe whoami` reports" and `10`.

## Auth & Setup

Auth is OAuth via browser: `stripe login` authorizes the CLI against a Stripe account and stores keys in `~/.config/stripe/config.toml`. Optional `STRIPE_API_KEY` for non-interactive use (the permission hook hard-blocks live keys).

Verify auth: `stripe whoami --format json` (stable schema, exit 0 = authenticated, reads config only, no API call) or `stripe config --list`.

**PRODUCTION SAFETY — HARD RULE:**
- **Commands run in test mode by default.** The CLI uses `sk_test_*` keys unless told otherwise.
- **Never use the `--live` flag.** The bundled permission hook hard-blocks any command containing it.
- **Never pass a live key** (`sk_live_*`, `rk_live_*`, `pk_live_*`). Hard-blocked.
- If the user needs live data, ask them to read it in the Stripe dashboard themselves.
- **Dashboard edits default to test mode too.** If a change must be made in the Stripe dashboard in a browser, use the account's `/test/` path and confirm the page shows the test-mode indicator before saving. Edit live only when the user explicitly says live for that task.

## Quick Reference

| Task | Command |
|------|---------|
| Check auth state (JSON) | `stripe whoami --format json` |
| Show config | `stripe config --list` |
| Show full command tree | `stripe --map=tree` (also `--map=paths`, `--map=json`, `--map=compact`) |
| List customers | `stripe customers list --limit 10` |
| Retrieve a customer | `stripe customers retrieve cus_123` |
| Search customers | `stripe customers search --query "email:'user@example.com'"` |
| List charges | `stripe charges list --limit 20` |
| Retrieve a charge | `stripe charges retrieve ch_123` |
| List payment intents | `stripe payment_intents list --limit 10` |
| List subscriptions | `stripe subscriptions list --limit 10` |
| List invoices for customer | `stripe invoices list -d "customer=cus_123"` |
| List products / prices | `stripe products list --limit 20` / `stripe prices list --limit 20` |
| Get a resource by ID | `stripe get ch_123` |
| GET API path | `stripe get /v1/charges --limit 50` |
| POST API path (write) | `stripe post /payment_intents -d amount=2000 -d currency=usd` |
| DELETE API path (write) | `stripe delete /customers/cus_123` |
| Tail API logs | `stripe logs tail` |
| Listen for webhooks | `stripe listen --forward-to localhost:3000/webhooks` |
| Trigger test event | `stripe trigger payment_intent.succeeded` |
| List events | `stripe events list --limit 20` |
| Open Stripe docs | `stripe docs` |
| Create a claimable sandbox | `stripe sandbox create` |

## Read vs Write Operations

**Read (the hook allows these):** `get`, `<resource> list/retrieve/search`, `v2 <ns> <resource> list/retrieve`, `logs tail`, `listen`, `config --list`, `whoami`, `version`, `docs`, `resources`, `help`, `--map`, `--help`, `login`/`logout`

**Write (the hook prompts; test mode only):** `post`, `delete`, `create`, `update`, `capture`, `cancel`, `confirm`, `pay`, `send_invoice`, `void_invoice`, `mark_uncollectible`, `finalize_invoice`, `trigger`, `fixtures`, `refunds create`, `reject`, `verify`, `activate`/`deactivate`/`reactivate`/`archive`, `expire`/`void_grant`, `close`, `enable`/`disable`/`ping` (v2 event destinations), `apps`/`projects`/`generate` (scaffolding writes files), `sandbox create/claim`, `switch context`, `provision`, `reauth`, `agent setup`, and anything unrecognised

## Resource Commands

### Customers
```bash
stripe customers list --limit 20
stripe customers retrieve cus_123
stripe customers search --query "email:'user@example.com'"
stripe customers create -d "email=test@example.com" -d "name=Test User"
# Metadata uses bracket syntax via -d, NOT a --metadata flag:
stripe customers create -d "email=test@example.com" -d "metadata[purpose]=verification-test"
stripe customers update cus_123 -d "description=Updated"
stripe customers delete cus_123
```

### Charges & Payments
```bash
stripe charges list --limit 20
stripe charges retrieve ch_123
stripe payment_intents list --limit 10
stripe payment_intents retrieve pi_123
stripe payment_intents cancel pi_123
stripe payment_intents capture pi_123
```

### Subscriptions
```bash
stripe subscriptions list --limit 20
stripe subscriptions retrieve sub_123
stripe subscriptions cancel sub_123
stripe subscriptions update sub_123 -d "description=Updated"
```

### Invoices
```bash
stripe invoices list -d "customer=cus_123"
stripe invoices retrieve in_123
stripe invoices pay in_123
stripe invoices void_invoice in_123
stripe invoices send_invoice in_123
```

### Products & Prices
```bash
stripe products list --limit 20
stripe products retrieve prod_123
stripe products create -d "name=My Product"
stripe prices list -d "product=prod_123"
```

### Events & Webhooks
```bash
stripe events list --limit 20
stripe listen --forward-to localhost:3000/webhooks
stripe listen --events payment_intent.succeeded,charge.failed --forward-to localhost:3000/webhooks
stripe trigger payment_intent.succeeded
stripe trigger customer.created
```

### Generic GET / POST / DELETE (raw API)
```bash
stripe get cus_123
stripe get /v1/balance

# Raw POST (write). -d "key=value" for body params; bracket syntax for nested params
stripe post /payment_intents -d amount=2000 -d currency=usd -d "payment_method_types[]=card"

# Preview a POST without sending it
stripe post /customers -d "email=test@example.com" --dry-run

# Idempotency key (prevents duplicates within 24h)
stripe post /charges -d amount=500 -d currency=usd -i my-key-001

# Raw DELETE (write)
stripe delete /customers/cus_123
```

### Command discovery
```bash
stripe --map=paths             # one command per line, best for grep
stripe resources               # list API resources
stripe customers --help        # operations + required params
stripe help customers create   # full param list for one operation
```

## v2 API Resources

```bash
# namespaces: billing, commerce, core, money_management, payments, payments_intents, tax
stripe v2 core accounts list
stripe v2 core accounts retrieve <id>
stripe v2 core event_destinations enable <id>   # write
stripe v2 core event_destinations ping <id>     # write: sends a test event
```

Treat all v2 writes (`create`, `update`, `delete`, `enable`, `disable`, `ping`, `close`) as test-mode writes requiring confirmation.

## Plugins

`stripe plugin install <name>` installs plugins such as `apps`, `projects`, `generate`, `directory`, `tools`. Scaffolding plugins write files in the working directory, and agent-facing plugins can provision third-party services; treat any command they expose as a write until proven otherwise.

## Account & Sandbox Management

```bash
stripe sandbox create                 # throwaway claimable test account
stripe sandbox claim                  # claim it in the browser
stripe switch context                 # pick which account subsequent commands target
stripe reauth                         # re-consent OAuth permissions
```

**`stripe switch context` changes the account every later `stripe` command targets**, so treat it as a write with real blast radius. Confirm the target account with the user first and run `stripe whoami` afterward to verify you landed on the expected test-mode account.

## Simulating a Signed Webhook Against a Remote URL

`stripe trigger` only reaches webhook endpoints registered on the Stripe account, and `stripe listen --forward-to` only forwards to a URL reachable from this machine. To test a deployed endpoint directly (e.g. a staging or preview environment):

1. Get that environment's webhook signing secret (`whsec_...`) from its own config or secret store. The Stripe API does not return a signing secret after creation, so `webhook_endpoints retrieve` won't help.
2. Build a synthetic event JSON matching the `type` and `data.object` shape Stripe would send.
3. Sign it with HMAC-SHA256 over `f"{timestamp}.{payload}"` using the `whsec_...` string as-is, and send header `Stripe-Signature: t=<ts>,v1=<hex>`.
4. POST it to the endpoint. If the endpoint sits behind a WAF/CDN that blocks default client user agents, send `User-Agent: Stripe/1.0 (+https://stripe.com/docs/webhooks)`.

```python
import hmac, hashlib, json, time, urllib.request
def fire(url, secret, event):
    payload = json.dumps(event, separators=(",", ":"))
    ts = int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.{payload}".encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request(url, data=payload.encode(), method="POST", headers={
        "Content-Type": "application/json",
        "Stripe-Signature": f"t={ts},v1={sig}",
        "User-Agent": "Stripe/1.0 (+https://stripe.com/docs/webhooks)",
    })
    with urllib.request.urlopen(req) as r:
        return r.status, r.read().decode()
```

This is an outward write against a deployed service; confirm the URL and event with the user first.

## Behavioral Rules

- Test mode only. Never use `--live` under any circumstances.
- Default to `--limit 10` (or `default_limit`) for list commands unless the user specifies otherwise.
- Always show IDs in output so the user can drill down.
- **Before any write (create/update/delete/cancel/refund/trigger/fixtures/post), say "this runs in test mode on <account_label or whoami account>" and ask for confirmation.**
- Don't auto-clean up test-mode artifacts (customers, charges, subscriptions) unless the user asks.

## Common Mistakes

- **Using a `--metadata` flag** — it doesn't exist. Use `-d "metadata[key]=value"`.
- **`stripe trigger` to test a deployed environment** — it only reaches Stripe-registered endpoints. Use the signed-POST pattern above.
- **Piping `stripe ...` straight into a JSON parser** — shell hooks (direnv, profile scripts) can print to stdout and break parsing. Redirect to a temp file first, then parse.
- **`stripe resources help`** — not a command. Use `stripe resources` or `stripe --map=paths`.
- **`--map tree` without `=`** — the next arg is parsed as a subcommand. Use `--map=tree`.

## Self-Update

```bash
brew upgrade stripe
stripe --version
```

After upgrading, run `/cortex:update-cli stripe` to diff `--map=paths` before vs after and patch this skill and the permission hook.
