from pathlib import Path

import pytest
import wpextract.parse.translations._pickers as pickers
from bs4 import BeautifulSoup
from langcodes import Language
from wpextract.parse.translations._resolver import TranslationLink


@pytest.mark.parametrize(
    ("picker_cls", "picker_file"),
    [
        (pickers.PolylangWidget, "polylang_widget.html"),
        (pickers.PolylangCustomDropdown, "polylang_custom_dropdown.html"),
    ],
)
def test_picker(datadir: Path, picker_cls: type[pickers.LangPicker], picker_file: str):
    doc = BeautifulSoup((datadir / picker_file).read_text(), "lxml")

    picker = picker_cls(doc)

    assert picker.matches()
    picker.extract()
    assert len(picker.translations) == 1
    assert (
        picker.current_language.language
        == Language.get("en-US", normalize=True).language
    )

    assert picker.translations[0] == TranslationLink(
        text=None,
        href="https://example.org/fr/translation-page/",
        destination=None,
        lang="fr-FR",
    )


class FaultyExtractPickerSelect(pickers.PolylangWidget):
    def extract(self) -> None:
        self._root_select(".not-a-real-element")


class FaultyExtractPickerSelectOne(pickers.PolylangWidget):
    def extract(self) -> None:
        self._root_select_one(".not-a-real-element")


@pytest.mark.parametrize(
    "picker_cls", [FaultyExtractPickerSelect, FaultyExtractPickerSelectOne]
)
def test_picker_extract_error(datadir: Path, picker_cls: type[pickers.LangPicker]):
    doc = BeautifulSoup((datadir / "polylang_widget.html").read_text(), "lxml")

    picker = picker_cls(doc)
    assert picker.matches()

    with pytest.raises(pickers.ExtractionFailedError):
        picker.extract()
