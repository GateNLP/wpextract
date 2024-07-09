import argparse
import logging
from importlib.metadata import version

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from extractor.cli._dl import do_dl, register_dl_parser
from extractor.cli._extract import do_extract, register_extract_parser


def _exec_command(parser, args):
    if args.command == "parse":
        do_extract(parser, args)
    elif args.command == "dl":
        do_dl(parser, args)
    else:
        raise ValueError("Unknown command")


def _get_version():
    return version("wp-site-extractor")


def _build_parser():
    """Entrypoint for CLI."""
    parser = argparse.ArgumentParser(
        prog="wpextract",
        description="Create datasets from WordPress sites using the REST API",
    )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + _get_version()
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
    )

    register_extract_parser(subparsers)
    register_dl_parser(subparsers)

    return parser

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.log is not None:
        logging.basicConfig(filename=args.log, level=log_level)
    else:
        logging.basicConfig(level=log_level)

    tqdm.pandas()

    if args.log is None:
        with logging_redirect_tqdm():
            _exec_command(parser, args)
    else:
        _exec_command(parser, args)
