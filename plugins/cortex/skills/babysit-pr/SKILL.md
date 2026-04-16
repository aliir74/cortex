---
name: babysit-pr
description: Use when monitoring a GitHub PR that needs CI fixes, code review fixes, or deploy URL tracking. Triggers on "babysit pr", "watch pr", "monitor pr", or explicit /babysit-pr command
disable-model-invocation: true
argument-hint: <pr-number-or-url>
---

# Babysit PR

Monitor a GitHub PR on a recurring loop. Automatically fix failed CI checks, address Claude Code Review feedback, address human review comments, and notify when deploy previews are ready.

**Invocation:** `/loop 5m /babysit-pr [pr-number-or-url]`

This skill is designed to run inside a `/loop`. Each invocation performs one check cycle and exits. The loop handles recurring execution.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/babysit-pr.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/babysit-pr/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/babysit-pr.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/babysit-pr.md` — edit anytime to customize."
2. Read it. Use `notification_command` for every event (falls back to the default `osascript` line under Notifications), `max_retries` for the retry cap, `max_idle_streak` for the idle cap, `state_dir` for the JSON state file location, `worktree_dir` for temporary worktrees, and `extra_notification_command` for a second channel (Telegram/Slack) fired alongside the main one. Empty fields mean "use the default."

## Argument Parsing

1. If argument is a GitHub URL -> extract owner/repo and PR number from URL
2. If argument is a number -> use as PR number, resolve repo from `gh repo view --json nameWithOwner -q '.nameWithOwner'`
3. If no argument -> resolve via `gh pr view --json number,headRefName`

## State File

Path: `/tmp/babysit-pr-<owner>-<repo>-<number>.json`

```json
{
  "pr_number": 47,
  "repo": "org/backend",
  "branch": "feature/signup",
  "fix_attempts": 0,
  "max_retries": 6,
  "no_progress_streak": 0,
  "max_idle_streak": 5,
  "last_fix_sha": null,
  "deploy_notified": false,
  "checks_green_notified": false,
  "review_fixed": false,
  "human_review_fixed": false,
  "completed": false
}
```

Create on first run. Load on subsequent runs.

## Main Cycle

1. Load state (or create)
2. If `completed` -> exit (tell user to cancel the loop)
3. Check PR state: `gh pr view <number> --json state` — if MERGED or CLOSED -> mark completed, exit
4. If `fix_attempts >= max_retries` -> notify "gave up (too many fix attempts)", mark completed, exit
5. If `no_progress_streak >= max_idle_streak` -> notify "gave up (stuck waiting — no progress)", mark completed, exit
6. Fetch: `gh pr view <number> --json statusCheckRollup,comments` and `gh api repos/<owner>/<repo>/pulls/<number>/comments` (inline review comments)
7. **Evaluate Claude Code Review FIRST** (see below) — review typically completes fastest; fixing it early avoids waiting for a second full CI cycle
8. **Evaluate Human Review Discussions** (see below) — check inline review comments from team members
9. Evaluate checks (see below)
10. Evaluate deploy (see below)
11. **Track progress:** Set `made_progress = true` if any fix was pushed this iteration. If `made_progress` -> reset `no_progress_streak` to 0. Otherwise increment `no_progress_streak`.
12. Save state

**Priority order matters:** Always check and fix review feedback before evaluating CI status. The review check (`claude-review`) usually finishes in ~2 minutes while other checks take 5-10 minutes. Fixing review issues immediately means the re-triggered CI run overlaps with the still-running first CI run, saving a full cycle.

## Check Status Handling

| Status | Action |
|--------|--------|
| All pass | Set `checks_green_notified` internally (do NOT notify yet — wait until review is also handled) |
| Any failed | Enter fix flow (with duplicate guard) |
| Some pass + some pending | Wait for next cycle |
| Failed + pending | Fix failed, ignore pending |

**IMPORTANT:** Do NOT fire the "checks green" notification when checks first pass. Review fixes will push new code and re-trigger CI. Only notify "all checks are green" at completion time, after both checks and review are resolved.

### Fix Flow

1. **Duplicate guard:** Get failing run's head SHA. If it predates `last_fix_sha` -> skip, wait for CI to re-run
2. Parse `statusCheckRollup` for failed check names and run IDs
3. Fetch logs: `gh run view <run_id> --log-failed`
4. **Worktree:** `git branch --show-current` — if on PR branch, work here. Otherwise: `git worktree add /tmp/babysit-worktree-<number> <branch>`
5. Read logs, identify issue, make fix
6. Verify locally if possible (run the project's lint/test command from CLAUDE.md)
7. Commit: `fix: resolve ci failure in <check-name>` — push to PR branch
8. Update state: increment `fix_attempts`, set `last_fix_sha`
9. If worktree created: `git worktree remove` after push

## Claude Code Review Handling

After evaluating CI checks, look for a Claude Code Review comment and fix the issues it raises.

### Detection

1. Search PR comments for a comment authored by `claude` whose body contains `### Issues` or `### Code Review`
2. If no such comment exists -> skip (review not posted yet or not configured)
3. If `review_fixed` is already `true` -> skip (already handled)

