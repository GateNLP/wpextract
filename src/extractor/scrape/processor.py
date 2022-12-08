import urllib.parse
from typing import Optional

from bs4 import BeautifulSoup, SoupStrainer

self_url_strainer = SoupStrainer(["head", "link", "meta"])


def _is_url_valid(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)

    return all([parsed.scheme, parsed.netloc])


def get_link_canonical(doc: BeautifulSoup) -> Optional[str]:
    """Get the canonical link if present.

    Args:
        doc: The document to search

    Returns:
        The canonical link or None if not present.
    """
    link_canonical = doc.head.find("link", rel="canonical")

    if link_canonical is None or not link_canonical.has_attr("href"):
        return None

    url = link_canonical["href"]

    return url if _is_url_valid(url) else None


def get_og_url(doc: BeautifulSoup) -> Optional[str]:
    """Get the meta ``og:url`` if present.

    Args:
        doc: The doc to search

    Returns:
        The og:url or None if not present.
    """
    og_url = doc.head.find("meta", property="og:url")

    if og_url is None or not og_url.has_attr("content"):
        return None

    url = og_url["content"]

    return url if _is_url_valid(url) else None


def extract_self_url(doc: BeautifulSoup) -> Optional[str]:
    """Extract the document's URL from meta tags.

    Args:
        doc: The doc to search

    Returns:
        The document's URL or None if it could not be found.
    """
    link_canonical = get_link_canonical(doc)
    if link_canonical is not None:
        return link_canonical

    og_url = get_og_url(doc)
    if og_url is not None:
        return og_url

    return None
