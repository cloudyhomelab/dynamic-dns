# Contributing

## Setup

```sh
uv sync
uv run pre-commit install
```

`pre-commit install` sets up two git hooks:

- `pre-commit`: `ruff check --fix` and `ruff format` on staged Python files, and `mypy --strict` on the package
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
