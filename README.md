# dynamic-dns

Sync DNS A records for domains hosted with Porkbun.

## Development

```sh
uv sync
uv run pre-commit install
```

`pre-commit install` sets up two git hooks:

- `pre-commit`: `ruff check --fix` and `ruff format` on staged Python files
- `commit-msg`: single-line Conventional Commit subject (`.githooks/commit-msg`)

Clones that previously used `core.hooksPath` need `git config --unset core.hooksPath` first; pre-commit refuses to install while it is set.

Run all hooks against the whole tree:

```sh
uv run pre-commit run --all-files
```