### Parsing the Review Comment

Review comments vary in format. Parse ALL actionable items using these heuristics:

- **Structured format:** Items under `### Issues` or `### Nits` headings, numbered as `**N. title**` with file references in backticks
- **Inline format:** Bold-titled items with file references and descriptions in `### Code Review` sections
- Code suggestions appear as fenced code blocks within each item

**IMPORTANT: Fix ALL items regardless of priority labeling.** Items marked as "low priority" or "not a blocker" are still valid improvements and MUST be fixed. Only skip items that would break functionality.

### Review Fix Flow

1. **Worktree:** Same logic as CI Fix Flow
2. For each issue/nit: read the file, understand the suggestion, apply the fix
3. **Verify:** Run the project's lint command (check CLAUDE.md) to ensure fixes don't introduce new issues
4. **Commit:** Single commit: `fix: address code review feedback`
5. **Push** to the PR branch
6. Update state: set `review_fixed: true`, increment `fix_attempts`, set `last_fix_sha`
7. Notify: "PROJECT PR NUMBER: addressed code review feedback (N issues fixed)"

## Human Review Discussion Handling

After evaluating Claude Code Review, check for unresolved human review discussions.

### Detection

1. Fetch inline review comments: `gh api repos/<owner>/<repo>/pulls/<number>/comments`
2. Filter for comments by humans (not bots)
3. Group by thread (`in_reply_to_id`)
4. If `human_review_fixed` is already `true` -> skip

### Decision Flow

| Situation | Action |
|-----------|--------|
| Reviewer asks for code change, no reply yet | Fix it if straightforward; ask user if ambiguous |
| Reviewer asks a question, author replied | Skip (resolved) |
| Ambiguous or design-level discussion | Notify user: "PR has unresolved discussion about X — needs your input" |

## Deploy Monitoring

1. Scan PR comments for body starting with `/deploy`
2. Find the LAST `/deploy` comment chronologically
3. Look for first comment after it authored by `github-actions[bot]` containing a URL
4. If found and not yet notified -> notify "preview ready", set `deploy_notified: true`

## Notifications

Fire a macOS notification for every event:

```bash
osascript -e 'display notification "MESSAGE" with title "Babysit PR" sound name "Glass"'
```

| Event | Message |
|-------|---------|
| Completed (all green) | "PROJECT PR NUMBER: all checks are green" |
| Preview ready | "PROJECT PR NUMBER: preview environment is ready" |
| CI fix pushed | "PROJECT PR NUMBER: pushed a fix for CHECKNAME, attempt N of 6" |
| Review fix pushed | "PROJECT PR NUMBER: addressed code review feedback, N issues fixed" |
| Gave up (too many fixes) | "PROJECT PR NUMBER: gave up fixing checks after 6 attempts" |
| Gave up (stuck waiting) | "PROJECT PR NUMBER: no progress for 5 consecutive checks — stuck" |

## Completion

Mark `completed: true` when ALL:
- Checks resolved (green or gave up)
- Claude review handled (`review_fixed: true`, or no review comment found)
- Human review handled (`human_review_fixed: true`, or no unresolved discussions)
- Deploy either not requested OR `deploy_notified: true`

When completed, tell the user: "PR babysitting complete. You can cancel the loop now."

## Quick Reference

| Task | Command |
|------|---------|
| PR status + comments | `gh pr view <N> --json statusCheckRollup,comments,state` |
| Failed run logs | `gh run view <run_id> --log-failed` |
| Run head SHA | `gh run view <run_id> --json headSha -q '.headSha'` |
| Claude review comment | `gh pr view <N> --json comments --jq '.comments[] \| select(.author.login == "claude") \| .body'` |
| Create worktree | `git worktree add /tmp/babysit-worktree-<N> <branch>` |
| Remove worktree | `git worktree remove /tmp/babysit-worktree-<N>` |
| macOS notify | `osascript -e 'display notification "MSG" with title "Babysit PR" sound name "Glass"'` |

## Common Mistakes

- Not checking `last_fix_sha` before fixing -> re-fixing the same failure
- Not checking PR state (merged/closed) -> looping forever on closed PRs
- Pushing fixes without incrementing `fix_attempts` -> infinite fix loop
- Working in wrong worktree when current branch differs from PR branch
- Trying to fix review comments before `claude-review` check completes
- Not running lint after review fixes -> introducing new issues
- Forgetting to reset/increment `no_progress_streak`
- Treating "low priority" review items as already handled
- Only parsing `### Issues` headings -> missing inline suggestions in `### Code Review` sections
