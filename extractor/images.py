from dataclasses import dataclass
from typing import Optional

from bs4 import Tag

from extractor.links import Linkable


def get_caption(img: Tag) -> Optional[str]:
    """Get the caption of an image tag.

    Searches adjacent tags for a <figcaption>.

    TODO: A heuristic to find likely non-figcaption captions.

    Raises:
        ValueError: if a non-image tag is passed.

    Args:
        img: An img tag

    Returns:
        The caption text or None if there is no caption.
    """
    if img.name != "img":
        raise ValueError("Attempting to get caption of non-image")

    caption = img.parent.find("figcaption")

    if caption is None:
        return None

    return caption.get_text()


@dataclass
class MediaUse:
    """An instance of media being used."""

    src: str
    alt: str
    caption: Optional[str]


@dataclass
class ResolvableMediaUse(MediaUse):
    """An instance of media that can be resolved against known media."""

    destination: Optional[Linkable] = None
