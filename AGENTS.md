# AI Agent Integration

This repository integrates with multiple AI providers through the [aisuite](https://github.com/mikep/aisuite) library to generate changelog entries from git commit history.

> **Note**: We dogfood on this project! The `CHANGELOG.md` file in this repository is always updated via `clog` itself, demonstrating the tool's capabilities in a real-world scenario.
>
> **Development Note**: This project uses `uv` for Python package management. When running commands locally, use `uv run` prefix (e.g., `uv run clog --dry-run`)

## Supported AI Providers

The clog tool works with any provider supported by aisuite. Currently, the following providers are included as dependencies:

### Anthropic

- **Purpose**: Generate concise, well-structured changelog entries
- **Usage**: `clog config set CLOG_MODEL anthropic:claude-3-5-haiku-latest`

### OpenAI

- **Purpose**: Generate changelog entries with advanced language understanding
- **Usage**: `clog config set CLOG_MODEL openai:gpt-4o`

### Groq

- **Purpose**: Fast changelog generation with quality results
- **Usage**: `clog config set CLOG_MODEL groq:llama3-70b-8192`

### Ollama

- **Purpose**: Privacy-focused, offline changelog generation
- **Usage**: `clog config set CLOG_MODEL ollama:llama3`

### Cerebras

- **Purpose**: High-performance AI processing for changelog generation
- **Usage**: `clog config set CLOG_MODEL cerebras:llama3.1-70b`

## How AI Agents Are Used

The clog tool uses AI agents in a structured workflow:

1. **Git Analysis**: Extract commits and changed files between tags
2. **Prompt Engineering**: Construct a detailed prompt with commit information
3. **AI Generation**: Use the configured provider to generate changelog content
4. **Content Processing**: Clean and format the AI response according to Keep a Changelog standards

Each provider brings different strengths to the changelog generation process, allowing users to choose based on their priorities (cost, speed, quality, privacy).

## Unreleased Changes Support

The clog tool automatically detects when the current git state doesn't match a tag and creates an "Unreleased" section in the changelog with changes since the latest tag. This allows you to keep your changelog up-to-date with ongoing development work.

When running `clog` without specific tag options:

1. New tags since the last changelog update are processed as usual
2. If the current commit is not tagged, an "Unreleased" section is automatically created
3. Changes since the last tag (or all changes if no tags exist) are included in this section

This feature makes it easier to track ongoing development work before officially releasing with a git tag.

> **Dogfooding Note**: This very `CHANGELOG.md` file is maintained using `clog` itself, so you can see this unreleased changes functionality in action!

## Configuration

AI providers are configured through the `CLOG_MODEL` environment variable or in `.clog.env` files:

```bash
# Set in ~/.clog.env for global configuration
CLOG_MODEL=anthropic:claude-3-5-haiku-latest

# Or override per project in ./.clog.env
CLOG_MODEL=openai:gpt-4o

# Or specify at runtime
clog -m "groq:llama3-70b-8192"
```

## Adding New Providers

To add support for a new AI provider:

1. Add the provider SDK to `pyproject.toml` dependencies
2. Test with aisuite to ensure compatibility
3. Add example configuration to `README.md` and this document
4. Add tests to verify integration

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.
