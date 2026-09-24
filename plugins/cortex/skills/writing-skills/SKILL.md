---
name: writing-skills
description: Use when creating a new skill, editing an existing skill's instructions, or writing any behavioral rule into a CLAUDE.md file. Triggers on "write a skill", "new skill", "fix this skill", "add a rule for", "why didn't the skill work", and on any learn-from edit that lands in a skill body.
---

# Writing Skills

Guidance is code. It ships to a runtime (a future session), it has failure modes, and an untested change to it is an untested deploy.

**Core principle:** if you have not seen a session fail without the rule, you do not know what the rule needs to say. Write the probe first.

**The corpus is not free.** Every line in `~/.claude/CLAUDE.md` (and in a project's root `CLAUDE.md`) is paid on every session, and every skill's name and description is paid in the skill listing. A line inside a skill body is paid only when that skill loads. Default to the skill.

Helper scripts referenced below ship in `${CLAUDE_PLUGIN_ROOT}/skills/helpers/`. They are stdlib-only Python; see the `helpers` skill for the full list.

## Before you write anything: is this even a documentation problem?

| The constraint is | Where it goes | Why |
|---|---|---|
| Mechanically checkable (a forbidden string, a path shape, a required flag) | A PreToolUse hook, via `create-permission-hook` | A hook cannot be rationalized past. Documentation can. |
| A judgment call under pressure | A skill, with a rationalization table | No regex decides this |
| True for every session regardless of task | `~/.claude/CLAUDE.md`, one line, pointer to detail | Rare. Most rules are not this. |
| True only inside one workflow | That workflow's skill | The common case |
| Reference data (IDs, mappings, tables) | A skill `references/` file, loaded on demand | Never always-loaded |

If a regex can catch it, do not write a paragraph about it.

## The description field: triggers only, never the workflow

A description that summarizes the process creates a shortcut future sessions will take instead of reading the body. A description saying "code review between tasks" produced one review when the body specified two; when the workflow summary was removed, the body was followed.

- Start with "Use when", third person, triggering conditions and symptoms only.
- Include the words someone would actually say, plus error strings and symptoms.
- Never list steps, never name the output format, never describe what the skill does.
- Keep it under about 400 characters. It is paid on every session as part of the listing.

```
BAD   Import bank exports (QFX/CSV) into the finance tracker, report results, and fix uncategorized transactions.
GOOD  Use when importing bank exports or reconciling the finance tracker. Triggers on "import bank data", "update finance", uncategorized-transaction cleanup.
```

**Never hand-edit the description line.** It is one YAML line that usually contains colons, backticks and slashes, and a broken frontmatter silently loads the skill with empty metadata, so it stops auto-triggering while still working via `/name`. Use the helper:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/set-skill-description.py" <skill-name-or-path> "<new description>"
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/set-skill-description.py" --report <skill-name-or-path>
```

## Match the form to the failure

Classify the failure before choosing the wording. The form that fixes one failure type backfires on another.

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Knows the rule, skips it under pressure | Prohibition, plus a rationalization table, plus red flags | Soft "prefer", "consider", "try to" |
| Complies, but the output has the wrong shape | A positive recipe: state what the output IS, its parts, in order | A prohibition list |
| Omits a required element from something it already produces | A structural REQUIRED slot in the template it fills in | A prose reminder near the template |
| Behavior should depend on a condition | A conditional keyed to an observable predicate | An unconditional rule plus exemption clauses |

**Prohibitions backfire on shaping problems.** In head-to-head wording tests, a prohibition can produce more of the unwanted content than no guidance at all. Under a competing incentive, a session negotiates with "don't X". A recipe leaves nothing to negotiate: the output either matches the stated shape or it does not.

Two corollaries, both easy to violate by accident:

- **No nuance clauses.** "Do not X unless it matters" reopens the negotiation. Appending a single nuance clause to a winning recipe can degrade it from consistent to noisy. Express a real exception as its own conditional on something observable.
- **Exemption clauses do not scope.** "This limit does not apply to code blocks" still suppresses code blocks. If part of the output must be exempt, restructure so the rule cannot reach it.

## Rationalization tables

For discipline failures only (knows better, does it anyway). Every excuse a real session actually made becomes a row. Do not invent rows for hypothetical excuses.

```markdown
| Excuse | Reality |
|--------|---------|
| "The API returned 201, so it sent correctly" | 201 proves the request succeeded, not that the content is right. Read the posted artifact back. |
| "I already ran the tests earlier" | Earlier is not now. Run them again after the last edit and quote the output. |
```

Rows come from observed failures, so each row should be traceable to a real incident. A table of guesses is decoration.

Pair a table with a red-flags list when the failure is a thought rather than an action:

```markdown
## Red flags, stop and re-read

- "Just this once"
- "I already checked that earlier"
- "Close enough"
```

And with an Iron Law when there is a single bright line worth stating absolutely:

```markdown
## The Iron Law

NO COMPLETION CLAIM WITHOUT FRESH VERIFICATION OUTPUT IN THIS MESSAGE.
```

Use at most one Iron Law per skill. Two bright lines means neither is bright.

## Which persuasion levers work

| Lever | Use it for | How |
|---|---|---|
| Authority | Discipline, safety-critical steps | Imperative, "no exceptions" |
| Commitment | Making a skipped skill visible | Require an announcement; force an explicit choice; one todo per checklist item |
| Social proof | Universal failure modes | "Checklists without todo tracking equals skipped steps, every time" |
| Scarcity | Killing procrastination | "Before proceeding", "immediately after" |
| Unity | Collaborative, judgment-heavy skills | "I need your honest read, not agreement" |

Two to avoid. **Reciprocity** reads as manipulative and is rarely needed. **Liking** actively harms: it produces sycophancy and conflicts with honest feedback.

## Test the wording, do not just ship it

The probe harness asserts with a regex, so no model judges another model. Probes live in a JSON file you own (see `helpers/probes.example.json` for the format); the default location is `${CLAUDE_PLUGIN_DATA}/adherence-probes.json`.

```bash
# Baseline: does the failure even happen? Run the control with the rule
# temporarily removed from the live corpus (see below).
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/adherence-probe.py" --only <probe_id> --repeat 5

# Then restore the rule and run the same probe again.
# Whole probe set, before and after a change.
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/adherence-probe.py" --json /tmp/probe-after.json
```

**Run the no-guidance control in place, not against a copied config dir.** On some platforms (macOS in particular) the login credential lives in the OS keychain, not under `~/.claude`, so a snapshot passed via `--config-dir` cannot authenticate. Every probe then answers `Not logged in`, which would read as a clean failure and certify an untested rule. The harness scores those runs as ERROR, but the safe control is: back up the edited file, remove the rule, probe, and restore from a shell `trap ... EXIT` so a crash still restores. Always hand-read the answers, not just the pass counts.

**The protocol, in order:**

1. **Write the probe before the rule.** A probe is a prompt whose correct answer is fixed by the rule, plus a regex that separates right from wrong. If you cannot write that regex, the rule is too vague to enforce and probably too vague to follow.
2. **The intuitive answer must be wrong.** If a model with no access to the rule would land on the right answer by default, the probe proves nothing about adherence.
3. **Always run the no-guidance control.** If the control passes, the failure is not real and the rule should not be written. Stop.
4. **Three to five reps per variant.** Single samples lie.
5. **Read every flagged match by hand.** Template echoes and quoted counter-examples masquerade as hits in both directions.
6. **Variance is a metric.** When wording lands, reps converge on the same shape. Five different readings across five reps means the wording is not binding: tighten the form before adding words.

**A skill-scoped rule needs the skill in context to be probed at all.** Skills load on demand, so a cold `claude -p` may never load the skill and the probe measures the base model, not your edit. Either have the probe prompt read the specific file, or say the probe cannot see the rule rather than reporting it as a verdict.

Use a cheap model for probes (the harness defaults to haiku) unless the failure only shows at a higher tier.

## Caps, checked mechanically

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/measure-instruction-corpus.py"
```

| Thing | Cap |
|---|---|
| `SKILL.md` | under 500 lines |
| `CLAUDE.md` (user or project root) | under 200 lines |
| Description / listing entry | about 400 chars (hard limit 1536) |

Run it after any corpus edit. It reports violations by name. Never hand-derive a token count; quote the script or `/context`.

Then pin what the probes depend on:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/skill-contracts.py"
```

Each contract is a file plus a regex for one load-bearing sentence, in `${CLAUDE_PLUGIN_DATA}/skill-contracts.json` (format: `helpers/skill-contracts.example.json`). It is free to run, so it goes before every probe: a FAIL means a rule's sentence left the file it lives in, which is exactly what a trim or a move does silently. When you write a rule a probe asserts, add its sentence as a contract in the same edit.

## Placement

| What | Where |
|---|---|
| Skill body | `<skills-dir>/<name>/SKILL.md` |
| Heavy reference (100+ lines), loaded on demand | `<skills-dir>/<name>/references/<topic>.md` |
| Script used by 2+ skills | a shared helpers folder |
| Script used by 1 skill | that skill's own folder |

Scripts are permanent and stdlib-only. Never inline `python3 -c` for anything a skill will run twice.

**Match the destination's trigger, not its topic.** The table above says WHERE a kind of content goes; it does not say a move is safe just because the new file is topically related. Before moving a rule, ask: does the destination file's own trigger actually fire in the situation the rule needs to be present for? A rule that must fire on "about to build a script" does not belong in a skill that triggers on "editing a skill's instructions", even though both are about skills. Verify with a probe or a dry run, not by re-reading the topic match.

## Checklist

Create one todo per line.

**Probe first**
- [ ] Named the specific failure, with the session where it happened
- [ ] Classified it against Match the Form to the Failure
- [ ] Wrote the probe and its regex
- [ ] Ran the no-guidance control; it fails without the rule

**Write**
- [ ] Description is triggers only, set via `set-skill-description.py`
- [ ] Form matches the failure type
- [ ] No nuance clauses, no exemption clauses
- [ ] Rationalization rows trace to real incidents, not guesses
- [ ] At most one Iron Law
- [ ] Mechanical parts pushed to a permission hook instead

**Verify**
- [ ] Probe passes with the rule, 3+ reps
- [ ] `measure-instruction-corpus.py` reports no new violation
- [ ] `skill-contracts.py` passes; new load-bearing sentences added as contracts
- [ ] Related skills that reference this one updated

## Common mistakes

- **Writing the rule from a hunch.** No observed failure means no rule. The control run is what tells you.
- **Putting it in CLAUDE.md because it feels important.** Importance is not the test; universality is. Ask whether it is true for a session that never touches this workflow.
- **Summarizing the workflow in the description.** The single highest-frequency defect, and it makes the body optional.
- **Softening a discipline rule to sound reasonable.** "Consider verifying" is not a rule.
- **Hardening a shaping rule into a prohibition.** Often worse than saying nothing.
- **Adding a nuance clause to a rule that was working.** Split it into a conditional instead.
- **Editing a skill and not re-probing.** An untested guidance edit is an untested deploy.

## Corpus maintenance rules

- When changing a workflow, folder, or convention a skill references, **proactively update the related skill file**.
- **When the user corrects a skill's output** (wrong tag, prefix, format, path), fix both the artifact and the skill in the same turn, re-deriving from the skill's own canonical logic rather than hand-patching.
- Save CLI-tool corrections to the tool's skill file, not to CLAUDE.md.
- Skills parsing CLI output use **permanent stdlib-only scripts** (shared → a helpers folder; single-use → that skill's folder), never inline `python3 -c`.

## Credits

Parts of this skill (triggers-only descriptions, test-first probing of skill wording, rationalization tables, red flags, the Iron Law device, and the persuasion-levers table) are adapted from the `writing-skills` skill in [obra/superpowers](https://github.com/obra/superpowers), MIT License, Copyright (c) 2025 Jesse Vincent.
