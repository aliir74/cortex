---
name: codex-ask
description: Use when user wants a second opinion from Codex/GPT, wants to ask Codex a question, pass custom context to Codex, or says "ask codex", "codex opinion", "run codex", "second opinion", "/codex-ask"
disable-model-invocation: true
argument-hint: [--files file1,file2] [--write] [--model name] <prompt>
---

# Codex Ask

Send arbitrary prompts and context to OpenAI Codex CLI (`codex exec`) from Claude Code. No MCP, no git dependency — just direct CLI.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/codex-ask.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/codex-ask/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/codex-ask.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/codex-ask.md` — edit anytime to customize."
2. Read it. Use `default_model` when the user does not pass `--model`, `default_effort` when they do not pass `--effort`, `default_timeout_ms` as the Bash call timeout, and `result_file` for the `-o` output path. Empty fields mean "use the default documented below."

## Usage

```
/codex-ask <prompt>
/codex-ask --files file1.py,file2.md <prompt>
/codex-ask --write <prompt>
/codex-ask --model o3 <prompt>
```

## Argument Parsing

Parse the user's arguments:

| Flag | Meaning | Default |
|------|---------|---------|
| `--files <paths>` | Comma-separated file paths to include as context | none |
| `--write` | Allow Codex to edit files (workspace-write sandbox) | read-only |
| `--model <name>` | Override Codex model | gpt-5.4 |
| `--effort <level>` | Reasoning effort: none, minimal, low, medium, high, xhigh | (codex default) |
| `--background` | Run in background, don't wait for result | foreground |
| Everything else | The prompt text for Codex | (required) |

If no `--files` flag but the user mentions specific files in their message, read those files and include them as context.

## Execution

### Build the command

Base command:
```bash
codex exec "<prompt>" --full-auto --skip-git-repo-check -o /tmp/codex-ask-result.md
```

Add flags as needed:
- `--write` user flag -> use `-s workspace-write`
- `--model` -> add `-m <model>`
- Read-only (default, no `--write`) -> add `-s read-only` to override `--full-auto`'s default

### Include context files

If `--files` is specified or the user references files, concatenate their contents and pipe to stdin:
```bash
cat file1.py file2.md | codex exec "<prompt>" --full-auto --skip-git-repo-check -o /tmp/codex-ask-result.md
```

### Read and present result

After execution:
1. Read `/tmp/codex-ask-result.md`
2. Present Codex's response inline, clearly labeled:

```
**Codex says:**

<result content>
```

3. If Codex made file changes (`--write` mode), run `git diff` to show what changed.

## Common Patterns

**Quick second opinion:**
```
/codex-ask Is this the right approach for handling auth tokens in this codebase?
```

**Review specific files:**
```
/codex-ask --files src/auth.py,src/middleware.py Review these for security issues
```

**Let Codex edit:**
```
/codex-ask --write Refactor the error handling in src/api/handlers.ts
```

## Error Handling

- If `codex` is not installed: tell user to run `npm install -g @openai/codex`
- If not authenticated: tell user to run `codex login`
- If command fails: show stderr output
- Timeout: 5 minutes max (`--timeout 300000` on the Bash call)
