---
name: integrate-cli
description: Use when the user wants to integrate a CLI tool for a platform into Claude Code end-to-end — research candidates, install, authenticate, generate a <tool>-cli skill, and create a permission hook. Triggers on "integrate CLI for X", "integrate X CLI", "set up X CLI", "onboard X CLI", "add X CLI integration", or explicit /integrate-cli command.
model: sonnet
argument-hint: <platform> [pinned-cli-repo]
---

# Integrate a CLI into Claude Code

End-to-end onboarding for a new CLI tool. Produces an installed and authenticated CLI, a `<binary>-cli` skill, an optional permission hook, and (optionally) a row in the user's CLI inventory table.

## Prerequisites

Generated permission hooks require `jq`. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **integrate-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/integrate-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/integrate-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/integrate-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/integrate-cli.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `skills_dir` → `~/.claude/skills` (written below as `<SKILLS_DIR>`)
   - `hooks_dir` → `~/.claude/hooks` (written below as `<HOOKS_DIR>`)
   - `shell_rc` → `~/.zshrc` (where env-var tokens get exported)
   - `cli_inventory_file` → empty, meaning skip Stage 7.3

## When to Use

- User says `/integrate-cli <platform>` or a trigger phrase with a platform name.
- Platform has (or is likely to have) a command-line tool suitable for agent use.

## Non-Goals

- Not for pure-HTTP / MCP-only integrations.
- Not for bundling multiple platforms in one run — one platform per invocation.
- Not for updating a CLI that is already integrated — use `update-cli`.
- macOS-focused. Other OSes may require manual branching.

## Flow Overview

Seven stages. Each must succeed before the next starts. On unrecoverable failure, offer rollback of artifacts created in this run.

1. Input parsing
2. Discovery (deep-research)
3. Install
4. Auth (research-plan + CLI-probe reconciliation, user fallback)
5. Command taxonomy crawl
6. Write `<binary>-cli` SKILL.md
7. Permission hook + registration + inventory update

## Stage 1 — Input parsing

1. Extract `<platform>` from the user's message. Examples: `Linear`, `Notion`, `Jira`, `Airtable`.
2. If the user pinned a specific CLI (second argument, e.g. `/integrate-cli Linear schpet/linear-cli`), store it as `PINNED_CLI` and skip Stage 2.
3. For every plausible binary name (`<platform>`, `<platform>-cli`, common abbreviations), check whether `<SKILLS_DIR>/<binary>-cli/` already exists. If any do, use `AskUserQuestion`:
   - **Overwrite** — delete existing folder, proceed.
   - **Update quick-ref only** — skip Stages 3–4, go to Stage 5 with the existing CLI.
   - **Skip** — stop with a message.

## Stage 2 — Discovery (deep-research)

Skip this stage if `PINNED_CLI` is set.

1. Invoke the `deep-research` skill with this structured request (verbatim):

   > "Find CLI options for <platform>. For each candidate, return YAML with these fields: `name`, `install_command` (brew / npm / pipx / cargo / curl), `homepage` (GitHub or docs URL), `last_commit` (YYYY-MM-DD), `stars`, `agent_friendly` (yes/no — has JSON output? non-interactive? structured --help?), `auth_method` (oauth / env_var / login_command / config_file), `auth_command`, `required_env_vars` (list). Return at least 3 candidates if available. Rank by agent-friendliness then maintenance recency."

2. Research output is saved wherever `deep-research` saves it (its own preferences decide).

3. Parse the YAML candidates block from the research output.

4. Present the top 3 candidates via `AskUserQuestion`. Include a "None — I'll name one" escape hatch that prompts for a direct install command and homepage URL.

5. Store the user's choice as `CHOSEN_CLI` with all its fields.

## Stage 3 — Install

1. Read `install_command` from `CHOSEN_CLI`.
2. Check the relevant package manager is available:

   | install_command prefix | Check |
   |------------------------|-------|
   | `brew install`         | `which brew` |
   | `npm i -g`             | `which npm` |
   | `pipx install`         | `which pipx` |
   | `cargo install`        | `which cargo` |
   | `curl \| sh`           | always available |

   If missing, stop and tell the user to install the package manager first. Do not try alternates.

