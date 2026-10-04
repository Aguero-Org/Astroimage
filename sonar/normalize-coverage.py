"""Rewrite workspace-relative coverage paths for the monorepo scanner.

Pytest and Vitest run inside ``backend/`` and ``frontend/``, so their
reports say ``src/...``. SonarQube matches paths from the repository
root, where those files are ``backend/src/...`` and ``frontend/src/...``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_XML = ROOT / "backend" / "coverage.xml"
LCOV = ROOT / "frontend" / "coverage" / "lcov.info"


def rewrite_coverage_xml(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace('filename="src/', 'filename="backend/src/'), encoding="utf-8")


def rewrite_lcov(path: Path) -> None:
    text = path.read_text(encoding="utf-8").replace("\\", "/")
    path.write_text(text.replace("SF:src/", "SF:frontend/src/"), encoding="utf-8")


def main() -> int:
    missing = [path for path in (COVERAGE_XML, LCOV) if not path.is_file()]
    if missing:
        for path in missing:
            print(f"missing coverage report: {path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    rewrite_coverage_xml(COVERAGE_XML)
    rewrite_lcov(LCOV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
