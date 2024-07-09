import urllib.parse
from typing import Optional

from langcodes import Language, tag_is_valid

from wpextract.util.str import remove_ends

EXCLUDED_TAGS = {"tag"}  # Tagoi


def extract_locale(link: str) -> Optional[str]:
    """Extract a locale string from a URL.

    Returns the string standardised into a common format.

    Examples:
        >>> extract_locale("https://example.org/news/foo")
        None

        >>> extract_locale("https://example.org/en/foo")
        "en"

        >>> extract_locale("https://example.org/en-gb/foo")
        "en-GB"

    Args:
        link: A URL

    Returns:
        A standardised locale.
    """
    parsed_link = urllib.parse.urlparse(link)
    path_stripped = remove_ends(parsed_link.path, "/")
    path_parts = path_stripped.split("/")
    if tag_is_valid(path_parts[0]) and path_parts[0] not in EXCLUDED_TAGS:
        lang = Language.get(path_parts[0], normalize=True)
        if lang.extensions is not None:
            # Language tag extensions are very unlikely to be used
            # Probably a mis-parse
            return None

        lang.prefer_macrolanguage()
        return lang.simplify_script().to_tag()

    return None
