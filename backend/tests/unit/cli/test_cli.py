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
    cmd_seed_delete,
    cmd_seed_dump,
    cmd_seed_list,
    cmd_seed_load,
    cmd_serve,
    main,
)
from astroimage.scripts.github_releases import ReleaseAsset
from astroimage.scripts.snapshot import SnapshotManifest, pack_snapshot


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
        patch("astroimage.scripts.db._alembic_config", return_value=MagicMock()) as config,
        patch("alembic.command.upgrade") as upgrade,
    ):
        assert cmd_db_upgrade(args) == 0
        upgrade.assert_called_once_with(config.return_value, "head")


def test_cmd_db_revision_invokes_alembic() -> None:
    args = Namespace(message="add table", autogenerate=True)
    with (
        patch("astroimage.scripts.db._alembic_config", return_value=MagicMock()) as config,
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
    monkeypatch.setattr("astroimage.scripts.openapi.backend_root", lambda: tmp_path)
    fake_app = MagicMock()
    fake_app.openapi.return_value = {"openapi": "3.1.0"}

    with patch("astroimage.main.app", fake_app):
        assert main(["openapi", "export"]) == 0

    assert (tmp_path / "openapi.json").is_file()


def test_cmd_seed_list_empty_release() -> None:
    catalog = MagicMock()
    catalog.list_assets.return_value = []
    with patch("astroimage.scripts.seed._seed_catalog", return_value=catalog):
        assert cmd_seed_list(Namespace(file=None, tag="seed-v1")) == 1


def test_cmd_seed_list_prints_assets(capsys: pytest.CaptureFixture[str]) -> None:
    catalog = MagicMock()
    catalog.list_assets.return_value = [
        ReleaseAsset(
            name="seed.tar.gz",
            download_url="https://example.test/seed.tar.gz",
            size_bytes=12,
            updated_at="2026-09-04T01:00:00Z",
            uploaded_by="fernando",
        )
    ]
    with patch("astroimage.scripts.seed._seed_catalog", return_value=catalog):
        assert cmd_seed_list(Namespace(file=None, tag="seed-v1")) == 0
    captured = capsys.readouterr()
    assert "seed.tar.gz" in captured.out
    assert "fernando" in captured.out


def test_cmd_seed_delete_missing_local_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert cmd_seed_delete(Namespace(file="missing-seed", tag=None, name=None)) == 1


def test_cmd_seed_delete_github_asset() -> None:
    catalog = MagicMock()
    catalog.list_assets.return_value = [
        ReleaseAsset(
            name="seed-2026.tar.gz",
            download_url="https://example.test/s",
            size_bytes=4,
        )
    ]
    with patch("astroimage.scripts.seed._seed_catalog", return_value=catalog):
        assert cmd_seed_delete(Namespace(file=None, tag="seed-v1", name="seed-2026.tar.gz")) == 0
    catalog.delete_asset.assert_called_once_with("seed-v1", "seed-2026.tar.gz")


def test_cmd_seed_dump_writes_archive_without_upload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("asyncio.run", return_value=b"tar-bytes"):
        assert cmd_seed_dump(Namespace(output="demo", tag=None)) == 0
    assert (tmp_path / "demo.tar.gz").read_bytes() == b"tar-bytes"


def test_cmd_seed_dump_uploads_when_tag_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    catalog = MagicMock()
    with (
        patch("asyncio.run", return_value=b"tar-bytes"),
        patch("astroimage.scripts.seed._seed_catalog", return_value=catalog),
    ):
        assert cmd_seed_dump(Namespace(output="demo", tag="seed-v1")) == 0
    catalog.ensure_release.assert_called_once_with("seed-v1")
    catalog.upload_file.assert_called_once()


def test_cmd_seed_load_from_local_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    packed = pack_snapshot(
        [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "object_key": "fits/a.fits",
                "original_filename": "a.fits",
                "size_bytes": 1,
                "metadata_payload": {},
            }
        ],
        {"fits/a.fits": b"F"},
        manifest=SnapshotManifest(
            name="seed-demo",
            created_at="2026-09-04T01:00:00Z",
            created_by="fernando",
            record_count=1,
        ),
    )
    archive = tmp_path / "seed-demo.tar.gz"
    archive.write_bytes(packed)
    with patch("asyncio.run", return_value=(1, 0)):
        assert cmd_seed_load(Namespace(file=str(archive), tag=None)) == 0
    captured = capsys.readouterr()
    assert "seed-demo" in captured.out
    assert "restored=1" in captured.out