3. Run the install command. Stream output.

4. On non-zero exit: stop. Do not try alternates. Surface stderr.

5. On success, verify:
   - `which <binary>` returns a path.
   - `<binary> --version` (or `<binary> -V`) prints a version. If the CLI has no version flag, run `<binary> --help | head -5` and confirm non-empty output.
   - Save the binary name as `BINARY`.

## Stage 4 — Auth

**Plan B — from research.** Parse `auth_method`, `auth_command`, `required_env_vars` from `CHOSEN_CLI`.

**Plan A — from the CLI itself.** In parallel, run:

```bash
<BINARY> --help 2>&1 | head -200
<BINARY> auth --help 2>&1 || true
<BINARY> login --help 2>&1 || true
<BINARY> config --help 2>&1 || true
```

Extract any `auth`, `login`, `token`, `config` subcommands and relevant flags from the output.

**Reconcile A and B:**

| Case | Action |
|------|--------|
| A and B agree on auth method | Execute that plan. |
| A and B disagree | Show both plans side by side. Use `AskUserQuestion` to ask the user which is correct. |
| Both return nothing useful | **Fallback C:** Print the auth section from the research document. Say "Run these steps, then confirm when done." Wait for the user's "done" reply. |

**Execution by auth type:**

| Auth type | Steps |
|-----------|-------|
| `login_command` (e.g. `gh auth login`) | Run the command. Surface any browser URL to the user. Wait for user's "done" reply. |
| `env_var` | Ask the user to store the token themselves; never have them paste it into the chat. Recommend a dedicated `chmod 600` dotfile (e.g. `~/.<tool>.env`) sourced from `shell_rc`, rather than a plain `export` in a world-readable rc file. Wait for them to source it. Verify with `test -n "$<VAR>" && echo set` (never print the value). |
| `config_file` | Write a template to the path the CLI expects. Use `AskUserQuestion` to confirm the user has filled in credentials. |
| `oauth` | Prefer the CLI's built-in `login` subcommand if one exists. Otherwise fall back to C. |

**Smoke test:** Run one known-safe read command (e.g., `<BINARY> auth status`, `<BINARY> whoami`, `<BINARY> ping`). On failure:

- Show the error to the user.
- Offer: retry auth, switch to fallback C, or abort with rollback.
- **Do not proceed to Stage 5 if the smoke test fails.**

## Stage 5 — Command taxonomy crawl

1. Run `<BINARY> --help 2>&1` and capture the output.
2. Identify top-level subcommand groups (words/tokens that look like subcommands, not flags).
3. For each top-level subcommand, run `<BINARY> <subcommand> --help 2>&1` and capture output. Go one level deeper if it has sub-subcommands.
4. Build a taxonomy dict:

   | Category | Verbs (whitelist) |
   |----------|-------------------|
   | `always_safe` | `auth`, `version`, `help`, `--help`, `config show`, `whoami`, `status`, `completion` |
   | `read_only`   | `list`, `get`, `show`, `describe`, `logs`, `view`, `search`, `ls`, `recent`, `activity`, `inbox` |
   | `modify`      | anything else — default to modify |

5. Record concrete example commands from each `--help` block for the Quick Reference table (1–2 examples per subcommand).

6. Store:
   - `SAFE_VERBS`, `READ_VERBS`, `MODIFY_VERBS` (sorted, deduped).
   - `EXAMPLES` (list of `{task, command}` pairs).
   - `WRITE_OP_COUNT` — length of `MODIFY_VERBS`.

If `<BINARY> --help` returns no output or errors, fall back to the README section from the research output for the taxonomy. If that also fails, write the SKILL.md with a `## First-Use Crawl TODO` section and log a warning — do not stop.

## Stage 6 — Write `<binary>-cli` SKILL.md

**Skill folder name:** `<BINARY>-cli`. Exception: if `BINARY` is a single char or extremely ambiguous (`t`, `x`, `j`), use `<platform>-cli` (lower-kebab-case).

**Write this template to `<SKILLS_DIR>/<BINARY>-cli/SKILL.md`** (substitute `{{...}}` placeholders from the captured state):

