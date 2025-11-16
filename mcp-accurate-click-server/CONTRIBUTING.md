# Contributing to MCP Accurate Click Server

Thank you for your interest in contributing to MCP Accurate Click Server! This document provides guidelines and instructions for contributing.

## Getting Started

### Development Environment Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mcp-accurate-click-server.git
   cd mcp-accurate-click-server
   ```

3. Set up the development environment:
   ```bash
   make dev-setup
   # or
   ./scripts/install.sh dev
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Before Making Changes

1. Ensure your fork is up to date:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_REPO/mcp-accurate-click-server.git
   git fetch upstream
   git merge upstream/main
   ```

2. Create a feature branch:
   ```bash
   git checkout -b feature/descriptive-name
   ```

### Making Changes

1. **Write Tests**: Add tests for new functionality
2. **Write Code**: Implement your changes
3. **Document**: Update docstrings and documentation
4. **Format**: Run code formatters
   ```bash
   make format
   ```

5. **Lint**: Check code quality
   ```bash
   make lint
   ```

6. **Type Check**: Run type checking
   ```bash
   make type-check
   ```

7. **Test**: Ensure all tests pass
   ```bash
   make test
   ```

### Running All Checks

Run the complete CI pipeline locally:
```bash
make check
# or
./scripts/build.sh ci
```

## Code Style

### Python Code Style

- Follow [PEP 8](https://pep8.org/)
- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Type hints are required for all functions
- Maximum line length: 100 characters

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

## Testing

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure in tests
- Use descriptive test names: `test_should_do_something_when_condition`
- Use pytest fixtures for setup/teardown
- Aim for high code coverage (>80%)

### Running Tests

```bash
# All tests
make test

# With coverage
make test-cov

# Watch mode (for development)
./scripts/test.sh watch

# Specific test file
pytest tests/test_specific.py

# Specific test function
pytest tests/test_specific.py::test_function_name
```

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    pass

@pytest.mark.integration
def test_integration():
    pass
```

## Commit Guidelines

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(dom): add support for shadow DOM extraction

fix(coordinates): handle negative monitor positions correctly

docs(api): update API documentation for click validation
```

### Commits

- Keep commits atomic and focused
- Write clear, descriptive commit messages
- Reference issues in commits: `fixes #123` or `relates to #456`

## Pull Request Process

### Before Submitting

1. Update your branch:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Run all checks:
   ```bash
   make check
   ```

3. Update documentation if needed

4. Add entry to CHANGELOG.md under [Unreleased]

### Submitting

1. Push your branch:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request on GitHub

3. Fill out the PR template completely:
   - Description of changes
   - Motivation and context
   - Testing done
   - Breaking changes (if any)
   - Related issues

### PR Requirements

- All tests must pass
- Code coverage should not decrease
- Code must pass linting and type checking
- Documentation must be updated
- Changes must be described in CHANGELOG.md

### Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Keep the PR updated with main branch
4. Once approved, maintainers will merge

## Code Review Guidelines

### For Contributors

- Be open to feedback
- Respond to comments promptly
- Ask questions if unclear
- Keep discussions respectful

### For Reviewers

- Be constructive and respectful
- Explain the "why" behind suggestions
- Approve when ready, don't block on minor issues
- Recognize good work

## Project Structure

```
mcp-accurate-click-server/
├── src/
│   └── mcp_server/
│       ├── core/          # Core server implementation
│       ├── dom/           # DOM extraction
│       ├── windows/       # Windows API integration
│       ├── validation/    # Click validation
│       ├── accessibility/ # Accessibility tree
│       └── vision/        # Computer vision
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                 # Documentation
├── examples/             # Example scripts
└── scripts/              # Build and development scripts
```

## Documentation

### Code Documentation

- All public APIs must have docstrings
- Include type hints
- Provide usage examples
- Document exceptions

### User Documentation

- Update README.md for user-facing changes
- Add examples for new features
- Update API documentation
- Keep documentation in sync with code

## Issue Reporting

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces
- Minimal code example

### Feature Requests

Include:
- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Alternatives considered

## Questions?

- Open an issue for questions
- Check existing issues and documentation first
- Be specific and provide context

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions make this project better. Thank you for taking the time to contribute!
