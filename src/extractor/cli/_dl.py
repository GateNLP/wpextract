from argparse import Namespace

from extractor.dl.downloader import WPDownloader

dl_types = ["categories", "media", "pages", "posts", "tags", "users"]


def register_dl_parser(subparsers):
    """Register the `dl` subcommand."""
    parser_dl = subparsers.add_parser("dl")
    parser_dl.add_argument(
        "target",
        type=str,
        help="the base path of the WordPress installation to examine",
    )
    parser_dl.add_argument(
        "out_json",
        type=str,
        help="the path of the output JSON file",
    )
    parser_dl.add_argument(
        "--media-dest",
        "-m",
        type=str,
        default=None,
        help="Path to download media files, skipped if not supplied."
    )
    type_group = parser_dl.add_argument_group("data types")
    for dl_type in dl_types:
        type_group.add_argument(
            f"--no-{dl_type}",
            dest=dl_type,
            action="store_false",
            help=f"Don't download {dl_type}",
        )
    parser_dl.set_defaults(**{dl_type: True for dl_type in dl_types})


def do_dl(args: Namespace):
    args_d = vars(args)
    """Perform the `dl` subcommand."""
    types_to_dl = [dl_type for dl_type in dl_types if args_d[dl_type]]

    downloader = WPDownloader(
        args.target,
        args.out_json,
        types_to_dl,
    )

    downloader.download()

    if args.media_dest:
        downloader.download_media_files(args.media_dest)
