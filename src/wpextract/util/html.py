from _warnings import warn
from typing import TypeVar, Union

T = TypeVar("T")


def attribute_list_guard(val: Union[T, list[T]]) -> T:
    """Type guard for processing attribute values.

    Accessing the value of a BeautifulSoup tag attribute may return a list of values. This function
    will return a single value or the first of a list of values.

    If the list of values has more than one unique value, a warning will be issued.

    Args:
        val: an attribute value or list of values

    Returns:
        the value or the first value in the list
    """
    if isinstance(val, list):
        if len(set(val)) > 1:
            warn(f"Attribute had multiple values ({val}), using first")
        return val[0]
    return val
