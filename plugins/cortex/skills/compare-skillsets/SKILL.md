---
name: compare-skillsets
description: Use when the user shares an external skillset, plugin, or another person's skills and wants it weighed against their own installed skills. Triggers on "compare these skills to mine", "audit this skillset", "what can I learn from X", "should I adopt this plugin", and on a pasted plugin, marketplace, or skills-repo link.
---

# Compare Skillsets

An external skillset is worth two different things, and the smaller one is obvious. The skills themselves are the obvious part. The **authoring technique underneath them** is usually the bigger transfer, and it is invisible unless you go looking for it.

**Core principle:** the comparison is mechanical before it is editorial. Measure both corpora with the same script, then use judgment on what the numbers surface.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/compare-skillsets.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/compare-skillsets/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/compare-skillsets.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/compare-skillsets.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `skills_dirs` → `~/.claude/skills` plus the `skills/` folder of every installed plugin under `~/.claude/plugins/cache/` (written below as `<USER_SKILLS_DIRS>`)
   - `extra_search_paths` → `~/.claude/CLAUDE.md`
   - `report_dir` → ask before saving; otherwise present inline only

## The Iron Law

NO CAPABILITY-GAP CLAIM WITHOUT GREPPING THE USER'S INSTALLED SKILLS FIRST.

A mature setup has many skills and helper scripts whose contents are not fully listed anywhere. "You do not have X" is the single easiest sentence to get wrong, and getting it wrong sends the user to build something they already own.

```bash
ls <USER_SKILLS_DIRS>
grep -rl "<capability keyword>" <USER_SKILLS_DIRS> <extra_search_paths>
```

Search for scripts too (`*.py`, `*.sh` inside skill folders), not just SKILL.md bodies: an existing harness or measuring script often turns "build X" into "wire the existing X into one more place", which is very different advice.

## Process

### Step 1: Locate the shared skillset

| How it arrived | Where to look |
|---|---|
| Installed plugin | `~/.claude/plugins/cache/<marketplace>/<name>/<version>/skills/` |
| Marketplace not yet installed | `~/.claude/plugins/marketplaces/`, then the repo it points at |
| Git URL or repo link | Clone to a temp dir (`mktemp -d`), never into a skills directory |
| A local directory | Use it in place, read-only |
| Loose files or a paste | Write to `<tmp>/shared-skills/<name>/SKILL.md` so the script can read it |

Never install a shared skillset into a skills directory to inspect it. It joins the always-paid listing and starts auto-triggering before it has been judged.

### Step 2: Measure both corpora with one script

