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

### commit-push-pr

Requires `git` plus a host CLI matching the remote:

- **GitHub remotes** → `gh` (see the **babysit-pr** section above for install + auth).
- **GitLab remotes** → `glab` (see the **glab-cli** section above).

### python-project-setup

Requires `uv` (Python package manager + virtualenv):

```bash
# macOS / Linux installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```

### convert-date

Requires Python 3 with the `jdatetime` package:

```bash
pip install jdatetime
# or, if you use uv:
uv pip install jdatetime
```

Verify: `python3 -c "import jdatetime; print(jdatetime.date.today())"`.

### fetch-raindrop-bookmarks

Requires a Raindrop.io API token:

1. Open https://app.raindrop.io/settings/integrations
2. Under "For Developers", click **Create new app** (any name), open it, then click **Create test token**.
3. Copy the token and export it:

   ```bash
   export RAINDROP_API_TOKEN="<your token>"
   ```

   Add it to your shell profile (`~/.zshrc` / `~/.bashrc`) so it persists.

   Alternatively, store it in `${CLAUDE_PLUGIN_DATA}/preferences/fetch-raindrop-bookmarks.md` under `raindrop_api_token` (less secure — env var is preferred).

4. Pick a collection ID and put it in the same preferences file under `collection_id`. Use `0` for "Unsorted", `-1` for "All".

### fetch-twitter-bookmarks

Requires the `bird` CLI (see the **bird-cli** section above for install + auth). Optional: install `yt-dlp` (`brew install yt-dlp`) if you want the skill to download tweet videos when `download_media=true`.
