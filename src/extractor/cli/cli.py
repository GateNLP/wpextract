import argparse
import logging
from importlib.metadata import version

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from extractor.cli._dl import do_dl, register_dl_parser
from extractor.cli._extract import do_extract, register_extract_parser


def _exec_command(args):
    if args.command == "parse":
        do_extract(args)
    elif args.command == "dl":
        do_dl(args)
    else:
        raise ValueError("Unknown command")


def _get_version():
    return version("wp-site-extractor")


def main() -> None:
    """Entrypoint for CLI."""
    parser = argparse.ArgumentParser(
        prog="wordpress-site-extractor",
        description="Create datasets from WordPress sites using the REST API",
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + _get_version()
    )

    parser.add_argument(
        "--log",
        "-l",
        help="File to log to. Will suppress stdout.",
        type=str,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--verbose",
        "-v",
        help="Increase log level to include debug logs",
        action="store_true",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
    )

    register_extract_parser(subparsers)
    register_dl_parser(subparsers)

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.log is not None:
        logging.basicConfig(filename=args.log, level=log_level)
    else:
        logging.basicConfig(level=log_level)

    tqdm.pandas()

    if args.log is None:
        with logging_redirect_tqdm():
            _exec_command(args)
    else:
        _exec_command(args)
