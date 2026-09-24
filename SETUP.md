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

### snow-cli

Requires the Snowflake CLI:

```bash
brew install snowflake-cli
```

Configure a connection (JWT with an RSA key pair is recommended for automation):

```bash
snow connection add
snow connection test -c <name>
```

Snowflake's docs cover RSA key-pair setup: <https://docs.snowflake.com/en/user-guide/key-pair-auth>.

After the connection exists, set `default_connection` in `${CLAUDE_PLUGIN_DATA}/preferences/snow-cli.md` so the skill doesn't need an explicit `-c` flag each invocation.

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

### summarize-content

Requires the `summarize` CLI (<https://summarize.sh>, MIT):

```bash
brew install summarize
summarize --help
```

It calls an LLM provider for the summary step; configure a provider key as described in its docs.

### make-slides

Requires `git`. On first run the skill clones the MIT-licensed [beautiful-html-templates](https://github.com/zarazhangrui/beautiful-html-templates) library into `${CLAUDE_PLUGIN_DATA}/beautiful-html-templates` (override with `templates_dir` in `${CLAUDE_PLUGIN_DATA}/preferences/make-slides.md`).

### generate-image

Requires Python 3 (stdlib only) plus an API key for at least one provider, exported in your shell profile or a secrets manager:

```bash
export OPENAI_API_KEY="<key>"   # default provider, https://platform.openai.com/api-keys
export GEMINI_API_KEY="<key>"   # optional, https://aistudio.google.com/apikey (image models need billing enabled)
```

`gpt-image-2` additionally requires OpenAI organisation verification; the skill falls back to `gpt-image-1.5` without it.

### md-to-pdf

Requires `pandoc`, Google Chrome or Chromium, and Python 3:

```bash
brew install pandoc            # macOS
sudo apt install pandoc chromium   # Debian/Ubuntu
```

If the browser isn't on `PATH` or at the default macOS location, export `CHROME_PATH=/path/to/chrome`.

### cut-clip

Requires `yt-dlp`, `ffmpeg` (includes `ffprobe`), `curl`, and Python 3:

```bash
brew install yt-dlp ffmpeg
```

Transcription uses ElevenLabs Scribe. Create a key at <https://elevenlabs.io/app/settings/api-keys> and either export it:

```bash
export ELEVENLABS_API_KEY="<key>"
```

or save it to `~/.config/elevenlabs/api_key` (`chmod 600`; override the location with `ELEVENLABS_API_KEY_FILE`).

### find-session

Requires Python 3 (standard library only, no packages). Most macOS and Linux systems ship it; otherwise `brew install python` or your distro's package.

Verify: `python3 --version`.

### new-session

Uses the Claude Code CLI itself. Background launch needs a version that supports `claude --bg` (check `claude --help`); on older versions set `dispatch_mode: print` in `${CLAUDE_PLUGIN_DATA}/preferences/new-session.md` to get a command to run yourself.

### integrate-cli

Generated permission hooks parse tool input with `jq`:

```bash
brew install jq
```

The CLI being integrated is installed by the skill itself, using that tool's own package manager (`brew`, `npm`, `pipx`, `cargo`).

### helpers

The helper scripts are stdlib-only Python 3. `adherence-probe.py` additionally needs the `claude` CLI on `PATH` (it runs `claude -p` for each probe), logged in as usual.

User data for the scripts (your probes and contracts) lives in the plugin data dir, `${CLAUDE_PLUGIN_DATA}`, so it survives plugin updates. The first time you run `adherence-probe.py` or `skill-contracts.py` without that file, the script prints the exact path it expects and the bundled example to copy from (`probes.example.json`, `skill-contracts.example.json`). Copy it there, then replace the example entries with probes and contracts for your own rules. Either script also accepts an explicit path (`--probes` / `--file`).
