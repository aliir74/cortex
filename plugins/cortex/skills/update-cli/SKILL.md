---
name: update-cli
description: Use when the user wants to update an installed CLI tool AND keep its `<tool>-cli` skill (and permission hook) in sync with new/changed/removed commands. Triggers on "update CLI", "upgrade <tool>", "sync skill with CLI", "refresh <tool> skill", "/update-cli". Distinct from `integrate-cli`, which onboards a new CLI from scratch.
model: sonnet
argument-hint: "[<tool-name> ...]"
---

# Update a CLI + Sync Its Skill and Hook

End-to-end refresh for an already-installed CLI: bump the binary, diff its help tree, propagate new/changed/removed commands into `<tool>-cli/SKILL.md`, and patch the matching permission hook when new write commands appear.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/update-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/update-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/update-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/update-cli.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `skills_dir` → `~/.claude/skills` (written below as `<SKILLS_DIR>`)
   - `hooks_dir` → `~/.claude/hooks` (written below as `<HOOKS_DIR>`)
   - `cli_map` → empty; resolve every binary and update mechanism from scratch (Stage 1)

## When to Use

- User asks to update/upgrade a CLI that has a `<tool>-cli` skill.
- User notices a CLI is out of date (e.g., an "Update available: x → y" banner).
- User wants the skill file regenerated against the currently-installed CLI version (no actual upgrade needed — `--no-upgrade` / `--sync-only`).

## Non-Goals

- **Not for new CLIs** — use `integrate-cli` for first-time onboarding.
- **Not for app updates** unrelated to a CLI skill (no SKILL.md to sync = nothing to do here).
- **Not for permission rule rewrites** — use `update-permissions` for `settings.json` allow/deny edits. This skill only touches `<HOOKS_DIR>/<tool>-permission-check.sh`, and only when new write commands need gating.

## Flow Overview

Six stages. Bail on any stage that fails — don't write a half-synced SKILL.md.

1. Resolve target CLI + skill path
2. Pre-update snapshot (version + help tree)
3. Run upgrade
4. Post-update snapshot
5. Diff + classify new commands (read vs write)
6. Update SKILL.md + (optionally) permission hook

## Single CLI vs Multiple CLIs

**One CLI in scope:** run Stages 1-6 inline in the main session. Skip the rest of this section.

**Two or more CLIs in scope** (user passed multiple names, said "all", or selected multiple options): **fan out subagents grouped by package manager**, each running the full flow. Do NOT crawl help trees sequentially in the main session; that burns context on `--help` output the main session never needs to read.

**Group by package manager, NOT one subagent per CLI.** Concurrent upgrades that share an installer contend for the same lock (several parallel `brew upgrade` runs block on the same Homebrew lock and can hang the batch). Typical groups:

| Group | Why grouped |
|---|---|
| Homebrew (formulae and casks) | Shared Homebrew lock. Run `brew update` ONCE at the start, then upgrade each formula in turn |
| bun global | Shared global install dir |
| npm global (including via a Node version manager) | Shared global prefix |
| Local wrappers / local clones | No upstream registry, so this is a sync-only drift repair, not an upgrade |
| Standalone installers | Resolve the real mechanism first |

Within a group the subagent processes its CLIs **sequentially** and is told so explicitly. Across groups they run concurrently.

Spawn pattern (one `Agent` tool call per group, all in a single message so the groups run concurrently):

```
Agent({
  description: "Update <group> CLIs + skills",
  subagent_type: "general-purpose",
  model: "sonnet",
  run_in_background: true,
  prompt: "<see template below>"
})
```

**Subagent prompt template** (fill in per CLI in the group):

```
You're running the full `/update-cli` flow for these CLIs, one at a time, in this order: <binary list>.
Do NOT upgrade them in parallel; they share an installer lock.

For each CLI:
- Binary: `<binary>` at `<resolved path>` (<install method>)
- Currently installed: <version>
- Skill path: `<SKILLS_DIR>/<skill-folder>/SKILL.md`
- Update command: `<resolved upgrade command>`
- <Any tool-specific quirks: banner-strip rules, shell-function wrappers, sibling skills not to touch, financial / message-sending risk class>

Reference: read `${CLAUDE_PLUGIN_ROOT}/skills/update-cli/SKILL.md` for the full 6-stage flow.

Do this per CLI:
1. Pre-update snapshot: `bash ${CLAUDE_PLUGIN_ROOT}/skills/update-cli/scripts/diff-help-tree.sh <binary> /tmp/update-cli-<binary>-<ts>/before-tree.txt`.
2. Upgrade via the resolved command. If it fails, STOP for that CLI and return the error; do not touch its SKILL.md.
3. Post-update snapshot to after-tree.txt.
4. Diff: new/removed top-level commands, subcommands, flags. Classify Read vs Write (Stage 5 keywords). Err on Write for financial / message-sending CLIs.
5. Update SKILL.md: version markers, Quick Reference table, Read/Write classification, dedicated sections, prune removed, add `## Self-Update` if missing.
6. Permission hook: if new Write commands exist AND `<HOOKS_DIR>/<tool>-permission-check.sh` exists, patch it. If the hook is missing AND new Write commands exist, FLAG it (do not auto-create).

