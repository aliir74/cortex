---
name: session-handoff
description: Use when user wants to summarize the current session's knowledge, fixes, or progress for handoff to another AI agent or engineer - triggers on "handoff", "share context", "export session", "summarize for handoff", or explicit /session-handoff command
disable-model-invocation: true
---

# Session Handoff

Generate a structured handoff document from the current conversation so another AI agent or engineer can pick up the work.

## Process

1. **Review the full conversation** for: objectives, approaches tried, outcomes, decisions, file changes, and open items
2. **Generate the handoff document** using the template below
3. **Present it to the user** for review
4. **Copy to clipboard** using `cat << 'EOF' | pbcopy` after user approves

## Handoff Template

```markdown
# Session Handoff: [Brief title of the work]

## Objective
[What we were trying to accomplish — 1-2 sentences]

## Context
- **Repo/Project:** [repo name, branch if relevant]
- **Environment:** [language, framework, tools involved]
- **Starting state:** [what the situation was before this session]

## What Was Tried
[Numbered list of approaches attempted, with outcome for each]
1. **[Approach]** — [Result: worked / failed / partial. Why.]

## What Worked
[The solution or fix that succeeded. Be specific — include the root cause if a bug was fixed, the pattern if a feature was built.]

## Current State
[Where things stand right now. What's working, what's deployed, what's committed.]

## Open Items
- [ ] [Remaining work, known issues, or gotchas the next person should know]

## Key Files
- `path/to/file` — [why it matters]
```

## Rules

- **Be specific:** Include actual error messages, file paths, and command outputs — not vague summaries
- **Include the "why":** Don't just say what was done, explain why that approach was chosen over alternatives
- **Flag gotchas:** If something was surprising or counterintuitive, call it out explicitly
- **Keep it scannable:** Use bullets and short paragraphs, not walls of text
- **Omit empty sections:** If nothing was tried and failed, skip "What Was Tried" — only include sections with real content
