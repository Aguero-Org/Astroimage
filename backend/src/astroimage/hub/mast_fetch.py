from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

import httpx

PART_BYTES = 8 * 1024 * 1024
RETRY_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = (2.0, 4.0, 8.0)


class MastFetchError(RuntimeError):
    """Raised when a MAST byte range cannot be read."""


@dataclass(frozen=True)
class ResourceProbe:
    total_bytes: int | None
    etag: str | None
    last_modified: str | None
    first_byte: bytes


def _total_from_content_range(header: str | None) -> int | None:
    if header is None or "/" not in header:
        return None
    total = header.rsplit("/", 1)[-1]
    if total == "*":
        return None
    return int(total)


def _retryable(status_code: int) -> bool:
    return status_code >= 500


async def _request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
) -> httpx.Response:
    last_error: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            response = await client.get(url, headers=headers)
        except httpx.TransportError as exc:
            last_error = exc
        else:
            if not _retryable(response.status_code):
                return response
            last_error = MastFetchError(f"MAST responded {response.status_code}")
        if attempt < RETRY_ATTEMPTS - 1:
            await asyncio.sleep(RETRY_BACKOFF_SECONDS[attempt])
    raise MastFetchError("MAST range request failed") from last_error


async def probe_resource(client: httpx.AsyncClient, url: str) -> ResourceProbe:
    response = await _request_with_retry(client, url, {"Range": "bytes=0-0"})
    if response.status_code != 206:
        raise MastFetchError(f"MAST did not honor Range (status {response.status_code})")
    return ResourceProbe(
        total_bytes=_total_from_content_range(response.headers.get("content-range")),
        etag=response.headers.get("etag"),
        last_modified=response.headers.get("last-modified"),
        first_byte=response.content,
    )


async def read_range(client: httpx.AsyncClient, url: str, start: int, end_inclusive: int) -> bytes:
    response = await _request_with_retry(
        client,
        url,
        {"Range": f"bytes={start}-{end_inclusive}"},
    )
    if response.status_code == 416:
        return b""
    if response.status_code != 206:
        raise MastFetchError(f"MAST range failed with status {response.status_code}")
    return response.content


def identity_changed(
    *,
    stored_etag: str | None,
    stored_last_modified: str | None,
    stored_total: int | None,
    probe: ResourceProbe,
) -> bool:
    if stored_etag and probe.etag:
        return stored_etag != probe.etag
    if stored_last_modified and probe.last_modified and stored_total is not None:
        return stored_last_modified != probe.last_modified or stored_total != probe.total_bytes
    return False


def can_resume(probe: ResourceProbe, *, bytes_transferred: int) -> bool:
    if bytes_transferred <= 0:
        return True
    return bool(probe.etag or probe.last_modified)


ClientFactory = Callable[[], httpx.AsyncClient]
