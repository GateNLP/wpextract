import functools
import logging
import pathlib
from collections.abc import Generator
from contextlib import contextmanager, nullcontext
from typing import TYPE_CHECKING, Any, Callable, Optional

import click
from click import BadParameter, Context, Parameter
from click_option_group import optgroup
from tqdm.contrib.logging import logging_redirect_tqdm

if TYPE_CHECKING:
    import sys
    from typing import TypeVar

    if sys.version_info >= (3, 10):
        from typing import ParamSpec
    else:
        from typing_extensions import ParamSpec

    P = ParamSpec("P")
    R = TypeVar("R")

EPILOG = "See https://wpextract.readthedocs.io/ for documentation."

file = click.Path(
    exists=False, dir_okay=False, file_okay=True, writable=True, path_type=pathlib.Path
)
directory = click.Path(
    exists=True,
    file_okay=False,
    dir_okay=True,
    readable=True,
    writable=False,
    path_type=pathlib.Path,
)


def empty_directory(
    ctx: Context, param: Parameter, value: Any
) -> Optional[pathlib.Path]:
    if value is None:
        return value

    path = pathlib.Path(value)

    if path.exists() and not path.is_dir():
        raise BadParameter("exists but is not a directory")

    try:
        path.mkdir(exist_ok=True)
    except OSError as e:
        raise BadParameter("directory could not be created") from e

    if any(path.iterdir()):
        raise BadParameter("is not empty, must be an empty directory")

    return path


def logging_options(cmd_func: "Callable[P, R]") -> "Callable[P, R]":
    @optgroup.group("logging")  # type: ignore[misc]
    @optgroup.option(
        "-l", "--log", type=file, help="File to log to, will suppress stdout."
    )
    @optgroup.option(
        "-v", "--verbose", is_flag=True, help="Increase log level to include debug logs"
    )
    @functools.wraps(cmd_func)
    def wrapper(*args: "P.args", **kwargs: "P.kwargs") -> "R":
        return cmd_func(*args, **kwargs)

    return wrapper  # type: ignore[no-any-return]


def setup_logging(verbose: bool, log_path: Optional[pathlib.Path]) -> None:
    log_level = logging.DEBUG if verbose else logging.INFO

    if log_path is not None:
        logging.basicConfig(filename=log_path, level=log_level)
    else:
        logging.basicConfig(level=log_level)


@contextmanager
def setup_tqdm_redirect(should_redirect: bool) -> Generator[None, None, None]:
    """Conditionally yields the tqdm log redirect context.

    If `should_redirect` is false, the [`nullcontext`][contextlib.nullcontext] is yielded.
    This is a valid context but has no effect, allowing this function to always be used in a with.

    This is necessary because, contrary to what the docs imply, using logging_redirect_tqdm
    when a log file is set causes logs to be output to stdout.

    Args:
        should_redirect: whether to apply the redirect.

    Yields:
        tqdm log redirect context or null context
    """
    with logging_redirect_tqdm() if should_redirect else nullcontext():
        yield
