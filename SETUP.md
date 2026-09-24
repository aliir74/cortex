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

### exa-cli

The `exa` wrapper ships inside the skill and runs the `exa-py` SDK through `uv`, so it needs `uv` (see the **python-project-setup** section above) and an Exa API key.

1. Create a key at <https://dashboard.exa.ai>.
2. Store it in a private env file that the wrapper sources automatically when `EXA_API_KEY` is unset:

   ```bash
   echo 'export EXA_API_KEY="<your key>"' > ~/.exa.env && chmod 600 ~/.exa.env
   ```

Exporting `EXA_API_KEY` in your environment works too and takes precedence.

### figma-cli

The `figma` wrapper ships inside the skill (stdlib-only Python 3, read-only). It needs a Figma personal access token:

1. Figma → Settings → Security → Personal access tokens → generate one with **File content: Read** scope.
2. Store it:

   ```bash
   echo 'FIGMA_TOKEN=<your token>' > ~/.figma.env && chmod 600 ~/.figma.env
   ```

`$FIGMA_TOKEN` in the environment overrides the file. Verify: `"${CLAUDE_PLUGIN_ROOT}/skills/figma-cli/figma" whoami` from inside Claude Code.

### gemini-cli

Requires the Google Gemini CLI ([source](https://github.com/google-gemini/gemini-cli)):

```bash
npm install -g @google/gemini-cli
# or: brew install gemini-cli
```

Create an API key at <https://aistudio.google.com/apikey> and export it as `GEMINI_API_KEY`, ideally from a `chmod 600` env file your shell sources rather than inline in `~/.zshrc`. Verify:

```bash
gemini -p "say hello in one word" --output-format json
```

### imsg-cli

macOS only. Requires the `imsg` CLI ([source](https://github.com/steipete/imsg)):

```bash
brew install steipete/tap/imsg
```

Grant **Full Disk Access** to the terminal app that runs Claude Code (System Settings → Privacy & Security → Full Disk Access), and make sure Messages.app is signed in. Verify: `imsg chats --limit 3 --json`.

### ntn-cli

Requires Notion's official `ntn` CLI:

```bash
brew install --cask notion-cli
# or: curl -fsSL https://ntn.dev | bash
```

Authenticate with either:

- **Integration token (recommended):** create an internal integration at <https://www.notion.so/profile/integrations>, connect it to the pages you want it to see, then export its secret as `NOTION_API_TOKEN` (for example from a `chmod 600` `~/.notion.env` your shell sources).
- **OAuth:** `ntn login` (required for `ntn workers *`).

Verify: `ntn whoami` or `ntn doctor`.

### signal-cli

Requires [signal-cli](https://github.com/AsamK/signal-cli) (Java-based) and `qrencode` for the device-linking QR:

```bash
brew install signal-cli qrencode
```

Link it to your existing account as a secondary device (the skill walks through this): `signal-cli link -n "claude-code"`, then scan the QR from Signal → Settings → Linked Devices. Verify: `signal-cli listAccounts`.

### stripe-cli

Requires the Stripe CLI ([docs](https://docs.stripe.com/stripe-cli)):

```bash
brew install stripe/stripe-cli/stripe
stripe login
```

Verify: `stripe whoami --format json`. The bundled hook blocks live mode, so use test-mode keys only.

### unleash-cli

The `unleash` wrapper ships inside the skill (stdlib-only Python 3, calls the Unleash Admin API). It needs a **personal access token** or **service account token** (an SDK client token will not work against `/api/admin`). Create one in the Unleash UI under **Profile → Personal API tokens**, then:

```bash
cat > ~/.unleash.env <<'ENV'
UNLEASH_URL=https://<your-unleash-host>
UNLEASH_PAT=<your token>
ENV
chmod 600 ~/.unleash.env
```

Add more instances as `UNLEASH_URL_<NAME>` / `UNLEASH_PAT_<NAME>` and select them with `--profile <name>` (or `default_profile` in `${CLAUDE_PLUGIN_DATA}/preferences/unleash-cli.md`).

### elevenlabs-voice

The `transcribe.sh` and `tts.sh` helpers ship inside the skill and need `curl`, `jq` and `python3` plus an ElevenLabs API key:

1. Create a key at <https://elevenlabs.io/app/settings/api-keys> (needs speech-to-text and text-to-speech access).
2. Either export it as `ELEVENLABS_API_KEY`, or store it in a key file:

   ```bash
   mkdir -p ~/.config/elevenlabs
   printf '%s' '<your key>' > ~/.config/elevenlabs/api_key && chmod 600 ~/.config/elevenlabs/api_key
   ```

Set `api_key_file` in `${CLAUDE_PLUGIN_DATA}/preferences/elevenlabs-voice.md` to use a different path.

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
