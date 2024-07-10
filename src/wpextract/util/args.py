from argparse import ArgumentTypeError
from pathlib import Path


def directory(arg: str) -> Path:
    """Ensure the provided argument is a directory.

    Args:
        arg: an argument string

    Raises:
        ArgumentTypeError: If the argument is not a directory

    Returns:
        The path to the directory
    """
    path = Path(arg)

    if not path.is_dir():
        raise ArgumentTypeError("Must be a directory")

    return path


def empty_directory(arg: str) -> Path:
    """Ensure the provided argument is an empty directory, creating it if needed.

    Will not create more than one level of directory, i.e. the parent directory must
    already exist at least.

    Args:
        arg: an argument string

    Raises:
        ArgumentTypeError: If the path exists but is not a directory, or it is a
            directory but not empty, or it did not exist and could not be created.

    Returns:
        The path to the directory
    """
    path = Path(arg)

    if path.exists() and not path.is_dir():
        raise ArgumentTypeError("exists but is not a directory")

    try:
        path.mkdir(exist_ok=True)
    except OSError as e:
        raise ArgumentTypeError("Directory could not be created") from e

    if any(path.iterdir()):
        raise ArgumentTypeError("is not empty, must be an empty directory")

    return path
