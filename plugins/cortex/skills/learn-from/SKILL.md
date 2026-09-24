---
name: learn-from
description: Use when user wants to analyze the current conversation for Claude mistakes and corrections, then suggest improvements to CLAUDE.md, memory, or skill files to prevent recurrence - triggers on "learn from mistakes", "what went wrong", "improve from this chat", "learn from", or explicit /learn-from command
---

# Learn From Conversation

Analyze the current conversation for mistakes, positive patterns, and decisions, then propose concrete edits to the right instruction file so the next session does better.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/learn-from.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/learn-from/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/learn-from.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/learn-from.md` — edit anytime to customize."
2. Read it. Empty fields fall back to these defaults:
   - `near_miss_log` → the current project's Claude Code auto-memory (`MEMORY.md`); if auto-memory is off, `${CLAUDE_PLUGIN_DATA}/learn-from-near-misses.md`
   - `extra_target_files` → none
   - `skills_dirs` → `~/.claude/skills`, plus any skill directory of a plugin whose skill was invoked in this conversation

## Process

### Step 1: Scan the conversation

Read the entire conversation and identify:

**Mistakes and corrections**
1. **Explicit corrections** — the user said "no", "wrong", "not that", "I meant X", "use Y instead"
2. **Repeated attempts** — Claude tried something 2+ times before getting it right
3. **Redirects** — the user steered away from an approach ("don't do X", "that's not how we do it")
4. **Denied tool calls** — the user denied a tool execution (signals a wrong approach)
5. **Wasted effort** — work the user had to undo or discard
6. **Wrong assumptions** — Claude assumed something that turned out to be incorrect
7. **Ignored context** — Claude missed information from CLAUDE.md, memory, or earlier in the conversation
8. **Failed CLI invocations** — a command failed (wrong path, missing env setup, wrong flags) and had to be retried, even if the user didn't comment; the error output itself is the signal. Subcategorize:
   - **Skill syntax error** — a CLI covered by a skill was called with a wrong or nonexistent flag or argument format. The fix belongs in **that skill's SKILL.md**.
   - **Wrong reference data** — stale or incorrect cached data (wrong ID, a name that doesn't resolve, a stale path). The fix belongs in **the file holding that data**.
   - **Ignored existing rule** — the correct rule already exists but wasn't followed. Do NOT add a duplicate; make the existing rule more prominent (see Step 3, item 5). Always note: "Rule existed at [file:line] but was ignored."

**Positive signals**
9. **Positive feedback** — "perfect", "exactly", "that's great": capture what worked and why
10. **Smooth execution** — tasks completed without corrections: note the patterns that made this work

**Decision moments**
11. **The user chose between options** — capture the decision criteria
12. **The user volunteered background** — unprompted context ("we use X because...") is a strong signal
13. **Code project decisions** — architecture, library picks, error handling, testing approach, naming, folder structure, trade-offs future sessions should follow; prime candidates for the project's `CLAUDE.md` if not already documented

For each finding, extract: **what happened**, **the user's response**, **the underlying rule** (the generalizable lesson), and **a category** from the table below.

### Step 2: Categorize

| Category | Examples |
|----------|----------|
| **Wrong file/path** | Used wrong directory, created file in wrong location |
| **Wrong tool/command** | Used npm instead of pnpm, wrong CLI tool |
| **Failed CLI — skill syntax** | Wrong flag or argument format for a skill's CLI. Fix target: the skill's SKILL.md. **Version-tag limitations**: run `<tool> --version` and note it ("not supported in v0.6.0") so future sessions know to re-check after upgrades. |
| **Failed CLI — wrong reference data** | Stale ID, cached name that doesn't resolve. Fix target: the reference file holding it |
| **Failed CLI — ignored existing rule** | Rule existed but wasn't followed. Fix: prominence, not duplication |
| **Failed CLI — other** | Wrong path, missing env setup, wrong flags for commands no skill covers |
| **Wrong convention** | Wrong naming, format, or style |
| **Wrong assumption** | Assumed a behavior, skipped reading existing code |
| **Missed context** | Didn't check CLAUDE.md, memory, or a file the user pointed at |
| **Over-engineering** | Unnecessary complexity, features, or abstractions |
| **Wrong workflow** | Skipped required steps, wrong order |
| **Wrong scope** | Did too much or too little, misunderstood the request |
| **Positive pattern** | Something that worked well, worth reinforcing |
| **Decision pattern** | How the user makes choices, for future reference |

### Step 3: Recurrence and tier gate (before presenting anything)

Not every mistake is a rule. Filter here so the user sees real rule candidates, not a list of one-offs.

**1. Recurrence filter. A single mistake is not yet a rule.** For each finding, search `near_miss_log` (and the target files from Step 5) for a prior near-miss on the same behavior:

- **First occurrence** → record a one-line near-miss in `near_miss_log` (date, what happened, what rule would have prevented it). Do NOT edit a canonical instruction file. Do NOT present it as a proposed rule.
- **Second occurrence** (a matching near-miss exists) → now it is a rule candidate. Promote it and cite both occurrences as evidence.
- **Exception, promote on first occurrence** only when the single failure was expensive and concrete: data loss, a broken production path, a leaked secret, or a silently wrong result that shipped. Say which applies.

If you cannot name the failure a proposed rule prevents, drop it. "This would be tidier" is not a finding.

**2. Tier before target.** A rule needed in every session goes in always-loaded context; a rule that only applies inside one workflow goes in that workflow's skill; **a multi-step procedure becomes or joins a skill, never a CLAUDE.md**; reference data goes in an on-demand file. Mechanically checkable constraints go in a PreToolUse hook (`create-permission-hook`), not prose.

**3. Phrase as a goal with concrete specifics**, not an emphasized prohibition, and check that Claude Code doesn't already do this by default before adding guidance for it.

**4. Budget guard.** Before proposing an edit to an always-loaded file (`~/.claude/CLAUDE.md`, a project root `CLAUDE.md`, `MEMORY.md`), run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/measure-instruction-corpus.py"
```

