from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import takewhile
from typing import Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

import structlog

_log = structlog.get_logger("astroimage.catalogs.readme")

ADS_ABSTRACT_URL = "https://ui.adsabs.harvard.edu/abs/{bibcode}/abstract"
DOI_URL = "https://doi.org/{doi}"
CDS_README_URL = "https://cdsarc.cds.unistra.fr/ftp/cats/{catalogue_id}/ReadMe"
_README_TIMEOUT_S = 30.0
_USER_AGENT = "astroimage-catalogs/0.1 (+https://github.com/anomalyco/opencode)"

_DOI_PATTERN = re.compile(
    r"(?:https?://doi\.org/|doi:\s*)?(10\.\d{4,9}/[^\s<>\"']+)", re.IGNORECASE
)
_BIBCODE_PATTERN = re.compile(r"\b\d{4}[A-Za-z&.]{4,}\d{2,4}[A-Za-z0-9.]*[A-Za-z]\b")
_TITLE_SKIP_PREFIXES = (
    "Byte-by-byte",
    "File Summary",
    "Keywords:",
    "ADC_Keywords:",
    "Description:",
    "Abstract:",
    "References:",
    "Tables:",
    "Acknowledgements:",
    "Bibliography:",
)
_REFERENCE_SECTIONS = (
    "References:",
    "Reference:",
    "Bibliography:",
    "Bibliography",
    "References",
)


@dataclass(frozen=True)
class ReadmeData:
    """Parsed contents of a CDS catalogue ReadMe."""

    url: str | None = None
    title: str = ""
    authors: str = ""
    bibcodes: tuple[str, ...] = ()
    dois: tuple[str, ...] = ()
    reference_bibcodes: tuple[str, ...] = ()
    reference_dois: tuple[str, ...] = ()
    keywords: str = ""
    description: str = ""
    abstract: str = ""
    objects: str = ""
    references: str = ""


class ReadmeFetcher(Protocol):
    def fetch(self, catalogue_id: str) -> ReadmeData | None: ...


def clean_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_bibcode(value: object) -> str:
    return clean_text(value).strip(".,;)]}")


def is_ycat_bibcode(bibcode: str) -> bool:
    return "yCat" in bibcode


def ads_url(bibcode: str | None) -> str | None:
    cleaned = clean_bibcode(bibcode or "")
    if not cleaned:
        return None
    return ADS_ABSTRACT_URL.format(bibcode=cleaned)


def clean_doi(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = re.sub(r"^https?://doi\.org/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    return text.rstrip(".,;)]}")


def doi_url(value: str | None) -> str | None:
    cleaned = clean_doi(value)
    if not cleaned:
        return None
    return DOI_URL.format(doi=cleaned)


def _unique_texts(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def extract_dois(text: str) -> tuple[str, ...]:
    return _unique_texts(clean_doi(match) for match in _DOI_PATTERN.findall(text or ""))


def extract_bibcodes(text: str) -> tuple[str, ...]:
    return _unique_texts(clean_bibcode(match) for match in _BIBCODE_PATTERN.findall(text or ""))


def catalogue_readme_candidates(catalogue_id: str) -> tuple[str, ...]:
    catalogue_id = catalogue_id.strip("/")
    parts = catalogue_id.split("/")
    candidates: list[str] = []
    if len(parts) >= 3:
        parent = "/".join(parts[:-1])
        candidates.append(CDS_README_URL.format(catalogue_id=parent))
    candidates.append(CDS_README_URL.format(catalogue_id=catalogue_id))
    return tuple(dict.fromkeys(candidates))


def _starts_next_section(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and not line.startswith(" ") and stripped.endswith(":")


def extract_section(readme: str, section_names: tuple[str, ...]) -> str:
    lines = readme.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() in section_names), None)
    if start is None:
        return ""
    body = takewhile(
        lambda line: line.strip() in section_names or not _starts_next_section(line),
        lines[start + 1 :],
    )
    kept = (
        stripped for line in body if (stripped := line.strip()) and stripped not in section_names
    )
    return clean_text(" ".join(kept))


def _title_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith(_TITLE_SKIP_PREFIXES) or set(stripped) <= set("-=_"):
        return ""
    return stripped


def extract_title(readme: str) -> str:
    first = next(filter(None, map(_title_line, readme.splitlines())), "")
    if not first:
        return ""
    title = clean_text(first)
    return re.sub(r"^Title\s*[:=]\s*", "", title, flags=re.IGNORECASE).strip()


