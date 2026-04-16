---
name: python-project-setup
description: Use when creating a new Python project, initializing a Python repo, or setting up Python tooling — covers uv, ruff, pyright, pytest, project structure, and CI configuration.
---

# Python Project Setup

## Overview

Standard Python project setup using uv (package manager + virtualenv), ruff (linter + formatter), pyright (type checker), and pytest (testing). All tool configs live in `pyproject.toml`. Source code in `src/`, tests in `tests/`.

## Prerequisites

Requires `uv`. If it's not installed, point the user to `SETUP.md` at the plugin root (section: **python-project-setup**) and stop until it's available.

## When to Use

- Creating a new Python project from scratch
- Setting up tooling for an existing Python project
- Adding CI to a Python project
- When the user says "create python project", "new python project", "setup python project", "init python project"

## Project Structure

```
project-name/
  src/
    __init__.py
    main.py
  tests/
    __init__.py
    conftest.py
  config/              # YAML configs (if needed)
  scripts/             # Utility scripts
  .env.example
  .env                 # (gitignored)
  .python-version
  pyproject.toml
  .claude/
    settings.json      # Claude Code hooks (lint + type check on edit)
  CLAUDE.md
  .gitignore
```

## Quick Reference

| Task | Command |
|------|---------|
| Initialize project | `uv init` |
| Install deps | `uv sync --all-extras` |
| Add dependency | `uv add <package>` |
| Add dev dependency | `uv add --optional dev <package>` |
| Run app | `uv run python -m src.main` |
| Lint | `uv run ruff check src tests` |
| Format | `uv run ruff format src tests` |
| Type check | `uv run pyright src` |
| Test | `uv run pytest` |
| Test with coverage | `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80` |

## Setup Steps

### 1. Initialize

```bash
uv init project-name
cd project-name
echo "3.11" > .python-version
```

Use whichever Python version the project targets — `3.11` is a safe default.

### 2. Add Dev Dependencies

```bash
uv add --optional dev pytest pytest-cov pytest-asyncio pyright ruff
```

Drop `pytest-asyncio` if the project is purely synchronous.

### 3. Create Structure

```bash
mkdir -p src tests config scripts
touch src/__init__.py tests/__init__.py tests/conftest.py
```

### 4. Configure pyproject.toml

Add these tool sections (adjust `project-name`, Python version, and dependencies as needed):

```toml
[project]
name = "project-name"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.23",
    "pyright>=1.1",
    "ruff>=0.1",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "basic"
include = ["src"]
exclude = ["tests", ".venv"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",       # pycodestyle errors
    "W",       # pycodestyle warnings
    "F",       # pyflakes
    "I",       # isort
    "B",       # flake8-bugbear
    "C4",      # flake8-comprehensions
    "UP",      # pyupgrade
    "PLC0415", # import-outside-toplevel
]
ignore = [
    "E501",    # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["src"]
```

### 5. Create .gitignore

```
__pycache__/
*.py[cod]
.venv/
.env
*.egg-info/
dist/
build/
.pytest_cache/
.pyright/
.ruff_cache/
coverage.xml
htmlcov/
```

### 6. Create .env.example

Document all required and optional environment variables with placeholder values. Never commit `.env` itself.

### 7. Set Up CI

Create `.github/workflows/ci.yaml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run linting
        run: uv run ruff check src tests

      - name: Run type checking
        run: uv run pyright src

      - name: Run tests with coverage
        run: uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

For GitLab, the equivalent `.gitlab-ci.yml` runs the same four commands (`uv sync --all-extras`, `uv run ruff check src tests`, `uv run pyright src`, `uv run pytest ...`) inside a `python:3.11` image after installing uv.

### 8. Set Up Claude Code Hooks

Create `.claude/settings.json` to auto-run the linter and type checker after every file edit:

```bash
mkdir -p .claude
```

Write `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "FILE=$(jq -r '.tool_input.file_path // .tool_input.filePath // empty' < /dev/stdin) && [[ \"$FILE\" == *.py ]] && PROJECT_ROOT=$(cd \"$(dirname \"$FILE\")\" && git rev-parse --show-toplevel 2>/dev/null || echo .) && cd \"$PROJECT_ROOT\" && uv run ruff check \"$FILE\" && uv run pyright \"$FILE\" || true"
          }
        ]
      }
    ]
  }
}
```

This hook:

- Triggers after every `Edit` or `Write` tool call
- Only runs on `.py` files
- Detects the git root dynamically (works in worktrees too)
- Runs `ruff check` and `pyright` on the edited file
- Uses `|| true` so lint/type errors are reported but don't block edits

## Code Conventions

| Convention | Rule |
|-----------|------|
| String quotes | Double quotes always |
| Line length | 100 characters |
| Imports | All at top of file, never inline (enforced by PLC0415) |
| Fixed values | Use `Enum` types, never raw strings with comments |
| Import order | stdlib -> third-party -> first-party (enforced by isort) |
| Dependencies | Use latest stable versions unless pinned for a reason |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using pip/poetry instead of uv | Always use `uv` for this setup |
| Configs in separate files (`.flake8`, `setup.cfg`) | All config in `pyproject.toml` |
| Using `npm run` patterns | Use `uv run` prefix for all commands |
| Single quotes for strings | Double quotes (ruff will catch this) |
| Inline imports in functions | Move to top of file (PLC0415 enforces) |
| Raw strings for fixed values | Create `Enum` types instead |
| Missing `--all-extras` on install | Always use `uv sync --all-extras` to get dev deps |