and quote the current size in the proposal. If the file is already near its cap, a net-new rule must come with the section that moves out to a skill or a reference file. If you cannot name what moves out, the rule is not for the always-loaded tier.

**5. Prominence, not duplication.** If the correct rule already existed and was ignored, move or sharpen it: put it next to the action where the mistake happens, add an inline wrong-vs-right example, or bold it. Never add a second copy; near-duplicates resolve arbitrarily, which makes two copies worse than one.

### Step 4: Present findings

```
I found N patterns in this conversation:

**Rule candidates:**
1. **[Category]**: [What went wrong]
   - You corrected: "[user's correction]"
   - Rule: [generalizable lesson]
   - Evidence: [this session + prior near-miss, or the first-occurrence exception that applies]

**Logged as near-misses (first occurrence):**
- [one line each]

**Positive patterns:**
- **[What worked]**: [why it worked]
```

If there are no findings, say so honestly. Don't fabricate issues.

### Step 5: Discover target files

1. **Skills invoked in this conversation** — read `<skills_dir>/<skill>/SKILL.md` for any skill whose workflow the finding concerns. Skills are the first-class target for lessons about their own behavior.
2. **Project instructions** — Glob `**/CLAUDE.md` from the current working directory (root and subfolders).
3. **User instructions** — `~/.claude/CLAUDE.md`.
4. **Auto-memory** — the project's `MEMORY.md` under `~/.claude/projects/<project>/memory/`, if auto-memory is enabled.
5. **`extra_target_files`** from preferences.

Read each to learn what rules already exist (avoid duplicates), which sections are relevant, and where the new rule fits.

### Step 6: Propose specific edits

For each rule candidate:

```
Finding: [description]
Target file: [full path]
Action: [Add new rule / Update existing rule / Move existing rule]
Proposed text:
  > [exact text]
```

**Placement, cheapest first.** The order is also a cost order: the first rows are free until read, the last rows are paid on every session.

