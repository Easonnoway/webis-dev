# Contributing to Webis

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to Webis. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by the [Webis Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for Webis. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as many details as possible.
- **Provide specific examples** to demonstrate the steps.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for Webis, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as many details as possible.
- **Explain why this enhancement would be useful** to most Webis users.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.

## Styleguides

### Python Styleguide

- We use `ruff` for linting and formatting.
- We use `mypy` for static type checking.
- All new code should have type hints.
- Docstrings should follow the Google Python Style Guide.

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Development Setup

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/webis.git
   cd webis
   ```

2. Install dependencies (using uv or pip)
   ```bash
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks
   ```bash
   pre-commit install
   ```

4. Run tests
   ```bash
   pytest
   ```

Thank you for contributing!
