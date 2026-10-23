from __future__ import annotations

import pytest

from astroimage.catalogs.papers import (
    AdsPaperLookup,
    PaperIdentifier,
    ads_query,
    identifiers_from_pairs,
    records_from_ads,
)

_BIBCODE = "2016A&A...595A...1G"
_DOI = "10.1051/0004-6361/201629272"


def test_identifiers_skip_blank_and_catalogue_bibcodes() -> None:
    identifiers = identifiers_from_pairs(
        [
            (_BIBCODE, _DOI),
            ("  ", None),
            ("2016yCat.1234....0G", None),
            (_BIBCODE, None),
            (None, _DOI),
        ]
    )

    assert [identifier.lookup_key for identifier in identifiers] == [_BIBCODE, f"doi:{_DOI}"]


def test_ads_query_quotes_each_value() -> None:
    assert ads_query("bibcode", [_BIBCODE, "2018A&A...616A...1G"]) == (
        'bibcode:("2016A&A...595A...1G" OR "2018A&A...616A...1G")'
    )


def test_records_from_ads_reads_title_and_caches_a_miss() -> None:
    found = PaperIdentifier(bibcode=_BIBCODE)
    missing = PaperIdentifier(bibcode="2018A&A...616A...1G")
    records = records_from_ads(
        [found, missing],
        {
            "response": {
                "docs": [
                    {
                        "bibcode": _BIBCODE,
                        "title": [" Gaia Data Release 1 "],
                        "abstract": "Summary of the release.",
                        "doi": [_DOI],
                    }
                ]
            }
        },
    )

    assert records[0].title == "Gaia Data Release 1"
    assert records[0].abstract == "Summary of the release."
    assert records[0].doi == _DOI
    assert records[1].title is None
    assert records[1].lookup_key == "2018A&A...616A...1G"


def test_ads_lookup_skips_the_network_without_a_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("urlopen")

    monkeypatch.setattr("astroimage.catalogs.papers.urllib_request.urlopen", fail_open)

    records = AdsPaperLookup(token="  ").fetch([PaperIdentifier(bibcode=_BIBCODE)])

    assert records == []
