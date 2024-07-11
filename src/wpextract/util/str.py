import re

ADJACENT_NEWLINE_REGEX = re.compile("\n{2,}")
WHITESPACE_LINE_STARTING_REGEX = re.compile(r"^\s+", re.MULTILINE)


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


def ensure_prefixes(text: str, prefixes: tuple[str], default: str):
    """Ensure the text starts with one of several prefixes, or prepend a default.

    Args:
        text: The string to process
        prefixes: acceptable prefixes to the string
        default: a prefix to prepend if none of the prefixes are present

    Returns:
        The prefixed string, or original string if no prefixes are present.
    """
    if not text.startswith(prefixes):
        return default + text
    return text


def ensure_prefix(text: str, prefix: str) -> str:
    """Ensure the text starts with a prefix.

    If it already starts with the prefix, the original string will be returned.

    Args:
        text: The string to process
        prefix: The prefix to ensure

    Returns:
        The text with the given prefix ensured.
    """
    if not text.startswith(prefix):
        return prefix + text
    return text


def ensure_suffix(text: str, suffix: str) -> str:
    """Ensure the text ends with the suffix.

    If it already ends with the suffix, the original string will be returned.

    Args:
        text: The string to process
        suffix: The suffix to add if not already present.

    Returns:
        The text with the given suffix.
    """
    if not text.endswith(suffix):
        return text + suffix
    return text


def squash_whitespace(string: str) -> str:
    """Reduces unnecessary whitespace in (multiline) strings.

    Replaces multiple adjacent newlines with a single newline. Removes whitespace at the
    start of a line. Removes whitespace at the start and end of the string.

    Args:
        string: A string to strip.

    Returns:
        The stripped strings.
    """
    return WHITESPACE_LINE_STARTING_REGEX.sub(
        "", ADJACENT_NEWLINE_REGEX.sub("\n", string)
    ).strip()
