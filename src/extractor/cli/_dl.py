from argparse import Namespace

from extractor.dl.downloader import WPDownloader

dl_types = ["categories", "media", "pages", "posts", "tags", "users"]


def register_dl_parser(subparsers):
    """Register the `dl` subcommand."""
    parser_dl = subparsers.add_parser(
        "dl", help="Download a site's content using the WordPress REST API."
    )
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
        type=str,
        default=None,
        help="Path to download media files, skipped if not supplied.",
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

    auth_group = parser_dl.add_argument_group("authentication")
    auth_group.add_argument("--proxy", "-P", help="Define a proxy server to use")
    auth_group.add_argument(
        "--auth", help="Define HTTP Basic credentials in format username:password"
    )
    auth_group.add_argument(
        "--cookies",
        help='define cookies to send with request in the format "cookie1=foo; cookie2=bar"',
    )


def do_dl(args: Namespace):
    """Perform the `dl` subcommand."""
    types_to_dl = [dl_type for dl_type in dl_types if vars(args)[dl_type]]

    target = args.target
    if not (target.startswith("http://") or target.startswith("https://")):
        target = "http://" + target
    if not target.endswith("/"):
        target += "/"

    auth = None
    if args.auth is not None:
        auth_list = args.auth.split(":")
        if len(auth_list) == 1:
            auth = (auth_list[0], "")
        elif len(auth_list) >= 2:
            auth = (auth_list[0], ":".join(auth_list[1:]))

    downloader = WPDownloader(
        args.target,
        args.out_json,
        types_to_dl,
        proxy=args.proxy,
        cookies=args.cookies,
        authorization=auth,
    )

    downloader.download()

    if args.media_dest:
        downloader.download_media_files(args.media_dest)
