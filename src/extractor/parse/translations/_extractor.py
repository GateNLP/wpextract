import logging
from typing import List, Optional, Type

import pandas as pd
from bs4 import BeautifulSoup

import extractor.parse.translations._pickers as pickers

PICKERS = [pickers.Polylang, pickers.GenericLangSwitcher]
PickerListType = List[Type[pickers.LangPicker]]

PageTranslationData = pd.Series


def extract_translations(
    page_doc: Optional[BeautifulSoup],
    link: str,
    translation_pickers: Optional[PickerListType],
) -> PageTranslationData:
    """Get a list of URLs linked as translations.

    Args:
        page_doc: The full scrape document
        link: The link to the post
        translation_pickers: A list of translation pickers to use

    Returns:
        The doc's language and list of translation links
    """
    if translation_pickers is None:
        translation_pickers = PICKERS

    if page_doc is None:
        return pd.Series([None, []])
    for picker_class in translation_pickers:
        picker = picker_class(page_doc)

        if not picker.matches():
            continue

        picker.extract()

        return pd.Series([picker.current_language, picker.translations])

    logging.debug(
        f'No translation pickers matched "{link}", unable to extract translations.'
    )

    return pd.Series([None, []])
