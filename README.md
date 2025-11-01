<!-- markdownlint-disable MD013 -->

# 🐾 kittylog

[![PyPI version](https://img.shields.io/pypi/v/kittylog.svg)](https://pypi.org/project/kittylog/)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12%20|%203.13-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://github.com/cellwebb/kittylog/actions/workflows/ci.yml/badge.svg)](https://github.com/cellwebb/kittylog/actions)
[![codecov](https://codecov.io/gh/cellwebb/kittylog/branch/main/graph/badge.svg)](https://app.codecov.io/gh/cellwebb/kittylog)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-checked-blue.svg)](https://mypy-lang.org/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
**LLM-powered changelog generation from git tags and commits.** Automatically analyzes your repository history to create well-structured changelog entries following the [Keep a Changelog](https://keepachangelog.com/) format.

---

## What You Get

Accurate, categorized release notes that capture the **impact** of each change:

![kittylog generating changelog entries](assets/kittylog-usage.png)

---

## Quick Start

### Use kittylog without installing

```bash
uvx kittylog init  # Configure your AI provider
uvx kittylog       # Generate changelog entries
```

Review the proposed changelog, accept with `y`, and you're done.

### Install and use kittylog

```bash
uv tool install kittylog
kittylog init
kittylog
```

### Upgrade installed kittylog

```bash
uv tool upgrade kittylog
```

---

## Key Features

### 🧭 **Smart Release Detection**

- Detects missing changelog entries across tags, dates, or development gaps
- Handles repositories with or without formal version tags
- Calculates next semantic versions automatically for unreleased work

### 🌐 **Multi-Provider AI**

- Works with Anthropic, Cerebras, Chutes.ai, DeepSeek, Fireworks, Gemini, Groq, LM Studio, MiniMax, Mistral, Ollama, OpenAI, OpenRouter, Streamlake, Synthetic.new, Together AI, Z.AI (standard + coding), and custom Anthropic/OpenAI-compatible endpoints
- Retry logic, token budgeting, and provider-specific integrations are built in

### 🗂️ **Keep a Changelog Formatting**

- Produces sections for Added, Changed, Deprecated, Removed, Fixed, and Security
- Enforces bullet limits, removes duplicates, and trims AI chatter automatically
- Supports multilingual changelog content with optional translated section headings
- Tailors tone for developers, end users, or stakeholders with audience presets

### 🧑‍💻 **Interactive Workflow**

- Preview every entry before writing to disk
- Enable `--dry-run` to audit changes or generate release notes without saving
- Add hints (`-h "Focus on breaking changes"`) to steer the AI’s attention
- Choose between quiet automation or guided interactive mode

### 🔍 **Context-Aware Analysis**

- Pulls git status, stats, diffs (when enabled), and commit messages for richer prompts
- Detects “what’s new” since the last entry to avoid duplicates
- Handles large repositories with diff preprocessing and token safeguards

---

## Grouping Modes

Choose how kittylog slices your history for release notes:

| Mode                | Best for                                     | Example                                                 |
| ------------------- | -------------------------------------------- | ------------------------------------------------------- |
| 🏷️ `tags` (default) | Projects with semantic version tags          | `kittylog --grouping-mode tags`                         |
| 📅 `dates`          | Teams that publish on a cadence without tags | `kittylog --grouping-mode dates --date-grouping weekly` |
| ⏱️ `gaps`           | Burst-style development sessions             | `kittylog --grouping-mode gaps --gap-threshold 6`       |

Switch modes at any time—kittylog recalculates boundaries automatically.

---

## Usage Examples

### Basic Workflow

```bash
# Generate changelog entries for missing releases
kittylog

# Approve or decline each entry interactively
# y = accept | n = skip | r = rerun | q = quit
```

### Common Commands

| Command                                      | Description                              |
| -------------------------------------------- | ---------------------------------------- |
| `kittylog --dry-run`                         | Preview without writing                  |
| `kittylog -y`                                | Auto-accept generated entries            |
| `kittylog --all`                             | Rebuild every existing release entry     |
| `kittylog --from-tag v1.0.0 --to-tag v1.2.0` | Regenerate a specific range              |
| `kittylog --no-unreleased`                   | Skip `[Unreleased]` sections             |
| `kittylog --include-diff`                    | Add git diff context for deeper analysis |
| `kittylog -h "Call out DB migrations"`       | Add extra LLM context                    |
| `kittylog --audience users`                  | Speak to end users instead of developers |

### Power User Recipes

```bash
# Batch rebuild all releases with auto-approval
kittylog --all -y

# Weekly status digest grouped by dates
kittylog --grouping-mode dates --date-grouping weekly --dry-run

# Generate translated changelog using your default language
kittylog -y --show-prompt
```

---

## Configuration

Run `kittylog init` to walk through provider setup, or configure manually with environment variables:

```bash
# Example configuration
KITTYLOG_MODEL=anthropic:claude-3-5-haiku-latest
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
```

- Set defaults in `$HOME/.kittylog.env`
- Override per-project in `.kittylog.env`
- One-off overrides via CLI flags (`--model`, `--language`, `--audience`, etc.)

**Multilingual changelog?** Run `kittylog language` to choose from 25+ languages and optionally translate section headings.

**Different audiences?** Use `kittylog --audience developers|users|stakeholders` or set `KITTYLOG_AUDIENCE` to change tone.

**Want custom prompting?** Check [USAGE.md](USAGE.md) for advanced options and prompt customization.

---

## Getting Help

- **Full CLI reference:** [USAGE.md](USAGE.md)
- **Configuration & contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Report issues:** [GitHub Issues](https://github.com/cellwebb/kittylog/issues)

---

<!-- markdownlint-disable MD033 MD036 -->

<div align="center">

Made with ❤️ for teams who care about great release notes  
[⭐ Star kittylog](https://github.com/cellwebb/kittylog) • [🐛 Report issues](https://github.com/cellwebb/kittylog/issues) • [📖 Read the docs](USAGE.md)

</div>

<!-- markdownlint-enable MD033 MD036 -->
