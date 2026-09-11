from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

_SNAPSHOT_SUFFIXES = (".tar.gz", ".tgz")

GhRunner = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    download_url: str
    size_bytes: int
    updated_at: str = ""
    uploaded_by: str = ""


class GitHubReleaseCatalog:
    def __init__(
        self,
        *,
        owner: str,
        repo: str,
        run: GhRunner | None = None,
    ) -> None:
        self._repo = f"{owner}/{repo}"
        self._run = run if run is not None else run_gh

    def list_assets(self, tag: str) -> Sequence[ReleaseAsset]:
        try:
            payload = self._view_assets(tag)
        except RuntimeError as exc:
            if _is_missing_release(exc):
                return []
            raise
        return payload

    def download_snapshot(self, tag: str) -> bytes:
        assets = [asset for asset in self.list_assets(tag) if _is_snapshot_name(asset.name)]
        if not assets:
            raise RuntimeError(f"No .tar.gz snapshot asset on release {tag}")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            self._gh(
                "release",
                "download",
                tag,
                "--repo",
                self._repo,
                "--pattern",
                assets[0].name,
                "--dir",
                str(dest),
            )
            matches = list(dest.rglob(assets[0].name))
            if not matches:
                raise RuntimeError(f"gh did not download {assets[0].name}")
            return matches[0].read_bytes()

    def ensure_release(self, tag: str) -> None:
        try:
            self._gh("release", "view", tag, "--repo", self._repo)
        except RuntimeError as exc:
            if not _is_missing_release(exc):
                raise
            self._gh(
                "release",
                "create",
                tag,
                "--repo",
                self._repo,
                "--prerelease",
                "--title",
                tag,
                "--notes",
                "astroimage seed snapshot",
            )

    def upload_file(self, tag: str, path: Path) -> None:
        self._gh("release", "upload", tag, str(path), "--repo", self._repo)

    def delete_asset(self, tag: str, name: str) -> None:
        self._gh("release", "delete-asset", tag, name, "--repo", self._repo, "--yes")

    def _view_assets(self, tag: str) -> list[ReleaseAsset]:
        raw = self._gh("release", "view", tag, "--repo", self._repo, "--json", "assets")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise RuntimeError("gh release view payload is not an object")
        assets = payload.get("assets")
        if not isinstance(assets, list):
            return []
        selected: list[ReleaseAsset] = []
        for raw_asset in assets:
            if not isinstance(raw_asset, dict):
                continue
            name = raw_asset.get("name")
            if not isinstance(name, str):
                continue
            url = raw_asset.get("url")
            size_bytes = raw_asset.get("size")
            updated_at = raw_asset.get("updatedAt")
            parsed_size = (
                size_bytes
                if isinstance(size_bytes, int) and not isinstance(size_bytes, bool)
                else 0
            )
            selected.append(
                ReleaseAsset(
                    name=name,
                    download_url=url if isinstance(url, str) else "",
                    size_bytes=parsed_size,
                    updated_at=updated_at if isinstance(updated_at, str) else "",
                )
            )
        return selected

    def _gh(self, *args: str) -> str:
        return self._run(("gh", *args))


def run_gh(argv: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("gh CLI not found; install GitHub CLI and run gh auth login") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or " ".join(argv)
        raise RuntimeError(detail)
    return completed.stdout


def _is_snapshot_name(name: str) -> bool:
    lowered = name.lower()
    return any(lowered.endswith(suffix) for suffix in _SNAPSHOT_SUFFIXES)


def _is_missing_release(exc: RuntimeError) -> bool:
    return "release not found" in str(exc).lower()
