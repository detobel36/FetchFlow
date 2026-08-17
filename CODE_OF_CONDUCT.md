# Code of Conduct

FetchFlow contributors are expected to keep changes readable, tested, and easy
to review.

## Before Opening a Pull Request

Use a Python virtual environment for local development, then install the
project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install ruff
```

Run the automated test suite:

```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

Run the linter:

```bash
python -m ruff check .
```

The same checks run in GitHub Actions for pull requests and pushes to `main`
or `master`.

## Linting Standard

This project uses Ruff. The lint configuration is defined in
[`pyproject.toml`](pyproject.toml).

The current baseline checks for syntax errors, undefined names, unused imports,
and import ordering. Keep imports sorted and remove dead code before submitting
changes.

## Testing Standard

Tests live in [`tests/`](tests). Add or update tests when changing behavior,
fixing bugs, or adding public functionality.

Automated tests should be deterministic and should avoid live network access
unless a test explicitly mocks the HTTP layer.
