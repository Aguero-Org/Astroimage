from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alembic.config import Config


def backend_root() -> Path:
    package_root = Path(__file__).resolve().parent
    candidates = (
        package_root.parents[1],
        package_root.parents[2],
        Path.cwd(),
    )
    for candidate in candidates:
        if (candidate / "alembic.ini").is_file():
            return candidate
    return package_root.parents[1]


def _alembic_config() -> Config:
    from alembic.config import Config

    root = backend_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    return config


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "astroimage.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_db_upgrade(args: argparse.Namespace) -> int:
    from alembic import command

    command.upgrade(_alembic_config(), args.revision)
    return 0


def cmd_db_revision(args: argparse.Namespace) -> int:
    from alembic import command

    command.revision(
        _alembic_config(),
        message=args.message,
        autogenerate=args.autogenerate,
    )
    return 0


def cmd_openapi_export(args: argparse.Namespace) -> int:
    from astroimage.main import app

    target = Path(args.output) if args.output else backend_root() / "openapi.json"
    target.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="astroimage",
        description="Astroimage project operations.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run the API development server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(handler=cmd_serve)

    db = subparsers.add_parser("db", help="Database migration operations")
    db_sub = db.add_subparsers(dest="db_command", required=True)

    upgrade = db_sub.add_parser("upgrade", help="Apply migrations")
    upgrade.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Target revision (default: head)",
    )
    upgrade.set_defaults(handler=cmd_db_upgrade)

    revision = db_sub.add_parser("revision", help="Create a new migration revision")
    revision.add_argument("-m", "--message", required=True)
    revision.add_argument("--autogenerate", action="store_true")
    revision.set_defaults(handler=cmd_db_revision)

    openapi = subparsers.add_parser("openapi", help="OpenAPI contract operations")
    openapi_sub = openapi.add_subparsers(dest="openapi_command", required=True)

    export = openapi_sub.add_parser("export", help="Write the OpenAPI document to disk")
    export.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output path (default: backend/openapi.json)",
    )
    export.set_defaults(handler=cmd_openapi_export)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.error("a subcommand is required")
    return int(handler(args))


if __name__ == "__main__":
    sys.exit(main())
