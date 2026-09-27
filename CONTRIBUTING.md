# Contributing

## Setup

```sh
uv sync
uv run pre-commit install
```

`pre-commit install` sets up two git hooks:

- `pre-commit`: `ruff check --fix` and `ruff format` on staged Python files, then `mypy --strict` (package and tests) and `pytest` on the whole project
- `commit-msg`: single-line Conventional Commit subject (`.githooks/commit-msg`)

Clones that previously used `core.hooksPath` need `git config --unset core.hooksPath` first; pre-commit refuses to install while it is set.

Run the tests:

```sh
uv run pytest
```

They mock the network at `requests` and `socket.getaddrinfo`, with an in-memory Porkbun in `tests/conftest.py`, so they never touch the real API.

Run all hooks against the whole tree:

```sh
uv run pre-commit run --all-files
```

CI (`.github/workflows/checks.yml`) runs the same two steps, `uv sync --locked` and `uv run pre-commit run --all-files`, on every push and pull request, so skipping the hooks locally with `--no-verify` still gets caught.

Branch protection should require only the `all checks passed` job. It fails if any job it depends on fails, is cancelled or is skipped, so new jobs only need adding to its `needs` list.
