def remove_prefix(text: str, prefix: str):
    """If the text starts with the prefix, remove it.

    If the prefix is not present, the original string will be returned.

    Args:
        text: The string to process
        prefix: The prefix to remove

    Returns:
        The text with the given prefix removed.
    """
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def remove_suffix(text: str, suffix: str):
    """If the text ends with the suffix, remove it.

    If the suffix is not present, the original string will be returned.

    Args:
        text: The string to process
        suffix: The suffix to remove

    Returns:
        The text with the given prefix removed.
    """
    if text.endswith(suffix):
        return text[: -len(suffix)]
    return text


def remove_ends(text: str, affix: str):
    """If the text starts or ends with the affix, remove it.

    If the affix is not present, the original string will be returned.

    Args:
        text: The string to process
        affix: The prefix and suffix to remove

    Returns:
        The text with the prefix and suffix removed.
    """
    return remove_prefix(remove_suffix(text, affix), affix)


def ensure_suffix(text: str, suffix: str) -> str:
    """Ensure the text ends with the suffix.

    If it already ends with the suffix, the original string will be returned.

    Args:
        text: The string to process
        suffix: The suffix to add if not already present.

    Returns:
        The text with the given suffix.
    """
    if text[-len(suffix) :] != suffix:
        return text + suffix
    return text
