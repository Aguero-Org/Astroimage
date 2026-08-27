# astroimage backend

FastAPI API for spatial image processing. See the repository root `README.md` and `AGENTS.md` for the full toolchain and conventions.

```bash
uv sync --all-groups
uv run uvicorn astroimage.main:app --reload --app-dir src
uv run ruff check src tests
uv run ruff format src tests
uv run mypy
uv run lint-imports
uv run pytest
uv run alembic upgrade head
```