Run once per user skills dir (usually `~/.claude/skills`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/audit-skill-corpus.py" \
    --dir <user-skills-dir> \
    --compare <shared-skills-dir> \
    --json /tmp/skillset-audit.json
```

It reports, for both sides: frontmatter integrity, description shape, coverage of each anti-rationalization device, and the names present in both. Read the name overlap before writing a single recommendation: it is the Iron Law in report form.

Then size the cost, which that script deliberately does not compute:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/measure-instruction-corpus.py" --skills-dir <shared-skills-dir>
```

Use its numbers verbatim. Dense instruction prose tokenizes at roughly 2.5 characters per token, not the naive 4, so hand estimates run far off.

### Step 3: Read every shared SKILL.md, and its reference files

Read them; do not skim the descriptions. The transferable technique is usually in a supporting file rather than the SKILL.md, and no description will mention it.

For a large shared set, dispatch readers per skill with the Agent tool (`model: sonnet`) and keep only their findings.

### Step 4: Triage each shared skill into exactly one bucket

| Bucket | Test | Output |
|---|---|---|
| **Adopt** | Solves a problem the user has, and the Iron Law grep found nothing that already solves it | Name the target path and what changes |
| **Mine it** | Too heavyweight or wrong-shaped to run, but contains ideas that survive extraction | Name each idea and the specific skill it lands in |
| **Skip** | The user's equivalent is better, or the problem is not theirs | One sentence on which of theirs does it better |

Three rules for this table:

- **Every "mine it" row owes a mapping.** "Four useful ideas inside" is not a recommendation. Name idea, target skill, and what changes there.
- **Read the target skill's own constraints before routing an idea into it.** An idea can directly contradict a hard rule written in the skill you want to put it in (for example, routing an "act without asking" idea into a skill that requires explicit confirmation before it dispatches anything).
- **Skip is a real verdict, and usually the most common one.** A shared set built for a different kind of work earns mostly skips. Padding the adopt column to look useful wastes the user's time.

### Step 5: Extract the techniques, separately from the skills

This is the section the user will actually act on. For each technique: what it is, why it works, and **where it applies in their setup specifically**, with a file. A technique with no named local target is trivia.

Look hardest at: how descriptions are written, how rules resist being argued past, how a rule's form is matched to its failure mode, what the set does about context cost, and how it verifies its own guidance.

### Step 6: Deliver

Present an inline summary: the headline verdict, the Step 4 triage table, the Step 5 techniques, and a ranked action list. The user should never have to open a file for the headline.

For a substantial audit, also write a result artifact. If `how-to-html` is available, follow it for an HTML report (include the Step 2 coverage numbers as a sorted horizontal bar list); otherwise write markdown. Save to `report_dir`, or ask where.

### Step 7: Implement only when asked, and only behind the probe loop

Do not implement off the back of the audit. When the user does ask:

1. **Back up first.** `~/.claude` is usually not a git repository. `cp -R ~/.claude/skills "$HOME/.claude-backup-skills-$(date +%Y%m%d-%H%M%S)"` (plus any CLAUDE.md you will touch) and report the path.
2. **Baseline the probes**, if the user has a probes file: `adherence-probe.py --json before.json`. A change is only safe relative to a known-good starting score.
3. Make the changes, following `writing-skills`.
4. **Re-probe.** Any regression is the change's fault until proven otherwise. Re-run a failure several times before believing it; single runs flip in both directions.
5. **Check the caps.** `measure-instruction-corpus.py`.

**The trim rule.** A rule can only move out of always-loaded context if the skill inheriting it is guaranteed to load at the moment the rule is needed. Where loading is not guaranteed, the trim must leave a self-sufficient form behind: the literal command, not just the routing principle.

## Rationalizations

| Excuse | Reality |
|---|---|
| "They clearly do not have this capability" | Run the Iron Law grep, including scripts. Existing tooling is the most common thing to miss. |
| "I can estimate the token cost closely enough" | You cannot. Run the measuring script and quote it. |
| "The shared skill is clearly better, recommend adopting it" | Read the user's equivalent first. It may already beat the shared one, or their instructions may already route away from it. |
| "Naming the ideas is enough, they can place them" | Placement IS the recommendation. Name the target file for every idea, or leave the row out. |
| "This idea fits that skill, it is obviously compatible" | Read that skill's hard constraints before routing anything into it. |
| "The pattern grep found the answer" | A body-wide grep for a frontmatter field also matches example frontmatter inside skill bodies. Scope the match to the frontmatter slice, which is what the audit script does. |
| "One probe run is evidence" | Single samples lie in both directions. Re-run before you believe a pass or a failure. |
| "I will tidy the punctuation across this file while I am in it" | Scope every bulk style fix to lines you authored this session. |

## Red flags, stop and re-read

- "They probably do not have..."
- "Roughly N tokens"
- "Four useful ideas" with no target named
- "The probe failed, so my change broke it" (before re-running it)
- "This is basically the same as their X" (without opening X)

## What this skill does NOT do

- **It does not install anything.** Inspect in place or in a temp clone.
- **It does not author the adopted skills.** That is `writing-skills`, which owns description shape, form-to-failure, and the probe protocol.
- **It does not implement without being asked.** Step 7 is opt-in.

## Common mistakes

- **Comparing descriptions instead of bodies.** The technique is in the body and the reference files.
- **Producing a flat list of summaries.** The triage buckets and the technique extraction are the value; a summary per skill is something the user could have read themselves.
- **Treating the shared set as a standard.** It was built for someone else's work. Most of it should skip.
- **Quietly dropping a recommendation you withdrew.** Say which ones you pulled and why. A withdrawn recommendation is information.
