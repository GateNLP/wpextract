import urllib.parse
from typing import Optional

from langcodes import standardize_tag, tag_is_valid

from extractor.util.str import remove_ends

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

    if tag_is_valid(path_parts[0]) and not path_parts[0] in EXCLUDED_TAGS:
        return standardize_tag(path_parts[0])

    return None
