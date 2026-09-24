---
name: gemini-cli
description: Use when interacting with Google Gemini — asking Gemini questions, getting a second opinion, generating content (text, SVG infographics, outlines), or managing Gemini CLI extensions/MCP servers. Triggers on "ask gemini", "gemini opinion", "run gemini", "second opinion from gemini", "gemini infographic", "call gemini".
model: sonnet
---

# Google Gemini with gemini CLI

## Prerequisites

Requires the `gemini` CLI and a `GEMINI_API_KEY`. If it's not installed or the key is unset, point the user to `SETUP.md` at the plugin root (section: **gemini-cli**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/gemini-cli.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/gemini-cli/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/gemini-cli.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/gemini-cli.md` — edit anytime to customize."
2. Read it. When `default_model` is set, pass `-m <value>` on every prompt call. When `quality_model` is set, use it for prose, reasoning, non-English writing and creative work. Empty fields mean "pick from the live model list" (see Models).

## Auth

The CLI reads `GEMINI_API_KEY` from the environment (no interactive login is needed for API-key auth). Verify:

```bash
gemini -p "say hello in one word" --output-format json
```

## Quick Reference

| Task | Command |
|------|---------|
| Ask Gemini a question (JSON) | `gemini -p "your question" --output-format json` |
| Ask with a specific model | `gemini -p "your prompt" -m <model> --output-format json` |
| Pipe content to Gemini | `cat file.md \| gemini -p "summarize this" --output-format json` |
| Generate SVG infographic | `gemini -p "create an SVG infographic about X" --output-format json` |
| Agentic task (auto-approve) | `gemini -p "refactor main.py" -y --output-format json` |
| Stream JSON output | `gemini -p "explain this" --output-format stream-json` |
| List MCP servers | `gemini mcp list` |
| Add MCP server | `gemini mcp add myserver npx my-mcp-server` |
| List extensions | `gemini extensions list` |
| List installed skills | `gemini skills list` |
| List sessions | `gemini --list-sessions` |
| Resume last session | `gemini --resume latest` |
| Load session from file | `gemini --session-file path/to/session.json` |
| Start session with custom UUID | `gemini --session-id <uuid>` |
| Local Gemma routing status | `gemini gemma status` |
| Check version | `gemini --version` |

## Extracting the Response

`--output-format json` returns an envelope:

```json
{
  "session_id": "...",
  "response": "the actual answer",
  "stats": { "models": {...}, "tools": {...}, "files": {...} }
}
```

```bash
gemini -p "your question" --output-format json | python3 -c "import sys,json; print(json.load(sys.stdin)['response'])"
```

## Read vs Write Operations

**Safe (no confirmation needed):** `--version`, `--help`, `--list-extensions`, `--list-sessions`, headless `-p` prompts without `-y`

**Read:** `mcp list`, `extensions list`, `skills list`, `gemma status`, `gemma logs`

**Write (the bundled permission hook prompts):** `mcp add/remove/enable/disable`, `extensions install/uninstall/update/enable/disable/link/new/validate/config`, `skills enable/disable/install/link/uninstall`, `gemma setup/start/stop`, `hooks migrate`, `--delete-session`, `--skip-trust` (bypasses workspace trust confirmation), `-y` / `--approval-mode yolo` (auto-approves all file writes and shell commands)

## Models

Model IDs change often, and the CLI's built-in default is usually a fast "flash" tier that is weaker at prose. **Verify what the key actually exposes before assuming a model ID:**

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY" | jq -r '.models[].name'
```

Rule of thumb: use the newest **pro** tier for prose, reasoning, non-English writing and creative work; use a **flash** tier for quick throwaway lookups. Pass `-m` explicitly for anything that is not a throwaway lookup.

## Headless / Non-Interactive Mode

Non-interactive mode activates when `-p/--prompt` is given or stdin is not a TTY. Key flags:

- `-p "prompt"` — headless mode, required for scripting
- `--output-format json` / `stream-json` — parseable output
- `-y/--yolo`, `--approval-mode yolo` — auto-approve all tool/file/shell actions (use carefully)
- `-m/--model` — specify model
- `--include-directories path1,path2` — add extra dirs to context

## MCP, Extensions & Skills

```bash
gemini mcp list | add <name> <cmd...> | remove <name> | enable <name> | disable <name>
gemini extensions list | install <github-url> | uninstall <name>
gemini skills list | install <github-url>
gemini hooks migrate   # migrate hooks from Claude Code to Gemini CLI
```

## Local Gemma Model Routing

Runs Gemma locally via a LiteRT-LM server so the CLI can route prompts to an on-device model.

```bash
gemini gemma setup    # write: downloads model weights
gemini gemma start    # write: spawns a long-running local server
gemini gemma stop     # write
gemini gemma status   # read
gemini gemma logs     # read
```

## Sessions

```bash
gemini --session-file path/to/session.json -p "continue the conversation"
gemini --session-id 550e8400-e29b-41d4-a716-446655440000 -p "your prompt"
```

Use `--session-id` for deterministic session ids in scripts (so a later `--resume <id>` is predictable).

## Workspace Trust

`--skip-trust` skips the workspace-trust confirmation shown before running tools in a new directory. Treat it as a write; only use it when the workspace is known-safe.

**Headless runs fail outside a trusted directory, and the failure looks like success.** Without `--skip-trust`, `gemini -p` in an untrusted dir exits with `Gemini CLI is not running in a trusted directory`, writes **zero bytes** to stdout, and puts the error only on stderr. A script that redirects stdout to a file sees an empty result with no explanation. Either pass `--skip-trust` for a known-safe scratch dir or export `GEMINI_CLI_TRUST_WORKSPACE=true`, and always capture stderr too.

## Behavioral Rules

- Match the user's language.
- Always use `--output-format json` when calling from scripts so the response is parseable.
- Never use `-y/--yolo` or `--skip-trust` without an explicit user request.
- For creative tasks and any prose or non-English writing, pass the pro-tier model (`quality_model` preference) explicitly; never let it fall through to the flash default.
- **Non-English prose:** Gemini tends toward a formal register. Spell out the register you want (casual vs formal) in the prompt, or it may slip mid-message.
- Treat Gemini's answer as a second opinion, not ground truth; verify factual claims before relaying them.

## Self-Update

```bash
npm i -g @google/gemini-cli@latest
gemini --version
```

After upgrading, run `/cortex:update-cli gemini` to keep this skill and the permission hook in sync with new commands.
