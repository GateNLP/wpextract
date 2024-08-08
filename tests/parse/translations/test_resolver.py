from typing import Union

import pytest
from langcodes import Language
from wpextract.parse.translations import TranslationLink


@pytest.mark.parametrize(
    ("input_lang", "expected_language"),
    [
        ("en", "en"),
        ("en-GB", "en-GB"),
        ("fr-FR", "fr-FR"),
        (Language.get("en-GB"), "en-GB"),
        ("zho", "zh"),
    ],
)
def test_translation_link_lang(
    input_lang: Union[str, Language], expected_language: str
):
    link = TranslationLink(text=None, href=None, destination=None, lang=input_lang)

    assert str(link.language) == expected_language
