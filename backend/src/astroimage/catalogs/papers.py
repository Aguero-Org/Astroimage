from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request
from uuid import UUID, uuid4

import structlog
from sqlalchemy import DateTime, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from astroimage.shared.database import Base

_log = structlog.get_logger("astroimage.catalogs.ads")

ADS_QUERY_URL = "https://api.adsabs.harvard.edu/v1/search/query"
_ADS_TIMEOUT_S = 30.0
_ADS_BATCH_SIZE = 40
_USER_AGENT = "astroimage-catalogs/0.1 (+https://github.com/anomalyco/opencode)"


@dataclass(frozen=True)
class PaperIdentifier:
    bibcode: str | None = None
    doi: str | None = None

    @property
    def lookup_key(self) -> str | None:
        bibcode = (self.bibcode or "").strip()
        if bibcode:
            return bibcode
        doi = (self.doi or "").strip()
        if doi:
            return f"doi:{doi}"
        return None


@dataclass(frozen=True)
class PaperRecord:
    lookup_key: str
    bibcode: str | None = None
    doi: str | None = None
    title: str | None = None
    abstract: str | None = None


class PaperLookup(Protocol):
    def fetch(self, identifiers: Sequence[PaperIdentifier]) -> list[PaperRecord]: ...


class PaperMetadataStore(Protocol):
    async def find_fresh(self, keys: Sequence[str]) -> dict[str, PaperRecord]: ...

    async def save(self, records: Sequence[PaperRecord]) -> None: ...


class PaperMetadata(Base):
    __tablename__ = "paper_metadata"
    __table_args__ = (UniqueConstraint("lookup_key", name="uq_paper_metadata_lookup_key"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    lookup_key: Mapped[str] = mapped_column(String(256), nullable=False)
    bibcode: Mapped[str | None] = mapped_column(Text)
    doi: Mapped[str | None] = mapped_column(String(256))
    title: Mapped[str | None] = mapped_column(Text)
    abstract: Mapped[str | None] = mapped_column(Text)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AdsPaperLookup:
    def __init__(self, *, token: str, timeout_s: float = _ADS_TIMEOUT_S) -> None:
        self._token = token.strip()
        self._timeout_s = timeout_s

    def fetch(self, identifiers: Sequence[PaperIdentifier]) -> list[PaperRecord]:
        usable = [identifier for identifier in identifiers if identifier.lookup_key]
        if not usable:
            return []
        if not self._token:
            _log.info("ads_skipped", reason="missing token", count=len(usable))
            return []
        records: list[PaperRecord] = []
        bibcodes = [identifier for identifier in usable if identifier.bibcode]
        dois = [identifier for identifier in usable if not identifier.bibcode and identifier.doi]
        records.extend(self._fetch_field("bibcode", bibcodes))
        records.extend(self._fetch_field("doi", dois))
        return records

    def _fetch_field(self, field: str, identifiers: Sequence[PaperIdentifier]) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        for batch in _batches(identifiers, _ADS_BATCH_SIZE):
            payload = self._query(field, batch)
            if payload is None:
                continue
            records.extend(records_from_ads(batch, payload))
        return records

    def _query(self, field: str, identifiers: Sequence[PaperIdentifier]) -> dict[str, Any] | None:
        terms = [
            value
            for value in (_search_value(field, identifier) for identifier in identifiers)
            if value is not None
        ]
        if not terms:
            return None
        query = urllib_parse.urlencode(
            {
                "q": ads_query(field, terms),
                "fl": "bibcode,title,abstract,doi",
                "rows": str(len(terms)),
            }
        )
        request = urllib_request.Request(
            f"{ADS_QUERY_URL}?{query}",
            headers={
                "Authorization": f"Bearer {self._token}",
                "User-Agent": _USER_AGENT,
            },
        )
        try:
            with urllib_request.urlopen(request, timeout=self._timeout_s) as response:
                if getattr(response, "status", 200) != 200:
                    return None
                payload = response.read()
        except (urllib_error.URLError, TimeoutError, ValueError) as exc:
            _log.warning("ads_query_failed", field=field, count=len(terms), exc_info=exc)
            return None
        try:
            parsed = json.loads(payload.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            _log.warning("ads_query_failed", field=field, count=len(terms), exc_info=exc)
            return None
        if not isinstance(parsed, dict):
            return None
        return parsed


def identifiers_from_pairs(
    pairs: Sequence[tuple[str | None, str | None]],
) -> list[PaperIdentifier]:
    candidates = [
        PaperIdentifier(bibcode=_usable_bibcode(bibcode), doi=_usable_text(doi))
        for bibcode, doi in pairs
    ]
    unique: dict[str, PaperIdentifier] = {}
    for identifier in candidates:
        key = identifier.lookup_key
        if key is not None:
            unique.setdefault(key, identifier)
    return list(unique.values())


def ads_query(field: str, values: Sequence[str]) -> str:
    quoted = " OR ".join(_quoted(value) for value in values)
    return f"{field}:({quoted})"


def _index_ads_docs(
    docs: Iterable[object],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    documents = [doc for doc in docs if isinstance(doc, dict)]
    by_bibcode = {
        bibcode: doc
        for doc in documents
        if (bibcode := _usable_text(doc.get("bibcode"))) is not None
    }
    by_doi = {doi.lower(): doc for doc in documents for doi in _string_list(doc.get("doi"))}
    return by_bibcode, by_doi


def _doc_for_identifier(
    identifier: PaperIdentifier,
    by_bibcode: dict[str, dict[str, Any]],
    by_doi: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    doc = by_bibcode.get(identifier.bibcode or "")
    if doc is not None or not identifier.doi:
        return doc
    return by_doi.get(identifier.doi.lower())


def records_from_ads(
    identifiers: Sequence[PaperIdentifier],
    payload: dict[str, Any],
) -> list[PaperRecord]:
    response = payload.get("response")
    docs = response.get("docs", []) if isinstance(response, dict) else []
    by_bibcode, by_doi = _index_ads_docs(docs)
    return [
        _record_from_doc(
            identifier,
            key,
            _doc_for_identifier(identifier, by_bibcode, by_doi),
        )
        for identifier in identifiers
        if (key := identifier.lookup_key) is not None
    ]


def _record_from_doc(
    identifier: PaperIdentifier,
    lookup_key: str,
    doc: dict[str, Any] | None,
) -> PaperRecord:
    if doc is None:
        return PaperRecord(
            lookup_key=lookup_key,
            bibcode=identifier.bibcode,
            doi=identifier.doi,
        )
    dois = _string_list(doc.get("doi"))
    return PaperRecord(
        lookup_key=lookup_key,
        bibcode=_usable_text(doc.get("bibcode")) or identifier.bibcode,
        doi=dois[0] if dois else identifier.doi,
        title=_first_text(doc.get("title")),
        abstract=_first_text(doc.get("abstract")),
    )


def _search_value(field: str, identifier: PaperIdentifier) -> str | None:
    if field == "bibcode":
        return identifier.bibcode
    return identifier.doi


def _usable_bibcode(value: object) -> str | None:
    text = _usable_text(value)
    if text is None or "yCat" in text:
        return None
    return text


def _usable_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _first_text(value: object) -> str | None:
    if isinstance(value, str):
        return _usable_text(value)
    if not isinstance(value, list):
        return None
    return next((text for item in value if (text := _first_text(item)) is not None), None)


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _usable_text(value)
        return [text] if text else []
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _usable_text(item)) is not None]


def _quoted(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _batches[T](items: Sequence[T], size: int) -> list[list[T]]:
    return [list(items[start : start + size]) for start in range(0, len(items), size)]
