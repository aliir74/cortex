---
name: catch-up
description: "Re-briefs the user on the current session when they have lost the thread (what it was about, what is done, what is left, the next step) from the conversation already in context. Use for 'catch me up', 'where were we', 'what was this session about'. Not for finding a past session (find-session)."
argument-hint: "(none, works off the current conversation)"
---

# Catch Up

Re-orient the user on the session they are currently in. They ran `claude --resume <id>` (or have been away from a long session) and the old transcript is loaded in context, but they don't remember it. Your job: read the conversation that is **already in context** and hand back a tight, accurate re-brief so they can keep going in under a minute.

This skill **reads and synthesizes**. It does not search history for a different session (`/find-session` does that) and does not spin up a new session (`/new-session` does that). It is read-only: never edit code or task files unless the user then asks you to act.

## Process

### 1. Reconstruct from loaded context

Read back over the current conversation (everything in this context window, including any prior-context summary the harness injected on resume). Pull out:
- **The original goal**: what was the user trying to accomplish? Look for the first substantive request, and an `intent:` header if one was set.
- **What actually happened**: files created/edited, commands run, decisions made, commits/PRs/branches created, things discovered.
- **Where it stopped**: the last action taken and why the session ended or stalled.

If the context looks thin or heavily compacted (e.g. only a short summary survived), say so in the brief; don't fabricate detail. As a fallback you may read the most recent session JSONL for this working directory under `~/.claude/projects/<cwd-slug>/` to recover earlier turns, but prefer what is already loaded.

### 2. Run live state checks, only for what the session touched

Infer from the transcript which of these the session actually involved, then run **only those**, in parallel:
- **Touched files / code**: `git status` and `git branch --show-current` in the relevant repo, to show uncommitted vs committed work.
- **Created or discussed a PR/MR**: `gh pr list --author @me` (or `glab mr list --author=@me` if `git remote -v` points at GitLab) to show current PR state and CI.
- **Referenced a task in a local task file or tracker**: re-read that task's current state (grep the file, or view it with the tracker's CLI if one is available).
- **Started a background process / server**: note it; don't re-scan heavily.

Skip live checks entirely for non-code sessions (research, drafting, advisory). Don't run a check the session never touched.

### 3. Deliver the brief

Inline markdown, concise and scannable, in this shape:

```
## Catch-up: <one-line what-this-is>

**Goal:** <1-2 sentences, what we set out to do>

**Done:**
- <concrete action / file / decision>

**Live state:** <git branch + clean/dirty, PR status, task state; only the checks that ran; omit this block if none applied>

**Remaining:**
- <open thread / unfinished piece>

**Next step:** <the single most immediate action to resume>
```

Keep it honest: if something was left half-done or a fix was never verified, say so plainly. Surface blockers and waiting-on items explicitly.

### 4. Offer the obvious next move

End by naming the natural follow-up, usually one of: resume the next step now, `/understand-session` if the user needs to actually grasp the work before owning it, or `/new-session` if the remaining work belongs in a fresh session in another folder. Don't auto-run any of them.

## Notes

- Don't re-derive the whole transcript verbatim. The value is the synthesis: goal, done, remaining, next, in that order, fast.
