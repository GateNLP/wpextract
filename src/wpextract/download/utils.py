import json
from collections.abc import Iterable
from typing import Any, Optional, Union
from urllib.parse import urlsplit, urlunsplit

from requests import Response


def get_by_id(
    value: list[Union[dict[Any, Any], None]], idx: Any
) -> Optional[dict[Any, Any]]:
    """Utility function to retrieve a value by and ID in a list of dicts.

    Args:
        value: the list of dicts to process
        idx: the id to get

    Returns:
        The matching value or None if no match is found
    """
    if value is None:
        return None
    for val in value:
        if val is None:
            continue
        if "id" in val.keys() and val["id"] == idx:
            return val
    return None


# Neat code part from https://codereview.stackexchange.com/questions/13027/joining-url-path-components-intelligently
def url_path_join(*parts: str) -> str:
    """Normalize url parts and join them with a slash.

    Args:
        parts: the parts of the url to join

    Returns:
        a normalized url

    """
    schemes, netlocs, paths, queries, fragments = zip(
        *(urlsplit(part) for part in parts)
    )
    scheme = first(schemes)
    netloc = first(netlocs)
    path = "/".join(x.strip("/") for x in paths if x)
    query = first(queries)
    fragment = first(fragments)
    return urlunsplit((scheme, netloc, path, query, fragment))


def first(sequence: Iterable[str], default: str = "") -> str:
    """Return the first element of an iterable sequence or a default value.

    Args:
        sequence: an iterable sequence.
        default: the value to return if the sequence is empty.

    Returns:
        The first element of an iterable sequence or a default value.
    """
    return next((x for x in sequence if x), default)


def get_content_as_json(response_obj: Response) -> Any:
    """Returns a json value even if a BOM is present in UTF-8 text.

    When a BOM is present (see issue #2), UTF-8 is not properly decoded by
    Response.json() method.


    Args:
        response_obj: a requests Response instance

    Returns:
        a decoded json object (list or dict)
    """
    if response_obj.content[:3] == b"\xef\xbb\xbf":  # UTF-8 BOM
        content = response_obj.content.decode("utf-8-sig")
        return json.loads(content)
    else:
        return response_obj.json()
