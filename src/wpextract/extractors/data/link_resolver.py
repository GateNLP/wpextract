import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

from wpextract.extractors.data.links import LinkRegistry, ResolvableLink
from wpextract.util.str import remove_ends


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
        # Heuristic to fix case when category slug has been removed from URL
        path_parts = remove_ends(href_parsed.path, "/").split("/")

        lang = None
        # Case /fr/category/article/
        if len(path_parts) == 3 and (len(path_parts[0]) == 2):
            lang = path_parts.pop(0)

        # Case /category/an-article-slug/
        if len(path_parts) == 2:
            path_parts.pop(0)
            if lang is not None:
                path_parts.insert(0, lang)
            whole_path = f"/{'/'.join(path_parts)}/"
            href_parsed = href_parsed._replace(path=whole_path)
            url = urlunparse(href_parsed)
            linkable = registry.query_link(url)

            if linkable is None:
                logging.debug(
                    f'Could not resolve with category removal heuristic: "{url}"'
                )

    if linkable is None:
        logging.debug(f'Could not resolve link "{href}"')
        return link

    link.destination = linkable

    return link


def resolve_links(
    registry: LinkRegistry, links: list[ResolvableLink]
) -> list[ResolvableLink]:
    """Resolve a list of links against the link registry.

    Args:
        registry: A link registry
        links: A list of resolvable links

    Returns:
        The list of resolvable links with destinations.
    """
    return [resolve_link(registry, link) for link in links]
