---
name: helpers
description: Shared stdlib-only Python scripts for measuring, auditing, probing and safely editing a Claude Code skill and instruction corpus. Used by writing-skills, learn-from and compare-skillsets; not a workflow on its own.
disable-model-invocation: true
---

# Shared Helper Scripts

Permanent, stdlib-only Python scripts used by more than one Cortex skill. Call them as `python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/<script>"`. Every script supports `--help`.

**Read this table before writing any new script that measures, probes, or rewrites the instruction corpus.** "Build a tool for X" often turns out to be "run the one that exists".

| Script | What it answers | Used by |
|--------|-----------------|---------|
| `adherence-probe.py` | Does a rule actually change behaviour? Asks a fresh headless `claude -p` session a question whose correct answer the rule fixes, then asserts with a regex. Probes live in your own JSON file (default `${CLAUDE_PLUGIN_DATA}/adherence-probes.json`; start from `probes.example.json`). `--repeat N` reports PASS / FLAKY / FAIL / ERROR. | writing-skills, learn-from, compare-skillsets |
| `measure-instruction-corpus.py` | What does the always-loaded corpus cost, and which files break their caps? Reads `~/.claude/CLAUDE.md` (and its @-imports), `~/.claude/rules/`, the project's `CLAUDE.md` files, and every `SKILL.md` under `--skills-dir` (repeatable). Uses a calibrated ~2.5 chars/token estimate for instruction prose. | writing-skills, learn-from, compare-skillsets |
| `audit-skill-corpus.py` | Which skills have frontmatter that silently breaks auto-triggering, which descriptions summarize the workflow instead of naming triggers, and how does device coverage compare against a shared skillset (`--compare`)? | compare-skillsets |
| `set-skill-description.py` | Rewrites a skill's frontmatter `description` in place, refusing to write unless the frontmatter parses before and after and the re-parsed value matches the input. Handles single-line and block-scalar forms; `--self-test` covers both. | writing-skills, learn-from |
| `skill-contracts.py` | Is every load-bearing sentence still in the file a rule depends on? Static regex pins in `${CLAUDE_PLUGIN_DATA}/skill-contracts.json` (start from `skill-contracts.example.json`). Free to run on every corpus edit, so it runs before `adherence-probe.py`, never instead of it. | writing-skills |

## Standing rules

- **Never hand-derive a token count.** Run `measure-instruction-corpus.py` and quote it, or read `/context`.
- **Run probe controls in place.** A copied `--config-dir` often cannot authenticate (the credential may live in the OS keychain), and `adherence-probe.py` scores such runs ERROR. Back up the file, remove the rule, probe, and restore from a shell `trap ... EXIT`.
- **Budget probe runs realistically.** Each probe rep is a full headless session. Prefer 3 reps, foreground, one or two probe ids at a time, and a cheap model unless the failure only shows at a higher tier.
- **Hand-read flagged answers.** Pass counts alone hide auth failures and template echoes.

## Design rules

- **stdlib only**, no pip dependencies
- **`--json`** for machine-readable output where applicable
- **exit 0** on success, **non-zero** on failure with a message to stderr
- User-specific data (probes, contracts) lives in `${CLAUDE_PLUGIN_DATA}`, never in the plugin directory, so it survives plugin updates
