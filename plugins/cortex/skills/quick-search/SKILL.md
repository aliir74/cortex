---
name: quick-search
description: "Fast web lookup for one fact: find a doc or API page, check syntax or a version, search inside a known docs site. Use for 'find the docs for X', 'how do I X in <library>', 'look up X'. Not for multi-source synthesis or option-weighing (deep-research)."
---

# Quick Search

## Overview

Fast, focused web lookup. The opposite end of the spectrum from `/deep-research`: one query, one answer, source links, done. No sub-agents, no rounds, no saved file by default.

**Core principle:** detect the search shape (doc lookup vs factual lookup vs site-constrained), parse any site hints from the prompt, run the minimum number of searches needed, return inline with cited URLs. Escalate to `/deep-research` if the question is bigger than it looked.

## When to Use

- "Find the Anthropic prompt caching docs"
- "What's the Kysely insert-and-return syntax?"
- "Search the Tailwind docs for `container queries`"
- "Latest version of `kysely`"
- "How do I disable a GitHub Action with `gh`?"
- Single-fact lookups, syntax checks, error message lookups
- Explicit `/quick-search <query>` or `/quick-search --site=<domain> <query>`

**NOT for:**
- "Research my options for X" → `/deep-research`
- "What are best practices for Y" → `/deep-research`
- Comparison / decision / multi-faceted questions → `/deep-research`
- News / current events

## Workflow

### 1. Pre-flight: should this be `/deep-research` instead?

Before searching, scan the query for escalation signals:

| Signal | Examples | Action |
|--------|----------|--------|
| Comparison / weighing options | "X vs Y", "should I use", "what are my options for" | Suggest `/deep-research`, stop |
| Personal decisions (health, legal, financial) | "best medication for", "visa pathway for", "tax implications" | Suggest `/deep-research`, stop |
| Multi-faceted / "current best practices" | "current best practices for X", "what's the modern way to" | Suggest `/deep-research`, stop |
| Single fact / doc lookup / syntax | "the docs for X", "how to X in Y", "version of Z" | Proceed |

If escalating, respond with one line, e.g. *"This looks like a multi-source question; recommend `/deep-research <topic>` for proper coverage. Want me to run that instead?"* and stop.

### 2. Parse the query

Extract three things:

- **Site hint:** explicit (`--site=docs.anthropic.com`) or inferred ("anthropic docs" → `docs.anthropic.com`, "tailwind docs" → `tailwindcss.com`, "MDN" → `developer.mozilla.org`, "stripe docs" → `docs.stripe.com`). If unsure of the canonical domain, do an unscoped search first.
- **Core query:** the actual thing being asked, stripped of the site hint and meta words ("find", "look up", "show me").
- **Search shape:** doc-page / factual / syntax / error-message lookup. This decides which tool to reach for first.

### 3. Run the search

Pick the smallest tool that fits:

| Shape | First tool | Notes |
|-------|------------|-------|
| Site-constrained doc lookup | `WebSearch` with `site:<domain>` in the query | Most precise. Cap to ≤3 domains via `allowed_domains` if you have several guesses. |
| Known URL handed to you | `WebFetch` | If a clean-markdown extractor skill such as `obsidian:defuddle` is installed, prefer it for docs/articles (fewer tokens). |
| Free-form factual / version / syntax | `WebSearch` (no site filter) | Then fetch the top result if more detail is needed. |
| JS-rendered / SPA docs WebFetch can't read | A browser automation tool, if available | Last resort, only if WebFetch returns empty/garbage. |

Stay on keyword `WebSearch` here: `site:` filtering is already precise for single-fact lookups. If a lookup turns out fuzzy, conceptual, or multi-source, escalate to `/deep-research` rather than adding a neural search call to this skill.

**Pace:** start with 1 search. If that nails the answer, stop. If sparse, do 1–2 more targeted ones. Past ~5 web calls without an answer, switch tactics or escalate.

### 4. Synthesise and respond

Inline answer plus source URLs:

```
<direct answer in 1–4 sentences, or a small code block if it's a syntax lookup>

Source: <url>
```

For multiple relevant pages, list 2–3 URLs max.

If the answer was unfindable or sources conflict, say so explicitly and offer `/deep-research` as the next step.

### 5. Sparse-result escalation

If after 3 searches the answer is still missing, contradictory, or shallow, stop and offer:

> *"Couldn't pin this down in a quick pass; found [what you found]. Want me to run `/deep-research <topic>` for a proper dig?"*

Do not keep iterating silently.

### 6. Saving (only if asked)

Default: no file written; the answer lives in the conversation. Save only if the user explicitly asks, to the location they name (or the repo/workspace convention in CLAUDE.md).

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Treating a multi-faceted question as quick-search | Pre-flight check (Step 1): escalate to `/deep-research` upfront |
| Burning 5+ web calls on a one-liner | Stop when you have the answer, not when you've "covered the space" |
| Ignoring site hints in the prompt | "anthropic docs prompt caching" means `site:docs.anthropic.com`, not raw web |
| Reaching for browser automation first | Last resort; WebSearch + WebFetch handle almost every case |
| Silent retry loop on sparse results | After 3 attempts, stop and offer `/deep-research` |
| Returning an answer with no source URL | Always cite, even for quick lookups |

## Relationship to `/deep-research`

| | `/quick-search` | `/deep-research` |
|---|---|---|
| Shape | One question, one answer | Iterative rounds, sub-agents |
| Sources | 1–3 URLs | 4+ with cross-verification |
| Output | Inline only (default) | Inline summary + saved file |
| Budget | ~3 web calls, soft | Up to 3 rounds of multi-agent search |
| Triggers | "find docs", "what's the syntax", "look up" | "research my options", "current best practices", "what's the latest" |

If unsure which to use, lean toward `/quick-search` first: escalating is cheap, downscoping after a full research run isn't.
