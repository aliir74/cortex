---
name: deploy-preview
description: Use when user wants to trigger a preview deployment for the current branch's PR, says "deploy preview", "deploy this", "trigger deploy", or explicit /deploy-preview command
disable-model-invocation: true
---

# Deploy Preview

## Overview

Comments `/deploy` on the current branch's GitHub PR to trigger a preview deployment, then uses the `/loop` skill to poll for the deployed environment URL.

## Steps

1. **Detect platform:** Check if `git remote -v` contains `github.com`. This skill is GitHub-only.
2. **Find the PR:** Run `gh pr view --json number,url,headRefName` to get the PR number and URL for the current branch.
   - If no PR exists, inform the user and stop.
3. **Record timestamp:** Capture the current UTC time before commenting (used to filter new comments later).
4. **Comment `/deploy`:** Run `gh pr comment <number> --body "/deploy"`
5. **Confirm:** Tell the user the deploy was triggered and that you will monitor for the preview URL.
6. **Poll for deploy URL using `/loop`:** Invoke the `loop` skill with interval `5m` and a prompt that:
   - Fetches PR comments created after the recorded timestamp using:
     ```
     gh api repos/{owner}/{repo}/issues/{number}/comments --jq '[.[] | select(.created_at > "TIMESTAMP") | select(.body | test("https?://")) | .body] | last'
     ```
   - If a URL is found, shares it with the user and cancels the cron job via CronDelete.
   - If no URL yet, says "No deploy URL yet."

## Quick Reference

| Task | Command |
|------|---------|
| Check current PR | `gh pr view --json number,url` |
| Comment /deploy | `gh pr comment <number> --body "/deploy"` |
| Fetch new PR comments | `gh api repos/{owner}/{repo}/issues/{number}/comments --jq '...'` |
| View PR in browser | `gh pr view --web` |

## Common Mistakes

- Running without a PR open for the current branch
- Forgetting to switch GitHub account first (if using multiple accounts)
- Using manual polling instead of the `/loop` skill
