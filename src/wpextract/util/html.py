from _warnings import warn
from typing import TypeVar, Union

def attr_concat(val: Union[str, list[str]]) -> str:
    """Concatenate attribute values if they are a list.

    Certain attributes (e.g. `class`) are multi-value and will be parsed as a list.

    This helper is used internally to resolve this issue with type checking. So long as you are
    mindful of which attributes are multi-value, it shouldn't be necessary in third-party code.

    Args:
        val: an attribute value or list of values

    Returns:
        the value or the values concatenated
    """
    if isinstance(val, list):
        return ' '.join(val)
    return val
