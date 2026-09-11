from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from astroimage.scripts.db import cmd_db_reconcile, cmd_db_revision, cmd_db_upgrade
from astroimage.scripts.openapi import cmd_openapi_export
from astroimage.scripts.paths import backend_root
from astroimage.scripts.seed import (
    cmd_seed_delete,
    cmd_seed_dump,
    cmd_seed_list,
    cmd_seed_load,
)
from astroimage.scripts.serve import cmd_serve

__all__ = [
    "backend_root",
    "build_parser",
    "cmd_db_reconcile",
    "cmd_db_revision",
    "cmd_db_upgrade",
    "cmd_openapi_export",
    "cmd_seed_delete",
    "cmd_seed_dump",
    "cmd_seed_list",
    "cmd_seed_load",
    "cmd_serve",
    "main",
]


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

    reconcile = db_sub.add_parser(
        "reconcile",
        help="Recreate fits_records rows from stored FITS objects",
    )
    reconcile.set_defaults(handler=cmd_db_reconcile)

    seed = subparsers.add_parser(
        "seed",
        help="Dev: snapshot/restore MinIO+Postgres test data via GitHub Releases",
    )
    seed_sub = seed.add_subparsers(dest="seed_command", required=True)
    seed_dump = seed_sub.add_parser("dump", help="Dump current MinIO objects and Postgres rows")
    seed_dump.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output path (default: seed-YYYY-MM-DD-HHMMSSZ.tar.gz)",
    )
    seed_dump.add_argument("--tag", default=None, help="Upload archive to this GitHub release tag")
    seed_dump.add_argument("--owner", default="Aguero-Org")
    seed_dump.add_argument("--repo", default="Astroimage")
    seed_dump.set_defaults(handler=cmd_seed_dump)

    seed_load = seed_sub.add_parser("load", help="Restore a snapshot into MinIO and Postgres")
    seed_load.add_argument("-f", "--file", default=None, help="Local seed.tar.gz")
    seed_load.add_argument("--tag", default=None, help="GitHub release tag containing the archive")
    seed_load.add_argument("--owner", default="Aguero-Org")
    seed_load.add_argument("--repo", default="Astroimage")
    seed_load.set_defaults(handler=cmd_seed_load)

    seed_list = seed_sub.add_parser("list", help="Show snapshot name, author and date")
    seed_list.add_argument("-f", "--file", default=None, help="Local snapshot file")
    seed_list.add_argument("--tag", default=None, help="GitHub release tag")
    seed_list.add_argument("--owner", default="Aguero-Org")
    seed_list.add_argument("--repo", default="Astroimage")
    seed_list.set_defaults(handler=cmd_seed_list)

    seed_delete = seed_sub.add_parser("delete", help="Delete a local or GitHub snapshot")
    seed_delete.add_argument("-f", "--file", default=None, help="Local snapshot file")
    seed_delete.add_argument("--tag", default=None, help="GitHub release tag")
    seed_delete.add_argument("--name", default=None, help="Asset filename on the release")
    seed_delete.add_argument("--owner", default="Aguero-Org")
    seed_delete.add_argument("--repo", default="Astroimage")
    seed_delete.set_defaults(handler=cmd_seed_delete)

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
