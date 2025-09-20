# Contributing to clog

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Adding New AI Providers

The clog tool uses [aisuite](https://github.com/mikep/aisuite) to interface with different AI providers. To add a new provider:

1. Add the provider SDK to `pyproject.toml` dependencies
2. Test the integration with aisuite
3. Update documentation in `README.md` and `AGENTS.md`

Note that aisuite handles the abstraction layer, so in many cases adding a new provider only requires adding the dependency.

## Development Setup

1. Clone the repo
2. Install dependencies with `pip install -e .[dev]`
3. Run tests with `pytest`

## Code Quality

- All code should be formatted with `black`
- Imports should be sorted with `isort`
- Code should pass `ruff` linting checks

## Testing

- All new features should include tests
- Run the full test suite before submitting PRs
- Use `pytest` for testing

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the style guidelines
5. Issue the pull request!