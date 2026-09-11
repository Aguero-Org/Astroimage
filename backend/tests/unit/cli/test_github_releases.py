from collections.abc import Sequence
from pathlib import Path

import pytest

from astroimage.scripts.github_releases import GitHubReleaseCatalog, ReleaseAsset
from astroimage.scripts.snapshot import (
    SnapshotManifest,
    default_snapshot_stem,
    pack_snapshot,
    snapshot_path,
    unpack_snapshot,
)


def test_list_assets_parses_gh_release_view() -> None:
    def fake_run(argv: Sequence[str]) -> str:
        assert argv[:4] == ("gh", "release", "view", "seed-v1")
        assert "--json" in argv
        return (
            '{"assets":[{"name":"seed.tar.gz","url":"https://example.test/seed.tar.gz",'
            '"size":20,"updatedAt":"2026-09-04T01:00:00Z"}]}'
        )

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    assets = catalog.list_assets("seed-v1")
    assert assets == [
        ReleaseAsset(
            name="seed.tar.gz",
            download_url="https://example.test/seed.tar.gz",
            size_bytes=20,
            updated_at="2026-09-04T01:00:00Z",
        )
    ]


def test_list_assets_missing_release_is_empty() -> None:
    def fake_run(_argv: Sequence[str]) -> str:
        raise RuntimeError("release not found")

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    assert catalog.list_assets("missing") == []


def test_ensure_release_creates_when_missing() -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(argv: Sequence[str]) -> str:
        calls.append(tuple(argv))
        if argv[1:3] == ("release", "view"):
            raise RuntimeError("release not found")
        return ""

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    catalog.ensure_release("seed-v1")
    assert calls[0][:4] == ("gh", "release", "view", "seed-v1")
    assert calls[1][:4] == ("gh", "release", "create", "seed-v1")
    assert "--prerelease" in calls[1]


def test_download_snapshot_reads_gh_release_file(tmp_path: Path) -> None:
    archive = tmp_path / "seed.tar.gz"
    archive.write_bytes(b"payload")
    calls: list[tuple[str, ...]] = []

    def fake_run(argv: Sequence[str]) -> str:
        calls.append(tuple(argv))
        if argv[1:3] == ("release", "view"):
            return (
                '{"assets":[{"name":"seed.tar.gz","url":"https://example.test/seed.tar.gz",'
                '"size":7,"updatedAt":"2026-09-04T01:00:00Z"}]}'
            )
        if argv[1:3] == ("release", "download"):
            dest = Path(argv[argv.index("--dir") + 1])
            (dest / "seed.tar.gz").write_bytes(b"payload")
            return ""
        raise AssertionError(argv)

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    assert catalog.download_snapshot("seed-v1") == b"payload"
    assert calls[1][:4] == ("gh", "release", "download", "seed-v1")


def test_download_snapshot_requires_tarball() -> None:
    def fake_run(_argv: Sequence[str]) -> str:
        return '{"assets":[{"name":"notes.txt","url":"https://example.test/n","size":1}]}'

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    try:
        catalog.download_snapshot("seed-v1")
    except RuntimeError as exc:
        assert "No .tar.gz" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_list_assets_reraises_other_gh_errors() -> None:
    def fake_run(_argv: Sequence[str]) -> str:
        raise RuntimeError("API rate limit")

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    try:
        catalog.list_assets("seed-v1")
    except RuntimeError as exc:
        assert "rate limit" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_ensure_release_skips_create_when_present() -> None:
    calls: list[tuple[str, ...]] = []

    def fake_run(argv: Sequence[str]) -> str:
        calls.append(tuple(argv))
        return ""

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    catalog.ensure_release("seed-v1")
    assert len(calls) == 1
    assert calls[0][:4] == ("gh", "release", "view", "seed-v1")


def test_run_gh_missing_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    from astroimage.scripts.github_releases import run_gh

    def fake_run(*_args: object, **_kwargs: object) -> object:
        raise FileNotFoundError("gh")

    monkeypatch.setattr("astroimage.scripts.github_releases.subprocess.run", fake_run)
    try:
        run_gh(("gh", "release", "list"))
    except RuntimeError as exc:
        assert "gh CLI not found" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_run_gh_nonzero_uses_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from astroimage.scripts.github_releases import run_gh

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stderr="release not found\n", stdout="")

    monkeypatch.setattr("astroimage.scripts.github_releases.subprocess.run", fake_run)
    try:
        run_gh(("gh", "release", "view", "x"))
    except RuntimeError as exc:
        assert str(exc) == "release not found"
    else:
        raise AssertionError("expected RuntimeError")


def test_view_assets_skips_non_objects() -> None:
    def fake_run(_argv: Sequence[str]) -> str:
        return '{"assets":[1, {"name": true}, {"name":"ok.tar.gz","size":true,"url":1}]}'

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    assets = catalog.list_assets("seed-v1")
    assert len(assets) == 1
    assert assets[0].name == "ok.tar.gz"
    assert assets[0].size_bytes == 0
    assert assets[0].download_url == ""


def test_upload_and_delete_use_gh_release(tmp_path: Path) -> None:
    calls: list[tuple[str, ...]] = []
    archive = tmp_path / "seed.tar.gz"
    archive.write_bytes(b"gz")

    def fake_run(argv: Sequence[str]) -> str:
        calls.append(tuple(argv))
        return ""

    catalog = GitHubReleaseCatalog(owner="org", repo="repo", run=fake_run)
    catalog.upload_file("seed-v1", archive)
    catalog.delete_asset("seed-v1", "seed.tar.gz")
    assert calls[0][:5] == ("gh", "release", "upload", "seed-v1", str(archive))
    assert calls[1][:5] == ("gh", "release", "delete-asset", "seed-v1", "seed.tar.gz")


def test_snapshot_path_appends_tar_gz() -> None:
    assert snapshot_path("seed").name == "seed.tar.gz"
    assert snapshot_path("seed.tar.gz").name == "seed.tar.gz"
    assert snapshot_path("seed.tgz").name == "seed.tgz"


def test_default_snapshot_stem_includes_date() -> None:
    from datetime import UTC, datetime

    stem = default_snapshot_stem(datetime(2026, 9, 4, 1, 0, 0, tzinfo=UTC))
    assert stem == "seed-2026-09-04-010000Z"


def test_pack_and_unpack_snapshot_roundtrip() -> None:
    records = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "object_key": "fits/a.fits",
            "original_filename": "a.fits",
            "size_bytes": 4,
            "metadata_payload": {"source_name": "a"},
        }
    ]
    objects = {"fits/a.fits": b"FITS"}
    manifest = SnapshotManifest(
        name="seed-2026-09-04",
        created_at="2026-09-04T01:00:00Z",
        created_by="fernando",
        record_count=1,
    )
    packed = pack_snapshot(records, objects, manifest=manifest)
    unpacked_records, unpacked_objects, unpacked_manifest = unpack_snapshot(packed)
    assert unpacked_records == records
    assert unpacked_objects == objects
    assert unpacked_manifest == manifest


def test_unpack_skips_unsafe_tar_member_names() -> None:
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo(name="../evil.txt")
        payload = b"nope"
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))
        records_bytes = b"[]"
        records_info = tarfile.TarInfo(name="records.json")
        records_info.size = len(records_bytes)
        archive.addfile(records_info, io.BytesIO(records_bytes))
    unpacked_records, unpacked_objects, unpacked_manifest = unpack_snapshot(buffer.getvalue())
    assert unpacked_records == []
    assert unpacked_objects == {}
    assert unpacked_manifest is None
