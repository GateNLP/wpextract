from pathlib import Path

from bs4 import BeautifulSoup
from wpextract.extractors.data.images import MediaUse, ResolvableMediaUse
from wpextract.extractors.data.links import Link, ResolvableLink
from wpextract.parse.content import (
    extract_content_data,
    extract_embeds,
    extract_images,
    extract_links,
)


def test_extract_links(datadir: Path):
    doc = BeautifulSoup((datadir / "links.html").read_text(), "lxml")

    internal, external = extract_links(doc, "https://example.org/home")

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


def test_extract_images(datadir: Path):
    doc = BeautifulSoup((datadir / "images.html").read_text(), "lxml")

    images = extract_images(doc, "https://example.org/home")

    assert images == [
        ResolvableMediaUse(
            src="https://example.org/justimg.png", alt="The alt text", caption=None
        ),
        ResolvableMediaUse(
            src="https://example.org/img-fig.png",
            alt="The alt text",
            caption="A caption",
        ),
        ResolvableMediaUse(
            src="https://example.org/relative-img.png",
            alt="A relative image",
            caption=None,
        ),
        MediaUse(
            src="https://example.com/external-img.png",
            alt="An external image",
            caption=None,
        ),
    ]


def test_extract_image_without_src(datadir: Path):
    doc = BeautifulSoup("<img alt='No src'>", "lxml")

    images = extract_images(doc, "https://example.org/home")

    assert images == [
        MediaUse(src="", alt="No src", caption=None),
    ]


def test_extract_content(datadir: Path):
    doc = BeautifulSoup((datadir / "content_extraction.html").read_text(), "lxml")
    content_series = extract_content_data(doc, "https://example.org/home")
    text = content_series[0]

    assert (
        text == "The first paragraph.\n"
        "The second paragraph.\n"
        "The third paragraph.\n"
        "Not in a paragraph.\n"
        "Heavily nested."
    )


def test_extract_content_br_newline(datadir: Path):
    doc = BeautifulSoup((datadir / "whitespace_br.html").read_text(), "lxml")

    content_series = extract_content_data(doc, "https://example.org/home")
    text = content_series[0]

    assert (
        text
        == "Before break\nAfter break. Don't break here.\nBefore break\nAfter break."
    )


def test_extract_content_whitespace_collapse(datadir: Path):
    doc = BeautifulSoup((datadir / "whitespace_collapse.html").read_text(), "lxml")

    content_series = extract_content_data(doc, "https://example.org/home")
    text = content_series[0]

    assert text == "First para.\nAfter empty.\nAfter gap in doc."
