import copy
import urllib.parse
from typing import List, Tuple

import pandas as pd
from bs4 import BeautifulSoup, NavigableString

from extractor.extractors.data.images import MediaUse, ResolvableMediaUse, get_caption
from extractor.extractors.data.links import Link, ResolvableLink

EXCLUDED_CONTENT_TAGS = {"figcaption"}

InternalLinks = List[ResolvableLink]
ExternalLinks = List[Link]


def extract_links(
    doc: BeautifulSoup, self_netloc: str
) -> Tuple[InternalLinks, ExternalLinks]:
    """Get the internal and external links of the document.

    Args:
        doc: A parsed document
        self_netloc: The netloc that should be considered internal

    Returns:
        A list of internal and a list of external link objects.
    """
    internal_links = []
    external_links = []

    links = doc.find_all("a")

    for link in links:
        if not link.has_attr("href"):
            external_links.append(Link(link.get_text(), None))
            continue

        href_parsed = urllib.parse.urlparse(link["href"])

        if href_parsed.netloc == self_netloc:
            internal_links.append(
                ResolvableLink(
                    text=link.get_text(), href=link["href"], destination=None
                )
            )
        else:
            external_links.append(Link(text=link.get_text(), href=link["href"]))

    return internal_links, external_links


Embeds = List[str]


def extract_embeds(doc: BeautifulSoup) -> Embeds:
    """Get a list of URLs embedded in the page.

    Args:
        doc: A parsed document.

    Returns:
        A list of URLs
    """
    return [iframe["src"] for iframe in doc.find_all("iframes")]


Images = List[MediaUse]


def extract_images(doc: BeautifulSoup, self_netloc: str) -> Images:
    """Get a list of images in the document.

    Args:
        doc: A parsed document
        self_netloc: The netloc of the page.

    Returns:
        A list of MediaUse objects. Internal images are returned as ResolvableMedia.
    """
    images = doc.find_all("img")

    media_uses = []

    for img in images:
        src_parsed = urllib.parse.urlparse(img["src"])

        media_data = {
            "src": img["src"],
            "alt": img.get("alt"),
            "caption": get_caption(img),
        }

        if src_parsed.netloc == self_netloc:
            media_uses.append(ResolvableMediaUse(**media_data))
        else:
            media_uses.append(MediaUse(**media_data))

    return media_uses


def extract_content_data(doc: BeautifulSoup, self_link: str) -> pd.Series:
    """Extract the links, embeds, images and text content of the document.

    Args:
        doc: A parsed document.
        self_link: The URL of the page.

    Returns:
        A series with the text, internal links, external links, embeds and images.
    """
    self_netloc = urllib.parse.urlparse(self_link).netloc

    internal_links, external_links = extract_links(doc, self_netloc)
    embeds = extract_embeds(doc)
    images = extract_images(doc, self_netloc)

    doc_c = copy.copy(doc)
    for child in doc_c.children:
        if type(child) == NavigableString:
            continue

        if child.name in EXCLUDED_CONTENT_TAGS:
            child.extract()

    content_text = doc_c.get_text()

    return pd.Series([content_text, internal_links, external_links, embeds, images])
