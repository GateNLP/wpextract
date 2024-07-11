import logging
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


def load_scrape(
    scrape_urls_files: dict[str, Path], link: str
) -> Optional[BeautifulSoup]:
    """Find, load and parse the scrape of a link.

    Args:
        scrape_urls_files: A dictionary of site URLs to scrape file paths
        link: The link of the page to find.

    Returns:
        The parsed document or None if it could not be found.
    """
    path = scrape_urls_files.get(link)

    if path is None:
        logging.debug(f'Unable to find scrape file for "{link}"')
        return None

    html_raw = path.read_text()
    doc = BeautifulSoup(html_raw, "lxml")
    return doc
