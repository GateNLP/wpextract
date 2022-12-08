from typing import List, Optional
from urllib.parse import urlparse, urlunparse

from extractor.extractors.data.links import LinkRegistry, ResolvableLink


def resolve_link(
    registry: LinkRegistry, link: ResolvableLink
) -> Optional[ResolvableLink]:
    """Find the linkable item from the registry the link refers to.

    Will not resolve a link if it already has a destination.

    Args:
        registry: A link registry.
        link: A resolvable link

    Returns:
        The resolved link.
    """
    if link.destination is not None:
        return link

    href_parsed = urlparse(link.href)
    if "preview_id" in href_parsed.query:
        href_parsed = href_parsed._replace(query="")
        href = urlunparse(href_parsed)
    else:
        href = link.href

    linkable = registry.query_link(href)

    if linkable is None:
        print(f"Could not find link {href}")
        return link

    link.destination = linkable

    return link


def resolve_links(
    registry: LinkRegistry, links: List[ResolvableLink]
) -> List[ResolvableLink]:
    """Resolve a list of links against the link registry.

    Args:
        registry: A link registry
        links: A list of resolvable links

    Returns:
        The list of resolvable links with destinations.
    """
    return [resolve_link(registry, link) for link in links]
