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

Requires the `bird` CLI. Once the `bird-cli` skill is installed in this plugin, follow its **bird-cli** section above (added by the `skill/cli-wrappers` PR) for install + auth. Optional: install `yt-dlp` (`brew install yt-dlp`) if you want the skill to download tweet videos when `download_media=true`.
