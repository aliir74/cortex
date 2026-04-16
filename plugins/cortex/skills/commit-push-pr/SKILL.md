---
name: commit-push-pr
description: "Use when user explicitly asks to commit, push, and open a PR/MR in one step. Triggers on 'commit and push', 'create PR', 'ship it', '/commit-push-pr'. Auto-detects GitHub vs GitLab from the remote and uses the matching CLI."
disable-model-invocation: true
---

# Commit, Push, PR/MR

Stage changes, commit them, push the current branch, and open a pull/merge request — all in one flow. Auto-detects the remote host (GitHub or GitLab) and uses the matching CLI.

## Prerequisites

Requires `git` plus the host CLI:

- **GitHub remotes** -> `gh`. If missing, point the user to `SETUP.md` at the plugin root (section: **babysit-pr** — same `gh` install) and stop until it's available.
- **GitLab remotes** -> `glab`. If missing, ask the user to install it (`brew install glab` on macOS, then `glab auth login`) and stop until it's available.

Both CLIs must be authenticated before this skill can push or open the PR/MR.

## Safety Rules

- **Never merge the PR/MR.** Merging is the human reviewer's call. This skill stops after the PR/MR is opened.
- **Never use `--no-verify`** on commit or push unless the user explicitly asks. If a hook fails, surface the error and let the user decide.
- **Never force-push** (`--force`, `--force-with-lease`) unless the user explicitly asks.
- **Do not stage secrets.** If `git status` shows files that look like credentials (`.env`, `*.pem`, `id_rsa`, `credentials.json`, `*.key`), warn the user and ask before staging.
- **Do not bypass GPG signing** (`--no-gpg-sign`) unless the user explicitly asks.

## Step-by-Step Flow

### 1. Inspect the working tree

Run in parallel:

```bash
git status
git diff
git diff --staged
git log -5 --oneline
git remote get-url origin
git branch --show-current
```

- If there are no changes (staged or unstaged) and no untracked files, stop and tell the user there's nothing to commit.
- If the current branch is `main`/`master`/`develop`, ask the user whether to create a feature branch first — never push commits straight to a protected branch unless they confirm.

### 2. Detect the host

Parse the `origin` URL:

- Contains `github.com` -> use `gh`.
- Contains `gitlab.com` or a self-hosted GitLab host -> use `glab`.
- Anything else -> ask the user which CLI to use.

### 3. Read repo conventions

Before drafting the commit message, look for repo-specific guidance:

1. Read the repo's `CLAUDE.md` (root and any nested ones touching the changed files) for commit style rules — message casing, length limits, prefix conventions (e.g., Conventional Commits), trailers.
2. Read recent commits (`git log -10 --pretty=format:"%s"`) to match the existing style if `CLAUDE.md` is silent.
3. Check `.gitmessage`, `CONTRIBUTING.md`, and `.github/PULL_REQUEST_TEMPLATE.md` (or `.gitlab/merge_request_templates/`) for additional conventions.

If no guidance exists, default to a short imperative subject (~50 chars) and a body that explains the *why*.

### 4. Stage changes

- If the user named specific files, stage only those: `git add <paths>`.
- Otherwise, list the modified/untracked files and ask which to include. Avoid `git add -A` / `git add .` unless the user explicitly OKs it — those can sweep in unintended files.

### 5. Commit

Build the message from the diff:

- Subject: imperative, short, follows the repo's casing convention.
- Body (if non-trivial change): explain motivation, not the diff itself.
- Honor any trailer conventions found in `CLAUDE.md` or recent commits (e.g., `Signed-off-by`, ticket refs, `Co-Authored-By`).

Pass via heredoc to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
<subject>

<body>
EOF
)"
```

If a pre-commit hook fails, do **not** `--amend` or retry with `--no-verify`. Fix the issue, re-stage, and create a new commit.

### 6. Push

```bash
git push -u origin "$(git branch --show-current)"
```

If the branch already tracks a remote, a plain `git push` is fine.

### 7. Open the PR/MR

Look for a PR/MR template in the repo (`.github/PULL_REQUEST_TEMPLATE.md`, `.gitlab/merge_request_templates/*.md`) and follow it if present.

**GitHub:**

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <how to verify>
EOF
)"
```

**GitLab:**

```bash
glab mr create --title "<title>" --description "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Test plan
- [ ] <how to verify>
EOF
)" --squash-before-merge --remove-source-branch
```

For GitLab MRs, `--squash-before-merge` and `--remove-source-branch` match the common convention of squashing on merge and cleaning up the source branch — drop them if the repo's CONTRIBUTING.md says otherwise.

### 8. Report back

Print the PR/MR URL and stop. Do not run a merge command.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Pushing to `main`/`master` without asking | Confirm or branch first |
| Staging everything with `git add -A` | Stage named files only |
| `--amend` after a hook failure | Fix the issue, create a new commit |
| `--no-verify` to skip a failing hook | Diagnose the hook, only bypass if user confirms |
| Hardcoding commit style across repos | Defer to the repo's `CLAUDE.md` / `CONTRIBUTING.md` |
| Merging the PR/MR after creation | Stop at PR/MR creation — merging is the reviewer's call |
| Force-pushing without asking | Never; ask first |