````markdown
---
name: {{BINARY}}-cli
description: Use when interacting with {{Platform}} — {{short summary of capabilities, 1 sentence}}. Triggers on {{comma-separated trigger phrases}}.
model: sonnet
---

# {{Platform}} with {{BINARY}} CLI

## Auth & Setup

Install: `{{install_command}}`

Auth: {{describe auth type and reproduce the exact steps executed in Stage 4}}

Required env vars: {{required_env_vars list, or "None"}}

Verify auth: `{{smoke_test_command}}`

## Quick Reference

| Task | Command |
|------|---------|
{{for each EXAMPLE, a row: `| {{task}} | \`{{command}}\` |`}}

## Read vs Write Operations

**Read (safe, no confirmation needed):** {{READ_VERBS joined with comma}}

**Write (require user permission prompt):** {{MODIFY_VERBS joined with comma}}

## {{Each top-level subcommand group — one section}}

{{For each group, list the 2–3 most common operations with real example commands from --help.}}

## Behavioral Rules

<!-- User fills these in after first real use. -->
- Language / tone:
- Draft confirmation before sends:
- Workspace defaults:
````

**Validate the generated SKILL.md:**

```bash
python3 - "<SKILLS_DIR>/{{BINARY}}-cli/SKILL.md" "{{BINARY}}-cli" <<'EOF'
import os, re, sys
p, name = os.path.expanduser(sys.argv[1]), sys.argv[2]
content = open(p).read()
m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
assert m, 'no frontmatter'
fm = m.group(1)
assert re.search(r'^name:\s*' + re.escape(name) + r'\s*$', fm, re.M), 'name mismatch'
assert re.search(r'^description:\s*\S', fm, re.M), 'no description'
print('OK')
EOF
```

If validation fails, delete the generated file and surface the error.

## Stage 7 — Permission hook + registration + inventory update

### 7.1 — Hook decision

**Credential store check (before defaulting to Pattern A):** If the CLI is a password manager, secrets manager, API key vault, or any tool where reading exposes credentials (e.g., `op`, `bw`, `vault`, `security`), use `AskUserQuestion` to ask:
> "This CLI accesses credentials. Should reads (show, ls, export) also require confirmation, or only writes? [Gate reads too / Gate writes only]"

Default Pattern A allows reads — override this for credential-class tools by removing the read-allow block and gating everything except metadata (`--help`, `--version`, `status`).

- If `WRITE_OP_COUNT == 0`: skip hook creation. Print: "No write ops detected — no permission hook needed." Go to 7.3.
- If `WRITE_OP_COUNT >= 1`: print the detected write ops and use `AskUserQuestion`:
  > "Found {{N}} write ops: {{MODIFY_VERBS}}. Create a permission hook to gate these? [Yes / No, skip hook]"
  - **No** → skip to 7.3.
  - **Yes** → continue to 7.2.

### 7.2 — Create the hook

Invoke the `create-permission-hook` skill with a structured brief:

```
Tool: <BINARY>
Pattern: A (read/write gating)
Safe verbs: <SAFE_VERBS>
Read verbs: <READ_VERBS>
Modify verbs: <MODIFY_VERBS>
Hook file: <HOOKS_DIR>/<BINARY>-permission-check.sh
```

If the `Skill` call is refused (for example the user disabled model invocation for that skill), read `${CLAUDE_PLUGIN_ROOT}/skills/create-permission-hook/SKILL.md` directly, adapt its Pattern A template by hand, and do the registrations yourself.

