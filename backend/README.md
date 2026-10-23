# astroimage backend

FastAPI API for spatial image processing. See the repository root `README.md` and `AGENTS.md` for the full toolchain and conventions.

```bash
uv sync --all-groups
uv run astroimage serve --reload
uv run astroimage openapi export
uv run astroimage db upgrade
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest
```

## Mutation testing

`mutmut` runs under WSL (it requires `fork`) and keeps its environment outside the
repo. See [`docs/mutation-testing.md`](../docs/mutation-testing.md) for scope,
timeouts, reports and survivor triage.

```bash
wsl.exe -d Ubuntu -- bash -lc \
  "cd /mnt/d/repos/tip/Astroimage/backend && \
   UV_PROJECT_ENVIRONMENT=/tmp/astroimage-mutmut-venv ~/.local/bin/uv run mutmut run --max-children 2"
```
