import pytest
from bs4 import BeautifulSoup
from wpextract.scrape.processor import (
    _is_url_valid,
    extract_self_url,
    get_link_canonical,
    get_og_url,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.org/", True),
        ("http://example.org/", True),
        ("/", False),
        ("notaurl", False),
    ],
)
def test_url_valid(url, expected):
    assert _is_url_valid(url) == expected


@pytest.mark.parametrize(
    ("file", "exp_out"),
    [
        ("link_canonical.html", "https://example.org/page_canon/"),
        ("link_canonical_no_href.html", None),
        ("link_canonical_empty_href.html", None),
        ("no_head.html", None),
        ("og_url.html", None),
    ],
)
def test_get_link_canonical(datadir, file, exp_out):
    soup = BeautifulSoup((datadir / file).read_text(), "lxml")
    assert get_link_canonical(soup) == exp_out


@pytest.mark.parametrize(
    ("file", "exp_out"),
    [
        ("og_url.html", "https://example.org/page_og/"),
        ("og_url_no_content.html", None),
        ("og_url_empty_content.html", None),
        ("no_head.html", None),
        ("link_canonical.html", None),
    ],
)
def test_get_og_url(datadir, file, exp_out):
    soup = BeautifulSoup((datadir / file).read_text(), "lxml")
    assert get_og_url(soup) == exp_out


@pytest.mark.parametrize(
    ("file", "exp_out"),
    [
        ("link_canonical.html", "https://example.org/page_canon/"),
        ("og_url.html", "https://example.org/page_og/"),
        ("self_url_both.html", "https://example.org/page_canon/"),
        ("no_self_url.html", None),
    ],
)
def test_extract_self_url(datadir, file, exp_out):
    soup = BeautifulSoup((datadir / file).read_text(), "lxml")
    assert extract_self_url(soup) == exp_out
