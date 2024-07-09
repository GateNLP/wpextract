"""Copyright (c) 2018-2020 Mickaël "Kilawyn" Walter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import json
from urllib.parse import urlsplit, urlunsplit


def get_by_id(value, id):
    """Utility function to retrieve a value by and ID in a list of dicts.

    Args:
        value: the dict to process
        id: the id to get

    Returns:
        The matching value or None if no match is found
    """
    if value is None:
        return None
    for val in value:
        if "id" in val.keys() and val["id"] == id:
            return val
    return None


# Neat code part from https://codereview.stackexchange.com/questions/13027/joini
# ng-url-path-components-intelligently
def url_path_join(*parts):
    """Normalize url parts and join them with a slash."""
    schemes, netlocs, paths, queries, fragments = zip(
        *(urlsplit(part) for part in parts)
    )
    scheme = first(schemes)
    netloc = first(netlocs)
    path = "/".join(x.strip("/") for x in paths if x)
    query = first(queries)
    fragment = first(fragments)
    return urlunsplit((scheme, netloc, path, query, fragment))


def first(sequence, default=""):
    return next((x for x in sequence if x), default)


def get_content_as_json(response_obj):
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
        try:
            return response_obj.json()
        except:  # noqa: E722
            return {}
