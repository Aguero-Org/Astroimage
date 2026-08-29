from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from astroimage.cli import (
    backend_root,
    build_parser,
    cmd_db_revision,
    cmd_db_upgrade,
    cmd_openapi_export,
    cmd_serve,
    main,
)


def test_backend_root_points_at_alembic_ini() -> None:
    root = backend_root()
    assert (root / "alembic.ini").is_file()
    assert root.name == "backend"


def test_parser_requires_command() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_main_serve_dispatches_to_uvicorn() -> None:
    with patch("astroimage.cli.cmd_serve", return_value=0) as serve:
        assert main(["serve", "--reload", "--port", "9000"]) == 0
        serve.assert_called_once()
        args = serve.call_args.args[0]
        assert args.reload is True
        assert args.port == 9000


def test_cmd_serve_runs_uvicorn() -> None:
    args = Namespace(host="0.0.0.0", port=8000, reload=True)
    with patch("uvicorn.run") as run:
        assert cmd_serve(args) == 0
        run.assert_called_once_with(
            "astroimage.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
        )


def test_cmd_db_upgrade_invokes_alembic() -> None:
    args = Namespace(revision="head")
    with (
        patch("astroimage.cli._alembic_config", return_value=MagicMock()) as config,
        patch("alembic.command.upgrade") as upgrade,
    ):
        assert cmd_db_upgrade(args) == 0
        upgrade.assert_called_once_with(config.return_value, "head")


def test_cmd_db_revision_invokes_alembic() -> None:
    args = Namespace(message="add table", autogenerate=True)
    with (
        patch("astroimage.cli._alembic_config", return_value=MagicMock()) as config,
        patch("alembic.command.revision") as revision,
    ):
        assert cmd_db_revision(args) == 0
        revision.assert_called_once_with(
            config.return_value,
            message="add table",
            autogenerate=True,
        )


def test_cmd_openapi_export_writes_document(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    fake_app = MagicMock()
    fake_app.openapi.return_value = {"openapi": "3.1.0", "paths": {}}

    with patch("astroimage.main.app", fake_app):
        assert cmd_openapi_export(Namespace(output=str(target))) == 0

    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["openapi"] == "3.1.0"


def test_main_openapi_export_default_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("astroimage.cli.backend_root", lambda: tmp_path)
    fake_app = MagicMock()
    fake_app.openapi.return_value = {"openapi": "3.1.0"}

    with patch("astroimage.main.app", fake_app):
        assert main(["openapi", "export"]) == 0

    assert (tmp_path / "openapi.json").is_file()
