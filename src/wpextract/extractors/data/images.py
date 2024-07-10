import logging
import re
from dataclasses import dataclass
from typing import Optional

from wpextract.extractors.data.links import Linkable, LinkRegistry


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


def resolve_image(
    registry: LinkRegistry, image: ResolvableMediaUse
) -> ResolvableMediaUse:
    """Resolve the internal links of a media use.

    Args:
        registry: A filled link registry
        image: A media use

    Returns:
        The media use with link data resolved.
    """
    if image.destination is not None:
        return image

    if "wp-content" not in image.src:
        return image

    # Remove dimensions from image URL
    # e.g. test-image-300x200.jpg -> test-image.jpg
    src = re.sub(r"-\d{3,4}x\d{3,4}\.", ".", image.src)

    linkable = registry.query_link(src)

    if linkable is None:
        logging.debug(f'Could not resolve image "{src}"')
        return image

    image.destination = linkable

    return image


def resolve_images(
    registry: LinkRegistry, images: list[ResolvableMediaUse]
) -> list[ResolvableMediaUse]:
    """Resolve the internal links of a list of media uses.

    Args:
        registry: A filled link registry
        images: A list of media uses

    Returns:
        The list of media uses with link data resolved.
    """
    return [resolve_image(registry, image) for image in images]
