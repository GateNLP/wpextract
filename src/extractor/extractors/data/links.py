from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Linkable:
    """An item which can be linked to."""

    link: str
    data_type: str
    idx: str


@dataclass
class Link:
    """A link to a URL."""

    text: Optional[str]
    href: Optional[str]


@dataclass
class ResolvableLink(Link):
    """A link to a URL which can be looked up against known links."""

    destination: Optional[Linkable]


class LinkRegistry:
    """A collection of all known links on the site."""

    links: List[Linkable]

    def __init__(self):
        """Init a new registry."""
        self.links = []

    def add_linkable(self, url: str, data_type: str, idx: str) -> None:
        """Add a single linkable item to the registry.

        The URL will be compared later against a list of links that
        need to be resolved and the data type and IDX will be returned.

        Data types should be unique.
        IDXes should be unique within one or more data types.

        Args:
            url: The URL of the destination
            data_type: A unique identifier for this type of item.
            idx: A unique identifier within the data type.
        """
        self.links.append(Linkable(link=url, data_type=data_type, idx=idx))

    def add_linkables(self, data_type: str, links: List[str], idxes: List[str]) -> None:
        """Add multiple linkable items at once.

        Args:
            data_type: The data type for all items.
            links: A list of links. Must be the same length as idxes.
            idxes: A list of IDs. Must be the same length as links.

        Raises:
            ValueError: if the links and idxes lists are not the same length.

        """
        if len(links) != len(idxes):
            raise ValueError(
                f"Links and idxes must be same length ({len(links)} != {len(idxes)})"
            )

        for link, idx in zip(links, idxes):
            self.add_linkable(data_type=data_type, url=link, idx=idx)
