---
name: discuss-comments
description: "Use when the user wants to find PR review comments where they were @-mentioned (often self-authored questions left inline in the GitHub UI while reading a diff) and reply to each one directly on GitHub, in italics. Triggers on \"reply to my PR comments\", \"answer my review comments\", \"check comments mentioning me\", \"discuss comments\", or explicit /discuss-comments [PR number|URL]. GitHub only (no GitLab/glab support yet)."
argument-hint: "[PR number|URL] (optional, auto-detects from the current branch if omitted)"
---

# Discuss Comments

Find PR comments/questions that @-mention the caller, answer each one from an actual read of the referenced code (never guess from the question text alone), and post the reply as a threaded reply in italics.

Typical use: the user reads a diff in the browser, leaves themselves a few inline questions tagged with their own handle, then asks Claude to answer them in-thread.

## Prerequisites

Requires the `gh` CLI, authenticated. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **babysit-pr**) and stop until it's available.

## Step 0: Resolve the target PR

1. If `$ARGUMENTS` is a full PR URL, extract `owner/repo` and the PR number from it.
2. If `$ARGUMENTS` is a bare number, resolve `owner/repo` from the current directory's git remote (`git remote get-url origin`).
3. If `$ARGUMENTS` is empty, auto-detect from the current branch: `gh pr view --json number,url` (run from inside the repo, on the PR's branch).
4. **GitHub only.** If the resolved remote is GitLab, stop and tell the user this skill doesn't support `glab`/GitLab MRs yet.

## Step 1: Resolve the handle

```bash
gh api user --jq .login
```

If the user has several GitHub accounts, make sure the active one is the one that owns the repo (check the repo's CLAUDE.md for account-switching conventions such as `direnv` or `gh auth switch`). A wrong account usually returns empty results rather than an error.

## Step 2: Fetch every comment that mentions the caller

Pull from all three comment surfaces; a self-mention can land in any of them:

```bash
# Inline (diff) review comments
gh api repos/<owner>/<repo>/pulls/<number>/comments --paginate \
  --jq '.[] | select(.body | test("@<handle>"; "i"))'

# Top-level PR/issue conversation comments
gh api repos/<owner>/<repo>/issues/<number>/comments --paginate \
  --jq '.[] | select(.body | test("@<handle>"; "i"))'

# Review summary bodies
gh api repos/<owner>/<repo>/pulls/<number>/reviews \
  --jq '.[] | select(.body | test("@<handle>"; "i"))'
```

## Step 3: Filter to what still needs an answer

Fetch the PR's review threads via GraphQL. This gives resolved status and the full comment list per thread in one call:

```graphql
query {
  repository(owner: "<owner>", name: "<repo>") {
    pullRequest(number: <number>) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 20) { nodes { id body path } }
        }
      }
    }
  }
}
```

Skip a comment if any of these are true:
- It is itself a reply (`in_reply_to_id` is set). Only answer root questions.
- Its thread already contains a reply authored by the caller's handle after the mention.
- Its review thread is already `isResolved: true`.

For top-level (non-inline) conversation comments there's no thread/resolved concept; skip only if a later comment from the caller's handle already responds to it.

## Step 4: Understand each question before answering, never guess

For every comment that survives the filter:
1. Note its `path`, `line`, and `diff_hunk` (inline comments) from `gh api repos/<owner>/<repo>/pulls/comments/<comment_id>`.
2. If the `diff_hunk` isn't enough to answer confidently, read the actual file at that path on the PR's branch: from the current checkout if it is on that branch, otherwise `gh api repos/<owner>/<repo>/contents/<path>?ref=<branch>` or `gh pr diff <number>`.
3. Ground the answer in what the code actually does; cite the specific mechanism. If the code genuinely doesn't make the answer clear, say so plainly in the reply instead of fabricating one.

## Step 5: Draft the reply: italics, tight, factual

- Wrap the entire reply body in a single pair of `*...*` (GitHub markdown italics). Inline code spans still render fine nested inside italics.
- A few sentences: answer the question, cite the concrete reason, stop.
- No praise or pleasantries; this is a technical answer, not a review verdict.

## Step 6: Post the reply

```bash
# Inline (threaded) reply
gh api --method POST repos/<owner>/<repo>/pulls/<number>/comments \
  -F in_reply_to=<comment_id> \
  -f body="*...*"

# Top-level conversation comment (no native reply, so @-mention the original asker)
gh api --method POST repos/<owner>/<repo>/issues/<number>/comments \
  -f body="*@<original-commenter> ...*"
```

## Step 7: Report back, and stop there

List what was answered: for each comment, its file/line (or "general comment"), a one-line summary of the question and the answer given, and the comment's `html_url`.

**Do not automatically** resolve the review threads, approve or request changes on the PR, or update any linked issue/task tracker. These are separate, higher-impact actions: offer them as a next step, act only on explicit instruction.

## Common mistakes

| Mistake | Fix |
|---|---|
| Answering from the question text alone | Always read the referenced code first; the diff hunk is often too short to be sure. |
| Replying to a comment that's already resolved or answered | Cross-check via the GraphQL `reviewThreads` query (Step 3) before drafting. |
| Posting from the wrong GitHub account | Confirm the active `gh` account in Step 1; empty results are the usual symptom. |
| Mixing italics with headers or bullet lists | Keep the reply to a plain italicised paragraph; heavy formatting inside `*...*` renders oddly. |
| Auto-resolving threads or approving the PR | Out of scope; separate asks, not implied by "reply to my comments". |
