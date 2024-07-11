import copy
import logging
from urllib.parse import urljoin, urlparse, urlunparse

import pandas as pd
from bs4 import BeautifulSoup, Comment, NavigableString

from wpextract.extractors.data.images import MediaUse, ResolvableMediaUse
from wpextract.extractors.data.links import Link, ResolvableLink
from wpextract.extractors.media import get_caption
from wpextract.util.str import squash_whitespace

EXCLUDED_CONTENT_TAGS = {"figcaption"}
NEWLINE_TAGS = {"br", "p"}


InternalLinks = list[ResolvableLink]
ExternalLinks = list[Link]


def extract_links(
    doc: BeautifulSoup, self_link: str
) -> tuple[InternalLinks, ExternalLinks]:
    """Get the internal and external links of the document.

    Args:
        doc: A parsed document
        self_link: The link of the page

    Returns:
        A list of internal and a list of external link objects.
    """
    internal_links = []
    external_links = []

    links = doc.find_all("a")

    self_link_parsed = urlparse(self_link)

    for link in links:
        if not link.has_attr("href"):
            external_links.append(Link(squash_whitespace(link.get_text()), None))
            continue

        href_parsed = urlparse(urljoin(self_link, link["href"]))
        if href_parsed.netloc == self_link_parsed.netloc:
            internal_links.append(
                ResolvableLink(
                    text=squash_whitespace(link.get_text()),
                    href=urlunparse(href_parsed),
                    destination=None,
                )
            )
        else:
            external_links.append(
                Link(text=squash_whitespace(link.get_text()), href=link["href"])
            )

    return internal_links, external_links


Embeds = list[str]


def extract_embeds(doc: BeautifulSoup) -> Embeds:
    """Get a list of URLs embedded in the page.

    Args:
        doc: A parsed document.

    Returns:
        A list of URLs
    """
    return [iframe["src"] for iframe in doc.find_all("iframe")]


Images = list[MediaUse]


def extract_images(doc: BeautifulSoup, self_link: str) -> Images:
    """Get a list of images in the document.

    Args:
        doc: A parsed document
        self_link: The link of the page.

    Returns:
        A list of MediaUse objects. Internal images are returned as ResolvableMedia.
    """
    images = doc.find_all("img")

    media_uses = []

    self_link_parsed = urlparse(self_link)

    for img in images:
        if not img.has_attr("src"):
            logging.warning(f"Image without source in {self_link}")
            media_uses.append(
                MediaUse(src="", alt=img.get("alt"), caption=get_caption(img))
            )
            continue

        src_parsed = urlparse(urljoin(self_link, img["src"]))

        media_data = {
            "src": urlunparse(src_parsed),
            "alt": img.get("alt"),
            "caption": get_caption(img),
        }

        if src_parsed.netloc == self_link_parsed.netloc:
            media_uses.append(ResolvableMediaUse(**media_data))
        else:
            media_uses.append(MediaUse(**media_data))

    return media_uses


def _get_text(doc: BeautifulSoup) -> str:
    """Custom function to get document text.

    Extracts text from all elements, inserting newlines for <p> and <br> tags.
    """
    text = ""
    for e in doc.descendants:
        # Comments are a subtype of NavigableString, they need to be excluded
        if isinstance(e, NavigableString) and not isinstance(e, Comment):
            text += e
        elif e.name in NEWLINE_TAGS:
            text += "\n"
    return text


def extract_content_data(doc: BeautifulSoup, self_link: str) -> pd.Series:
    """Extract the links, embeds, images and text content of the document.

    Args:
        doc: A parsed document.
        self_link: The URL of the page.

    Returns:
        A series with the text, internal links, external links, embeds and images.
    """
    internal_links, external_links = extract_links(doc, self_link)
    embeds = extract_embeds(doc)
    images = extract_images(doc, self_link)

    doc_c = copy.copy(doc)
    for child in doc_c.descendants:
        if type(child) == NavigableString:
            continue

        if child.name in EXCLUDED_CONTENT_TAGS:
            child.extract()

    content_text = squash_whitespace(_get_text(doc_c))

    return pd.Series([content_text, internal_links, external_links, embeds, images])
