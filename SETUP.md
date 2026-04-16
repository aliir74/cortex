# Setup Guide

## Plugin Installation

```bash
claude plugin marketplace add aliir74/cortex
claude plugin install cortex
```

## Skill-Specific Prerequisites

### babysit-pr

Requires the GitHub CLI:

```bash
brew install gh
gh auth login
```

### clickup-cli

Requires the ClickUp CLI ([source](https://github.com/triptechtravel/clickup-cli)):

```bash
brew install triptechtravel/tap/clickup
```

Authenticate: `clickup auth login`

### gws-cli

Requires the Google Workspace CLI:

```bash
npm install -g @googleworkspace/cli
gws auth login
```

### codex-ask

Requires the OpenAI Codex CLI:

```bash
npm install -g @openai/codex
codex login
```

### commit-push-pr

Requires `git` plus a host CLI matching the remote:

- **GitHub remotes** -> `gh` (see the **babysit-pr** section above for install + auth).
- **GitLab remotes** -> `glab`:

```bash
brew install glab
glab auth login
```

### python-project-setup

Requires `uv` (Python package manager + virtualenv):

```bash
# macOS / Linux installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```
