import pytest
from langcodes import Language

from extractor.util.locale import extract_locale


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.org", None),
        ("https://example.org/fr", "fr"),
        ("https://example.org/fr/slug", "fr"),
        ("https://example.org/fr-FR/slug", "fr-FR"),
        ("https://example.org/fr-fr/slug", "fr-FR"),
        ("https://example.org/tag/my-tag", None),
        ("https://example.org/fr/tag/my-tag", "fr")
    ]
)
def test_lang_extract(url, expected):
    assert extract_locale(url) == expected
