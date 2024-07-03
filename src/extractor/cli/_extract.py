from extractor.extract import WPExtractor
from extractor.util.args import directory, empty_directory


def register_extract_parser(subparsers):
    """Register the `extract` subcommand."""
    parser_extract = subparsers.add_parser("extract", help="Convert the downloaded data files into a dataset.")

    parser_extract.add_argument(
        "json_root", help="JSON dump of the site", type=directory
    )
    parser_extract.add_argument(
        "out_dir", help="Output directory", type=empty_directory
    )
    parser_extract.add_argument(
        "--scrape-root",
        "-S",
        help="Root directory of an HTML scrape",
        type=directory,
        required=False,
        default=None,
    )
    parser_extract.add_argument(
        "--json-prefix",
        "-P",
        help="Prefix to the JSON files",
        type=str,
        required=False,
        default=None,
    )
    parser_extract.set_defaults(feature=True)


def do_extract(args):
    """Perform the extract command."""
    extractor = WPExtractor(
        json_root=args.json_root,
        scrape_root=args.scrape_root,
        json_prefix=args.json_prefix,
    )
    extractor.extract()
    extractor.export(args.out_dir)
