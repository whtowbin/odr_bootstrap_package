# Contributing to ODR Bootstrap

Thank you for considering contributing to `odr-bootstrap`! This guide will help you get started.

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/<your-username>/odr_bootstrap_package.git
cd odr-bootstrap
```

### 2. Set Up Development Environment

We use `uv` for fast, reliable dependency management.

```bash
# Install all dependencies (including dev, test, and docs)
uv sync --all-extras

# Install pre-commit hooks for automatic code quality checks
uv run pre-commit install
```

### 3. Run Tests Locally

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=odr_bootstrap --cov-report=html

# Run specific test file
uv run pytest tests/test_odr_bootstrap.py -v
```

### 4. Test Package Installation with uv

`tests/test_installation.py` contains end-to-end tests that build the
package and install it with `uv` exactly as described in the README and
`docs/source/installation.rst` (`uv pip install`, `uv add`, and
`uv sync` from a source checkout). They're excluded from the default
`pytest` run (they're slower and don't touch application code, so they
don't count towards coverage) and are run separately:

```bash
make test-install
# or
uv run pytest -m install tests/test_installation.py --no-cov
```

To test installation and the full test/lint/type-check suite across every
Python version the package supports (3.11, 3.12, 3.13), use:

```bash
make test-all-versions
# or directly
./scripts/test-all-python-versions.sh

# only specific versions
./scripts/test-all-python-versions.sh 3.12 3.13

# also include the slow uv-installation tests
INSTALL_TESTS=1 ./scripts/test-all-python-versions.sh
```

This uses `uv python install` to provision any missing interpreters, then
runs `ruff`, `mypy`, and `pytest` (and optionally the installation tests)
against each one in an isolated environment.

## Code Quality Standards

All contributions must meet these standards:

### Type Hints

Every function must have complete type hints:

```python
from typing import Tuple
import numpy as np

def my_function(x: np.ndarray, y: float) -> Tuple[np.ndarray, float]:
    """Descriptive docstring."""
    pass
```

**Verification**: `uv run mypy odr_bootstrap` (strict mode enabled)

### Formatting and Linting

Code is formatted with `ruff`:

```bash
uv run ruff format .           # Format all files
uv run ruff check . --fix      # Auto-fix linting issues
```

### Docstring Style

Use NumPy-style docstrings for all public functions:

```python
def function(x, y):
    """
    Brief one-line summary.

    Longer description spanning multiple lines if needed.

    Parameters
    ----------
    x : array-like
        Description of x parameter.
    y : float
        Description of y parameter.

    Returns
    -------
    tuple
        Description of return value.

    Examples
    --------
    >>> result = function([1, 2, 3], 1.0)
    """
    pass
```

### Test Coverage

- All new code must be accompanied by tests
- Target minimum coverage of **85%** (enforce in CI/CD)
- Run `make test-cov` to generate coverage report

## Submitting Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-feature-name
```

### 2. Make Changes

- Implement feature or bug fix
- Write tests for new functionality
- Update docstrings and type hints
- Run `make lint` to auto-format

### 3. Commit with Clear Messages

```bash
# Stage changes
git add .

# Commit with conventional commit format
git commit -m "feat: add bootstrap confidence intervals"
```

**Commit Format**:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `test:` test additions/updates
- `refactor:` code refactoring without behavior change
- `chore:` dependency updates, CI/CD config, etc.

### 4. Push and Create a Pull Request

```bash
git push origin feature/my-feature-name
```

Then open a PR on GitHub with:
- Clear title describing the change
- Description of what changes and why
- Link to related issues (e.g., "Fixes #123")

## Pull Request Checklist

Before submitting your PR, verify:

- [ ] Tests pass locally: `make test`
- [ ] Coverage is adequate: `make test-cov`
- [ ] Code is formatted: `make format`
- [ ] No linting errors: `make lint`
- [ ] Type hints are complete: `uv run mypy odr_bootstrap`
- [ ] Docstrings are updated
- [ ] CHANGELOG.md is updated if user-facing changes

## Development Commands

Helpful commands defined in `Makefile`:

```bash
make help                # Show all available commands
make sync                # Sync dependencies
make test                # Run tests
make test-cov            # Run tests with coverage report
make lint                # Check code style
make type-check          # Run mypy type checking
make format              # Auto-format code
make build               # Build distribution package
make docs                # Build Sphinx documentation
make clean               # Remove build artifacts
```

## Documentation

If you're adding or modifying functionality:

1. Update or write docstrings in NumPy style
2. Add examples to docstrings if appropriate
3. Update README.md if user-facing
4. Update CHANGELOG.md under [Unreleased] section

To build and preview documentation locally:

```bash
make docs
open docs/build/html/index.html  # or use your browser
```

## Reporting Issues

When reporting bugs, include:

1. **Description**: What's the issue?
2. **Reproduction Steps**: How to reproduce it
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - Python version: `python --version`
   - Package version: `pip show odr-bootstrap`
   - OS: macOS / Linux / Windows

Example:

```markdown
## Bug Report: ODR_Bootstrap fails with NaN values

### Reproduction
```python
import numpy as np
from odr_bootstrap import ODR_Bootstrap

x = np.array([1.0, 2.0, np.nan, 4.0])
result = ODR_Bootstrap(x, y, x_err, y_err)
```

### Expected
Function should handle NaN gracefully by dropping those values

### Actual
TypeError: cannot perform reduce with flexible type

### Environment
- Python 3.12.0
- odr-bootstrap 0.1.0
- numpy 2.2.4
```

## Questions?

Open a discussion or issue on [GitHub Issues](https://github.com/whtowbin/odr_bootstrap_package/issues).

---

**Thank you for contributing!** Your efforts make this package better for everyone. 🙌
