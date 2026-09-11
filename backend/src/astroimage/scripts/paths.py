from __future__ import annotations

from pathlib import Path


def backend_root() -> Path:
    package_root = Path(__file__).resolve().parents[1]
    candidates = (
        package_root.parents[1],
        package_root.parents[2],
        Path.cwd(),
    )
    for candidate in candidates:
        if (candidate / "alembic.ini").is_file():
            return candidate
    return package_root.parents[1]
