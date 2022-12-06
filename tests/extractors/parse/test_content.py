from pathlib import Path

from bs4 import BeautifulSoup

from extractor.extractors.data.links import Link, ResolvableLink
from extractor.parse.content import extract_embeds, extract_links


def test_extract_links(datadir: Path):
    doc = BeautifulSoup((datadir / "links.html").read_text(), "lxml")

    internal, external = extract_links(doc, "https://example.org/home")

    print(internal)
    print(external)

    assert internal == [
        ResolvableLink(
            text="An internal link", href="https://example.org/link1", destination=None
        ),
        ResolvableLink(
            text="Another internal link",
            href="https://example.org/link2",
            destination=None,
        ),
        ResolvableLink(
            text="A relative internal link",
            href="https://example.org/link3",
            destination=None,
        ),
    ]

    assert external == [Link(text="An external link", href="https://gate.ac.uk")]


def test_extract_embeds(datadir: Path):
    doc = BeautifulSoup((datadir / "embeds.html").read_text(), "lxml")

    embeds = extract_embeds(doc)

    assert embeds == ["https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"]
