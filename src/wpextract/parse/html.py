import re

from bs4 import BeautifulSoup

from wpextract.util.str import squash_whitespace

PROBABLY_HTML = re.compile(r"<|&\S+;")


def parse_html(html: str) -> BeautifulSoup:
    """Helper to parse HTML into a BeautifulSoup document.

    Args:
        html: an HTML document as a string.

    Returns:
        The parsed document
    """
    return BeautifulSoup(html, "lxml")


def extract_html_text(html: str) -> str:
    """Extract text from an HTML document.

    Will skip parsing if the document does not contain "<" or an HTML-entity-like
    sequence ("&" followed by some characters and a ";")

    Args:
        html: A string containing HTML.

    Returns:
        The extracted text from the document
    """
    if PROBABLY_HTML.search(html) is None:
        return html

    return squash_whitespace(parse_html(html).get_text())