| Rule type | Location | Session cost |
|-----------|----------|--------------|
| Skill-specific lesson | The related skill's `SKILL.md` | Zero until the skill loads |
| Reference data for one domain | A `references/` file of the related skill, or an `extra_target_files` entry | Zero until read |
| Subfolder technical knowledge | That subfolder's `CLAUDE.md` | Only when working there |
| Project convention | Project root `CLAUDE.md` | Every session in that project |
| Global preference (all projects) | `~/.claude/CLAUDE.md` | Every session everywhere; budget-neutral, name what moves out |
| Truly cross-cutting behavior with no better home | Auto-memory `MEMORY.md` | Every session in that project; last resort |

**Prefer a scoped CLAUDE.md or skill over MEMORY.md.** Auto-memory loads regardless of what the session is doing, so a domain rule there pollutes unrelated work.

**Rules for good entries:**
- Imperative instructions, not observations
- Specific: "Always use `pnpm`, not `npm`, in this repo" rather than "the user prefers pnpm"
- Include the "why" only if it's non-obvious
- Update an existing similar rule rather than adding a new one
- One or two lines each
- Prefix inferred items with `(inferred)`

### Step 7: Choose the form, and probe it (REQUIRED)

An edit that does not change behavior is paperwork, not a fix.

**Form.** Match the wording to the failure (full table in `writing-skills`):

| The session | Right form | Wrong form |
|---|---|---|
| Knew the rule, skipped it under pressure | Prohibition, plus a row in that skill's rationalization table | Soft "prefer", "consider" |
| Complied, but produced the wrong shape | A positive recipe stating what the output IS | A prohibition list |
| Left out a required element | A REQUIRED slot in the template it fills in | A prose reminder |
| Should behave differently by condition | A conditional on an observable predicate | A rule plus exemption clauses |

Never append a nuance clause to a rule that was working; split it into a conditional.

**Probe.** If the rule is checkable by regex, add a probe to your probes file and run it:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/adherence-probe.py" --only <probe_id> --repeat 3
```

**Run the control first**, by temporarily reverting the rule in the live file and restoring it afterwards:

```bash
cp <edited-file> /tmp/learn-from-edited.bak
trap 'cp /tmp/learn-from-edited.bak <edited-file>' EXIT
# revert just the new rule in the live file, then:
python3 "${CLAUDE_PLUGIN_ROOT}/skills/helpers/adherence-probe.py" --only <probe_id> --repeat 3
```

Do not control with a copied config dir plus `--config-dir`: where the login credential lives in the OS keychain, the copy cannot authenticate and every run is an ERROR, not a behavioral signal. Use `--repeat 3` or more; one run cannot separate "rule missing" from "lucky guess". A skill-scoped rule is only probe-able if the probe prompt makes the session read that skill file; otherwise say the probe cannot see it.

If the control PASSES, the failure was situational: drop the rule and say so.

### Step 8: Confirm with the user

Use `AskUserQuestion` to confirm which proposed edits to apply, whether the targets are right, and whether any should be skipped or modified.

### Step 9: Apply and report

For each confirmed edit: read the target file, find the right section (or create one), apply with Edit, avoid duplicating existing content. If the edit landed in a skill body, follow `writing-skills` (and use `set-skill-description.py` for any description change).

Then show a summary of what was added or moved and where, and what was logged as a near-miss. Re-run `measure-instruction-corpus.py` if an always-loaded file changed.

## Common Mistakes

- Writing narrative observations instead of actionable rules
- Adding duplicate rules that already exist somewhere in the corpus
- Placing project-specific rules in `~/.claude/CLAUDE.md`, or global preferences in a project file
- Vague rules ("be more careful") instead of specific ones ("always check X before Y")
- Not reading the existing target files before proposing edits
- **Defaulting to MEMORY.md** when a subfolder CLAUDE.md or a skill would scope the rule better
- Proposing a CLAUDE.md edit when the mistake is about a specific skill's behavior; the skill file comes first
- **Dismissing a failure as "already documented".** If the rule existed and was still broken, it isn't prominent enough. Propose a concrete visibility edit.
- Turning a one-off into a rule without the recurrence check
