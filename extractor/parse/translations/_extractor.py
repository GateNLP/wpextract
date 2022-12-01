from typing import List, Optional

import pandas as pd
from bs4 import BeautifulSoup
from langcodes import Language

import extractor.parse.translations._pickers as pickers
from extractor.parse.translations._resolver import TranslationLink

RESOLVERS = [pickers.Polylang, pickers.GenericLangSwitcher]

PageTranslationData = pd.Series[Optional[Language], Optional[List[TranslationLink]]]


def extract_translations(page_doc: Optional[BeautifulSoup]) -> PageTranslationData:
    """Get a list of URLs linked as translations.

    Args:
        page_doc: The full scrape document

    Returns:
        The doc's language and list of translation links
    """
    if page_doc is None:
        return pd.Series([None, None])
    for resolver_class in RESOLVERS:
        resolver = resolver_class(page_doc)

        if not resolver.matches():
            continue

        return pd.Series([resolver.current_language, resolver.translations])

    return pd.Series([None, None])
