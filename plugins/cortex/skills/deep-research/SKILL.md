---
name: deep-research
description: Use when researching any topic - technical docs, best practices, API changes, library updates. Triggers on explicit /deep-research or phrases like "what's the latest on X", "current best practices for Y", "research X for me"
---

# Deep Research

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/deep-research.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/deep-research/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/deep-research.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/deep-research.md` — edit anytime to customize."
2. Read it. If `default_depth` is set, skip the depth AskUserQuestion and use it directly. Use `research_output_dir` as the save destination (otherwise ask the user before saving). Use `subagent_model` as the model for research sub-agents (otherwise `sonnet`). If `personal_context_files` is set and the topic is personal, read those files before searching.

## Overview

Research skill that discovers broadly via web search, then verifies against official sources. The main session acts as **Lead Researcher** — orchestrating iterative rounds of sub-agents, reviewing output between rounds, and spawning deeper searches based on findings. Adapts depth to query complexity.

## When to Use

- User asks about latest documentation, API changes, library updates
- Phrases: "what's the latest on", "current best practices", "research X for me", "what's new in"
- Explicit `/deep-research <topic>` invocation

**NOT for:** News/current events, competitive analysis

## Workflow

### Phase A: Preparation

#### 1. Check Existing Research
Search the project for any existing research on the topic BEFORE any web search.
If existing research is found, use **AskUserQuestion** to ask:
```
Question: "I found research on [topic] from [date]. What would you like to do?"
Header: "Existing"
Options:
  - "Use existing" / "Skip new research and use what we have"
  - "Research fresh" / "Start over with new web searches"
  - "Update existing" / "Build on top of the existing research"
```

#### 2. Determine Scope & Depth
Use **AskUserQuestion** to ask scope and depth:
```
Question: "How deep should I research this?"
Header: "Depth"
Options:
  - "Quick overview (2-3 sources)" / "Fast answer with key facts"
  - "Balanced (4-6 sources) (Recommended)" / "Good coverage without going overboard"
  - "Exhaustive" / "As many sources as needed, thorough deep dive"
```
If the topic is clearly a single-fact lookup (version number, specific answer), skip asking and do an inline response + source link.

### Phase B: Research Rounds (Iterative)

The main session acts as **Lead Researcher** — coordinating agents, reviewing findings between rounds, and deciding when to go deeper.

#### Round 1 — Broad Discovery
**REQUIRED:** Use parallel sub-agents to search simultaneously (2-3 agents).
**Model:** All research sub-agents MUST use `model: "sonnet"` to optimize cost. The main session (Lead Researcher) stays on the default model for orchestration and synthesis.

**Search targets:**
- Official documentation
- Recent release notes / changelogs
- GitHub issues / discussions
- Recent blog posts / tutorials
- Community resources, forums

Each agent returns: key findings, source URLs, identified gaps, suggested follow-up areas.

#### Lead Researcher Reviews Round 1
After agents return, the main session:
1. Reads all agent outputs
2. Identifies: gaps, contradictions, areas needing deeper investigation
3. Tells user: "Round 1 complete. Found X, Y, Z. Gaps: A, B. Going deeper on those."
4. Decides: enough info? -> proceed to Phase C. Need more? -> Round 2.

#### Round 2+ — Targeted Deep Dives (if needed)
Spawn agents with `model: "sonnet"` for SPECIFIC gaps identified in the previous round:
- "Verify conflicting claims about X"
- "Find official source for Y"
- "Check if Z applies to [specific use case]"

Each subsequent round gets MORE SPECIFIC than the last (broad -> targeted -> verification).

#### Lead Researcher Reviews Round N
Same review process. Exit when:
- Sufficient coverage, no critical gaps remain
- Maximum 3 rounds reached (prevent infinite loops)

**Key rules:**
- Maximum 3 rounds total
- Each round should be MORE SPECIFIC than the last
- Always tell user what round you're on and what gaps you're investigating
- Quick lookups skip the iterative pattern entirely (inline answer + source link)

### Phase C: Synthesis & Output

#### 5. Verify Against Official Docs
For each finding from non-official sources:
- Cross-check against official documentation
- Sources >12 months old: explicitly verify still accurate

#### 6. Flag Conflicts
When sources disagree, present BOTH:
```
**Conflict:** Source A says X, Source B says Y
- A: [explanation + link]
- B: [explanation + link]
Your call which applies to your situation.
```

#### 7. Present Inline Summary (MANDATORY)

> **IMPORTANT:** This step is NON-NEGOTIABLE. ALWAYS do this before mentioning saved files.

After all research is complete, ALWAYS present a concise TL;DR summary directly in the conversation response. This should be:
- **Executive summary** (2-3 sentences max) — the absolute essence of findings
- **Key numbers/facts** in a compact table or bullet list
- **Actionable takeaways** — what the user should do with this information
- Written for someone who "doesn't have time to read the full report"

This summary MUST appear BEFORE mentioning any saved files.

#### 8. Optionally Save Research
If the user wants to save the research, save to a file with structured frontmatter:
```yaml
---
date: YYYY-MM-DD
title: Descriptive Title
summary: One-line summary
tags: [relevant, tags]
last_verified: YYYY-MM-DD
sources:
  - https://...
---
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| Topic too broad | Use AskUserQuestion to narrow focus |
| Existing research found | Use AskUserQuestion: use existing, refresh, or update? |
| Quick lookup | Inline response + source link |
| Comprehensive research | AskUserQuestion for depth -> iterative rounds -> inline summary -> save |
| Conflicting sources | Flag both, let user decide |
| Outdated source (>12mo) | Auto-verify against official docs |
| Round 1 has gaps | Tell user, spawn Round 2 for specific gaps |
| Max rounds reached (3) | Synthesize what you have, note remaining gaps |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip existing research check | ALWAYS search for existing research on the topic first |
| Assume depth without asking | Ask "How deep?" via AskUserQuestion for comprehensive queries |
| Type questions in chat and wait | ALWAYS use AskUserQuestion tool for user input |
| One-shot flat research | Use iterative rounds — review between rounds, go deeper on gaps |
| Present conflicts as facts | Flag disagreements explicitly |
| Skip inline summary | ALWAYS present TL;DR before mentioning saved files |
| Assert feature ABSENCE without verification | NEVER claim a product/service LACKS a feature unless verified against official specs. When uncertain, write "unverified" instead of "No". |

## User Interaction Rule

**MANDATORY:** Whenever this skill needs user input (choosing between options, confirming a direction, narrowing scope, selecting depth), use the **AskUserQuestion** tool. Do NOT type the question as text in the conversation and wait for the user to reply. AskUserQuestion provides a structured UI with selectable options, which is faster and clearer for the user.
