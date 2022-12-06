from typing import Optional

import pandas as pd
from bs4 import BeautifulSoup

import extractor.parse.translations._pickers as pickers

RESOLVERS = [pickers.Polylang, pickers.GenericLangSwitcher]

PageTranslationData = pd.Series


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

        resolver.extract()

        return pd.Series([resolver.current_language, resolver.translations])

    return pd.Series([None, None])
