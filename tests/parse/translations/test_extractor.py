import logging

import pytest
from bs4 import BeautifulSoup
from wpextract.parse.translations import extract_translations
from wpextract.parse.translations._pickers import PolylangCustomDropdown, PolylangWidget


class FaultyDummyPicker(PolylangWidget):
    def extract(self) -> None:
        raise self._build_extraction_fail_err(".dummy")


@pytest.fixture()
def parsed_page(shared_datadir):
    soup = BeautifulSoup((shared_datadir / "polylang_widget.html").read_text(), "lxml")
    return soup


def test_extract_translations(parsed_page):
    res = extract_translations(
        parsed_page, "https://example.org/current-lang-page/", translation_pickers=None
    )

    assert str(res.iloc[0]) == "en-US"
    assert len(res.iloc[1]) == 1


def test_none_matching(caplog, parsed_page):
    with caplog.at_level(logging.DEBUG):
        res = extract_translations(
            parsed_page,
            "https://example.org/current-lang-page/",
            translation_pickers=[PolylangCustomDropdown],
        )
    assert res.iloc[0] is None
    assert res.iloc[1] == []

    assert "No translation pickers matched" in caplog.text


def test_error_extracting(caplog, parsed_page):
    res = extract_translations(
        parsed_page,
        "https://example.org/current-lang-page/",
        translation_pickers=[FaultyDummyPicker],
    )

    assert res.iloc[0] is None
    assert "but failed to select element with: .dummy" in caplog.text