The hook work covers:
- Writing the hook script (Pattern A template) and making it executable.
- Registering the PreToolUse entry in `~/.claude/settings.json` (or the settings file named in create-permission-hook's preferences).
- A permissions-TOML allow rule, **only if the user has such a file and only if the rule is scoped to read verbs**. Do NOT add a blanket `^<tool>(\s|$)` allow alongside a gating hook: an allow rule evaluated before the hook can pre-empt the hook's `ask` and let writes through ungated. When in doubt add no rule, since the hook already returns `allow` for reads.

After the hook is created, verify:

```bash
test -x "<HOOKS_DIR>/<BINARY>-permission-check.sh" && echo 'hook OK'
python3 -c "import json, os; json.load(open(os.path.expanduser('~/.claude/settings.json'))); print('JSON OK')"
grep -q '<BINARY>-permission-check' ~/.claude/settings.json && echo 'registered OK'
# Only if a permissions TOML was edited:
python3 -c "import tomllib, os, sys; tomllib.load(open(os.path.expanduser(sys.argv[1]),'rb')); print('TOML OK')" <toml-path>
```

All checks that apply must succeed. If any fail, surface the issue and offer rollback of 7.2 artifacts.

### 7.3 — CLI inventory update

Skip if `cli_inventory_file` is empty.

Otherwise, find the CLI inventory markdown table in that file (a table with columns like `Service | Skill | CLI tool`) and append a row:

```
| {{Platform}} | `<BINARY>-cli` | `<BINARY>` |
```

Use `Edit` to insert the new row just after the table's last row. Do not overwrite or reorder existing rows. If no such table exists, ask the user whether to create one.

### 7.4 — Success summary

Print a summary to the user:

- Installed: `<BINARY>` at `<path>`
- Skill: `<SKILLS_DIR>/<BINARY>-cli/SKILL.md`
- Hook: `<HOOKS_DIR>/<BINARY>-permission-check.sh` (or "skipped")
- Registered in: settings.json (plus permissions TOML if edited)
- Inventory: row appended to `cli_inventory_file` (or "skipped")
- Next steps: "Reload Claude Code so the new skill is discovered. First time you use it, add your workspace defaults and tone preferences to its Behavioral Rules section."

## Rollback

On unrecoverable failure in any stage, offer the user an interactive rollback of artifacts created **in this run only**. Never remove files created before this run.

| Stage that failed | Rollback offer |
|-------------------|----------------|
| 3 (install)       | Uninstall the CLI (run the reverse of the install command). User may decline to keep it. |
| 4 (auth)          | Ask if the user wants to uninstall the CLI. Keep env vars / config files — user may want to fix them manually. |
| 5 (taxonomy)      | Same as 4. |
| 6 (skill write)   | `rm -rf <SKILLS_DIR>/<BINARY>-cli/`. |
| 7.2 (hook)        | Remove the hook file, revert the settings.json (and TOML) edits. |
| 7.3 (inventory)   | Revert the inventory row edit. |

Rollback is always interactive — use `AskUserQuestion` for each removable artifact. If the user Ctrl+Cs mid-run, partial artifacts stay; on next invocation, detect them via Stage 1's existence check and offer Overwrite / Update / Skip.

## Failure Modes

| Failure | Handling |
|---------|----------|
| Research returns 0 candidates | Tell the user; ask them to provide a direct install command + homepage. Retry from Stage 3. |
| Package manager missing | Stop. Tell user to install it. Do not try alternates. |
| Install command fails | Stop. Show stderr. |
| `<binary>` not found after install | Stop. Tell the user to check their PATH. |
| Auth plans A and B both empty | Fallback to C (show research docs, ask user to complete). |
| Smoke test fails | Do not write the skill. Offer retry auth, switch to fallback C, or abort with rollback. |
| Binary collides with existing skill | Ask Overwrite / Update / Skip in Stage 1. |
| Hook creation fails mid-registration | Verify each registration point; revert the ones that succeeded; surface the error. |

## Success Criteria

The integration is complete when all of these are true:

1. `which <BINARY>` returns a path.
2. `<BINARY> --version` (or the smoke-test read command) returns non-error output.
3. `<SKILLS_DIR>/<BINARY>-cli/SKILL.md` exists, frontmatter parses, has a non-empty Quick Reference table.
4. If `WRITE_OP_COUNT >= 1` and user chose Yes on the hook prompt:
   - `<HOOKS_DIR>/<BINARY>-permission-check.sh` exists and is executable.
   - `~/.claude/settings.json` PreToolUse entry present.
5. If `cli_inventory_file` is set, it has a row for the new tool.

## Related

- Generated skills follow the shape of the `slack-cli`, `clickup-cli`, and `gws-cli` skills.
- Permission hook templates: `create-permission-hook`.
- Research flow: `deep-research`.
- Keeping an integrated CLI current: `update-cli`.
