from dataclasses import dataclass
from typing import Optional

from extractor.extractors.data.links import Linkable


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
