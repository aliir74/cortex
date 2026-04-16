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

### slack-cli

Requires the [`agent-slack`](https://github.com/stablyai/agent-slack) CLI.

```bash
# Recommended (Bun-based installer):
curl -fsSL https://raw.githubusercontent.com/stablyai/agent-slack/main/install.sh | sh

# Or via npm (Node >= 22.5):
npm i -g agent-slack
```

Authenticate (on macOS/Windows, Slack Desktop data is read automatically):

```bash
agent-slack auth whoami
# Fallbacks if needed:
agent-slack auth import-desktop
agent-slack auth import-chrome
```

### bird-cli

Requires the `bird` CLI for X/Twitter. Install via Bun:

```bash
bun install -g bird
```

Verify auth:

```bash
bird whoami
```

If `bird` is configured for explicit credentials (`cookieSource: []` in
`~/.config/bird/config.json5`), populate `~/.config/bird/accounts.json`
with `ct0` and `auth_token` per account.

### tgcli

Requires the `tgcli` CLI:

```bash
brew install kfastov/tap/tgcli
```

First-time setup needs API credentials from <https://my.telegram.org/apps>:

```bash
tgcli auth
tgcli doctor
```

### glab-cli

Requires the GitLab CLI:

```bash
brew install glab
glab auth login
```

For self-hosted GitLab, point the CLI at the right host:

```bash
glab config set -g host gitlab.example.com
```
