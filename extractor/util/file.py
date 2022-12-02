from typing import Optional


def prefix_filename(file_name: str, prefix: Optional[str]):
    """Adds an optional prefix to the file name.

    If the prefix is ``None``, no prefix will be added.

    Args:
        file_name: The base file name.
        prefix: A prefix, or ``None``.

    Returns:
        The file name with prefix.
    """
    if prefix is None:
        prefix = ""

    return prefix + file_name
