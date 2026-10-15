from __future__ import annotations

from astroimage.catalogs.readme import (
    ReadmeData,
    ads_url,
    catalogue_readme_candidates,
    clean_bibcode,
    clean_doi,
    determine_catalogue_bibcode,
    determine_paper_bibcode,
    determine_paper_doi,
    doi_url,
    extract_bibcodes,
    extract_dois,
    parse_readme,
)

_README = """Title: Gaia DR3 part 1. Main source
Authors: Gaia Collaboration
Keywords: surveys -- astrometry
Abstract: The Gaia catalogue of stars.
References:
 Gaia Collaboration 2016, A&A, 595, A1 (10.1051/0004-6361/201629272)
 2016A&A...595A...1G
"""


def test_clean_and_url_helpers_strip_noise() -> None:
    assert clean_doi("https://doi.org/10.1051/0004-6361/201629272.") == (
        "10.1051/0004-6361/201629272"
    )
    assert doi_url("doi: 10.1051/0004-6361/201629272") == (
        "https://doi.org/10.1051/0004-6361/201629272"
    )
    assert ads_url("2016A&A...595A...1G") == (
        "https://ui.adsabs.harvard.edu/abs/2016A&A...595A...1G/abstract"
    )
    assert clean_bibcode("2016A&A...595A...1G,") == "2016A&A...595A...1G"
    assert ads_url(None) is None
    assert doi_url("") is None


def test_extract_dois_and_bibcodes_deduplicate() -> None:
    text = "See 10.1051/0004-6361/201629272 and 10.1051/0004-6361/201629272 and 2016A&A...595A...1G"
    assert extract_dois(text) == ("10.1051/0004-6361/201629272",)
    assert extract_bibcodes(text) == ("2016A&A...595A...1G",)


def test_parse_readme_pulls_title_authors_and_references() -> None:
    readme = parse_readme(_README, url="https://cdsarc.cds.unistra.fr/ftp/cats/I/350/ReadMe")
    assert readme.title.startswith("Gaia DR3 part 1")
    assert readme.authors == "Gaia Collaboration"
    assert "10.1051/0004-6361/201629272" in readme.dois
    assert "2016A&A...595A...1G" in readme.bibcodes
    assert readme.url is not None


def test_readme_candidates_include_the_parent_catalogue() -> None:
    candidates = catalogue_readme_candidates("J/A+A/595/A1/table1")
    assert candidates[0] == "https://cdsarc.cds.unistra.fr/ftp/cats/J/A+A/595/A1/ReadMe"
    assert candidates[-1] == "https://cdsarc.cds.unistra.fr/ftp/cats/J/A+A/595/A1/table1/ReadMe"


def test_determine_bibcodes_prefers_origin_article_and_skips_ycat() -> None:
    readme = ReadmeData(
        bibcodes=("2016yCat....102025G",), reference_bibcodes=("2000A&A...357..265F",)
    )
    assert determine_catalogue_bibcode("2016A&A...595A...1G", readme) == "2016A&A...595A...1G"
    assert determine_catalogue_bibcode(None, readme) == "2016yCat....102025G"
    assert determine_paper_bibcode("2016yCat....102025G", readme) == "2000A&A...357..265F"
    assert determine_paper_bibcode("2016A&A...595A...1G", readme) == "2016A&A...595A...1G"


def test_determine_paper_doi_prefers_readme_reference_doi() -> None:
    readme = ReadmeData(reference_dois=("10.1051/0004-6361/201629272",))
    assert determine_paper_doi("2016A&A...595A...1G", readme, "10.0000/meta") == (
        "10.1051/0004-6361/201629272"
    )
    assert determine_paper_doi("", readme, "10.0000/meta") == ""
    assert determine_paper_doi("2016A&A...595A...1G", ReadmeData(), "10.0000/meta") == (
        "10.0000/meta"
    )