Constraints:
- Do NOT touch settings.json or permission allowlists; out of scope.
- Autonomous edits OK; no per-diff confirmation (this is a parallel batch).
- If the upgrade is a no-op (already latest), proceed to Stage 5 anyway to repair drift.

Return a 4-7 line summary per CLI in the Output Format of the reference skill.
```

After all subagents complete, the main session consolidates the per-CLI summaries into a single table.

**Why subagents over inline:** crawling help trees and reading several SKILL.md files for many CLIs pushes a large volume of one-time-use output into the main context. Subagents isolate that noise and return only the structured summary.

## Stage 1 — Resolve target CLI(s)

1. **From args:** if the user passed one or more tool names (e.g. `/update-cli stripe gemini`), use them directly. If they passed "all", expand to every CLI skill found in step 2.
2. **No args:** list skills matching `<SKILLS_DIR>/*-cli/` (plus any skill whose folder name differs from its binary, e.g. `tgcli/`) and ask via `AskUserQuestion`. Show:
   - Skill folder name
   - Binary name (parsed from the skill's install line or its `## Auth` / `## Setup` section)
   - Currently-installed version

   **AskUserQuestion option cap.** The tool accepts at most 4 options per question. With more than 4 CLIs:
   - Split into multiple questions of ≤4 options each, in the **same** `AskUserQuestion` call (up to 4 questions per call, so 16 CLIs per round).
   - If you still have more than 16, run a second round.
   - Tell the user in the question text that they can pick several via the "Other" free-text input (e.g., "1,3" or "all").
   - Never pass 5+ options to one question; it errors with `InputValidationError`.

3. **Resolve binary + update mechanism** for each target. If `cli_map` in preferences has an entry for it, use that as a fast path, but still verify. Otherwise:
   - Find the real binary with `command -v <binary>` or `type -a <binary>`. `which` can return a shell-function body when the CLI is wrapped by a function in the user's shell rc; always resolve to the real path and invoke it by absolute path so help output is not polluted by wrapper stderr.
   - Resolve symlinks (`readlink -f` or `realpath`) and infer the installer from the target path:

     | Resolved path contains | Likely update command |
     |---|---|
     | `/Cellar/` or `/Caskroom/` | `brew upgrade <formula>` (or `brew upgrade --cask <cask>`) |
     | `/.bun/` | `bun install -g <package>@latest` |
     | `/node_modules/` or a Node version-manager dir | `npm i -g <package>@latest` (use the package name from the symlink target) |
     | `/.cargo/bin/` | `cargo install <crate>` |
     | `/pipx/` | `pipx upgrade <package>` |
     | A git checkout (`.git` beside the binary or its target) | `git pull` in that clone plus its build step |
     | None of the above | ask the user |

   - Find the right version probe. Some CLIs use `version` as a subcommand instead of `--version`; some print disclaimers or ANSI codes around the version.

4. **Confirm with user** if the binary or update mechanism is ambiguous.

## Stage 2 — Pre-update snapshot

Capture the version and help tree (top-level plus one level deep) with the bundled script, which also strips common upgrade banners (`Update available`, `npm notice`, `bun notice`):

```bash
SNAP=$(mktemp -d "/tmp/update-cli-${BINARY}-XXXXXX")
bash "${CLAUDE_PLUGIN_ROOT}/skills/update-cli/scripts/diff-help-tree.sh" "$BINARY" "$SNAP/before-tree.txt"
```

If the script's `Commands:` heuristic finds no subcommands (CLIs format help differently), crawl manually: for each top-level subcommand listed in `--help`, capture `<binary> <subcmd> --help` into the same file.

If the binary is already at the latest version and the user invoked `/update-cli` with `--sync-only` or `--no-upgrade`, skip Stage 3.

## Stage 3 — Run the upgrade

1. Run the resolved update command. Stream stdout/stderr to the user — no silent upgrades.
2. If the command fails, **stop here**: print the error, do not touch SKILL.md, do not run Stage 4.
3. After success, verify the new version with the version probe from Stage 1.
4. If the new version equals the old version, surface that and ask if the user wants to re-sync the skill anyway (Stage 4+).

## Stage 4 — Post-update snapshot

Same crawl as Stage 2, written to `$SNAP/after-tree.txt`.

## Stage 5 — Diff and classify

1. **Version diff:** old → new (record for the SKILL.md changelog or version markers).
2. **Full diff:** `diff "$SNAP/before-tree.txt" "$SNAP/after-tree.txt"`.
3. **Top-level command diff:** compare the command names in the two `=== <binary> --help ===` blocks → **new** and **removed** top-level commands.
4. **Subcommand diff:** repeat for each `=== <binary> <sub> --help ===` block.
5. **Flag diff (per command):** new `--flags` are informational; usually they don't need to be in the table.
6. **Classify each new command as Read or Write** by name pattern:
   - **Read (safe, no permission gate):** `list`, `get`, `show`, `search`, `find`, `preview`, `inspect`, `view`, `read`, `tail`, `whoami`, `test`, `status`, `count`, `unreads`
   - **Write (requires hook + confirmation):** `send`, `post`, `create`, `new`, `add`, `delete`, `remove`, `edit`, `update`, `set`, `react`, `archive`, `complete`, `reopen`, `save`, `remind`, `run`, `trigger`, `invite`, `kick`, `merge`, `close`, `revert`
   - **Ambiguous:** ask the user. Anything that touches external state, shared infra, or sends visible messages = Write.

## Stage 6 — Update SKILL.md and hook

Open `<SKILLS_DIR>/<skill-folder>/SKILL.md` and apply changes in this order. In single-CLI mode, show a unified-diff preview before each write and confirm with the user.

### 6a. Version markers

Bump any `(vX.Y+)` section markers if a new section is being added for a feature introduced in this release.

### 6b. Quick Reference table

Insert one row per new command at the end of the existing table. Pattern:

```markdown
| <verb in plain English> | `<binary> <command-path> [<minimal-args>]` |
```

Use the example argument from the help text where possible; otherwise use placeholders consistent with the rest of the table (`<id>`, `"#channel"`, `"@user"`).

### 6c. Read vs Write Operations classification

Append each new command to the right line. Edit in place; keep the original order.

### 6d. Dedicated sections

Add a section per new top-level command (or per logical feature group). Template:

````markdown
## <Feature name> (vX.Y+)

```bash
# <One-line purpose>
<binary> <command> [<flags>]

# <Variant>
<binary> <command> --<flag> <value>
```

<One paragraph: when to use it, common gotchas, write-side-effect warning if applicable.>
````

For Write commands, **always include an explicit "this is a write operation that does X" sentence** so future sessions don't run them implicitly.

### 6e. Removed/renamed commands

If Stage 5 found removed commands, search SKILL.md for references. For each:
- If the command appears in the Quick Reference, delete the row.
- If it has a dedicated section, replace the section with a one-line `**Removed in vX.Y** — use <replacement> instead.` note (or delete entirely if no replacement).

### 6f. Permission hook patch (write commands only)

Look for `<HOOKS_DIR>/<tool>-permission-check.sh`. Two cases:

- **Hook exists:** read the script. If it gates write commands by name (regex or case statement), propose adding the new write commands to that pattern. **Show the diff and require explicit user confirmation** — hooks are global and affect every session.
- **Hook missing but new write commands found:** flag for the user that they may want to create one with `create-permission-hook`. Don't auto-create; that's a wide-blast-radius decision.

If the new commands are all read-only, no hook change is needed.

### 6g. Self-Update section

If the SKILL.md doesn't already have a `## Self-Update` (or similar) section, add one with the resolved update command. This makes future runs faster.

## Common Mistakes

- **Running multiple CLI updates inline in the main session.** Always fan out subagents when 2+ CLIs are in scope.
- **Spawning one subagent per CLI when several share a package manager.** Group by installer and go sequential inside each group.
- **Passing 5+ options to AskUserQuestion.** Split into several questions of ≤4 options in the same call.
- **Diffing without the help-tree crawl.** Top-level `--help` only shows top-level commands; new subcommands hide one level down.
- **Trusting the description verbatim.** A rephrased description is not a new command. Match by command name, not description string.
- **Auto-classifying every new command as read.** When in doubt, ask. A misclassified write command means future sessions run it without confirmation.
- **Forgetting to strip upgrade banners.** `Update available` / `npm notice` lines break naive JSON and grep parsing.
- **Touching settings.json or permission allowlists.** Out of scope; defer to `update-permissions`.
- **Updating a skill for a CLI that isn't installed.** Verify the binary is on `$PATH` first. If the user uninstalled the CLI but kept the skill, ask before doing anything.
- **Resolving the binary through a shell function.** Use `command -v` / `type -a`, not `which`, then call the absolute path.
- **Skipping confirmation before writing SKILL.md (single-CLI mode only).** In fan-out mode, subagents edit autonomously and the user reviews the consolidated summary.

## Output Format

After all stages succeed, print a 4-7 line summary:

```
Updated <binary>: <old-version> → <new-version>
- <N> new commands documented (<list>)
- <N> commands classified as Write (<list>) — added to hook: <yes/no/skipped>
- <N> commands removed (<list>) — pruned from SKILL.md
- <N> sections added: <names>
- Skill: <SKILLS_DIR>/<skill>/SKILL.md
- Hook: <HOOKS_DIR>/<hook>.sh (or "no hook touched")
```
