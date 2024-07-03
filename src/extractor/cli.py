import argparse
import logging

from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm

from extractor.extract import WPExtractor
from extractor.util.args import directory, empty_directory


def _do_extract(args):
    extractor = WPExtractor(
        json_root=args.json_root,
        scrape_root=args.scrape_root,
        json_prefix=args.json_prefix,
    )
    extractor.extract()
    extractor.export(args.out_dir)


def main() -> None:
    """Entrypoint for CLI."""
    parser = argparse.ArgumentParser(
        prog="wordpress-site-extractor",
        description="Extracts posts from wordpress dump",
    )

    parser.add_argument("json_root", help="JSON dump of the site", type=directory)
    parser.add_argument("out_dir", help="Output directory", type=empty_directory)
    parser.add_argument(
        "--scrape-root",
        "-S",
        help="Root directory of an HTML scrape",
        type=directory,
        required=False,
        default=None,
    )
    parser.add_argument(
        "--json-prefix",
        "-P",
        help="Prefix to the JSON files",
        type=str,
        required=False,
        default=None,
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
    parser.set_defaults(feature=True)

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.log is not None:
        logging.basicConfig(filename=args.log, level=log_level)
    else:
        logging.basicConfig(level=log_level)

    tqdm.pandas()

    if args.log is None:
        with logging_redirect_tqdm():
            _do_extract(args)
    else:
        _do_extract(args)
