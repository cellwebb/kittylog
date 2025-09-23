# Contributing to kittylog

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Setup

1. Clone the repo
2. Install dependencies with `uv pip install -e ".[dev,test]"` or use `make install-dev`
3. Install pre-commit hooks with `pre-commit install` (or use `make install-dev` which does this automatically)
4. Run tests with `pytest` or `make test`

For a quick setup, you can run `make quickstart` which will install dependencies, set up pre-commit hooks, and run initial tests.

## Code Quality

- All code should be formatted with `ruff format` (replaces black and isort)
- Code should pass `ruff check` linting
- Type checking should pass `mypy src/kittylog`

You can run all code quality checks with:

- `make lint` - runs ruff check and mypy
- `make format` - formats code with ruff
- `make pre-commit` - runs all pre-commit hooks
- `make check` - runs both linting and tests

## Testing

- All new features should include tests
- Run the full test suite before submitting PRs
- Use `pytest` for testing
- Tests are isolated from global configuration files
- Configuration-related tests mock the KITTYLOG_ENV_PATH constant to prevent interference from existing global config files

Run tests with:

- `make test` - runs pytest
- `make test-coverage` - runs tests with coverage report
- `make test-integration` - runs integration tests only
- `make test-watch` - runs tests in watch mode

## Adding New AI Providers

The kittylog tool uses [aisuite](https://github.com/mikep/aisuite) to interface with different AI providers. To add a new provider:

1. Add the provider SDK to `pyproject.toml` dependencies
2. Test the integration with aisuite
3. Update documentation in `README.md` and `AGENTS.md`

Note that aisuite handles the abstraction layer, so in many cases adding a new provider only requires adding the dependency.

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the style guidelines (`make format` and `make lint`)
5. Issue the pull request!

All PRs will automatically run pre-commit hooks and tests. Make sure to run `make check` locally to verify everything passes before submitting.