def extract_authors(readme: str) -> str:
    labeled = next(
        (line.strip() for line in readme.splitlines() if line.strip().startswith("Authors:")),
        None,
    )
    if labeled is not None:
        return clean_text(labeled.split(":", 1)[1])
    collaboration = next(
        (line for line in readme.splitlines() if "gaia collaboration" in line.lower()),
        None,
    )
    if collaboration is None:
        return ""
    return clean_text(collaboration)


def extract_reference_blocks(readme: str) -> str:
    blocks = [extract_section(readme, (section,)) for section in _REFERENCE_SECTIONS]
    return "\n".join(block for block in blocks if block)


def parse_readme(readme: str, *, url: str | None = None) -> ReadmeData:
    references = extract_reference_blocks(readme)
    return ReadmeData(
        url=url,
        title=extract_title(readme),
        authors=extract_authors(readme),
        bibcodes=extract_bibcodes(readme),
        dois=extract_dois(readme),
        reference_bibcodes=extract_bibcodes(references),
        reference_dois=extract_dois(references),
        keywords=extract_section(readme, ("Keywords:",)),
        description=extract_section(readme, ("Description:",)),
        abstract=extract_section(readme, ("Abstract:",)),
        objects=extract_section(readme, ("Objects:",)),
        references=references,
    )


def determine_catalogue_bibcode(metadata_origin_article: str | None, readme: ReadmeData) -> str:
    origin = clean_bibcode(metadata_origin_article or "")
    if origin:
        return origin
    return next((code for code in readme.bibcodes if is_ycat_bibcode(code)), "")


def _first_paper_bibcode(codes: tuple[str, ...]) -> str:
    return next(
        (
            cleaned
            for code in codes
            if (cleaned := clean_bibcode(code)) and not is_ycat_bibcode(cleaned)
        ),
        "",
    )


def determine_paper_bibcode(metadata_origin_article: str | None, readme: ReadmeData) -> str:
    origin = clean_bibcode(metadata_origin_article or "")
    if origin and not is_ycat_bibcode(origin):
        return origin
    return _first_paper_bibcode(readme.reference_bibcodes) or _first_paper_bibcode(readme.bibcodes)


def _present_dois(dois: tuple[str, ...]) -> list[str]:
    return [doi for doi in map(clean_doi, dois) if doi]


def _bibcode_near(references: str, doi: str, bibcode: str) -> bool:
    position = references.find(doi)
    if position < 0:
        return False
    start = max(0, position - 500)
    end = min(len(references), position + 500)
    return bibcode in references[start:end]


def _doi_near_bibcode(dois: list[str], references: str, bibcode: str) -> str:
    if len(dois) == 1:
        return dois[0]
    return next((doi for doi in dois if _bibcode_near(references, doi, bibcode)), "")


def determine_paper_doi(
    paper_bibcode: str | None,
    readme: ReadmeData,
    metadata_doi: str | None,
) -> str:
    if not paper_bibcode:
        return ""
    cleaned_bibcode = clean_bibcode(paper_bibcode)
    from_references = _doi_near_bibcode(
        _present_dois(readme.reference_dois),
        readme.references,
        cleaned_bibcode,
    )
    if from_references:
        return from_references
    from_readme = _present_dois(readme.dois)
    if len(from_readme) == 1:
        return from_readme[0]
    return clean_doi(metadata_doi)


class CdsReadmeFetcher:
    """Downloads and parses a catalogue ReadMe from CDS over HTTP."""

    def __init__(self, *, timeout_s: float = _README_TIMEOUT_S) -> None:
        self._timeout_s = timeout_s

    def fetch(self, catalogue_id: str) -> ReadmeData | None:
        for url in catalogue_readme_candidates(catalogue_id):
            text = self._download(url)
            if text is None:
                continue
            return parse_readme(text, url=url)
        _log.info("readme_not_found", catalogue_id=catalogue_id)
        return None

    def _download(self, url: str) -> str | None:
        request = urllib_request.Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib_request.urlopen(request, timeout=self._timeout_s) as response:
                if getattr(response, "status", 200) != 200:
                    return None
                payload: bytes = response.read()
        except (urllib_error.URLError, TimeoutError, ValueError):
            return None
        text = payload.decode("utf-8", errors="replace")
        if "<html" in text.lower() or len(text.strip()) < 50:
            return None
        _log.debug("readme_downloaded", url=url, bytes=len(payload))
        return text
