from argparse import Namespace

from wpextract.cli._shared import _register_shared
from wpextract.downloader import WPDownloader
from wpextract.dl.requestsession import RequestSession
from wpextract.util.args import empty_directory

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
        type=empty_directory,
        help="the path of the output JSON file",
    )
    parser_dl.add_argument(
        "--media-dest",
        type=str,
        default=None,
        help="Path to download media files, skipped if not supplied.",
    )
    parser_dl.add_argument(
        "--json-prefix",
        "-P",
        help="Prefix to the JSON files",
        type=str,
        required=False,
        default=None,
    )

    _register_shared(parser_dl)

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
    auth_group.add_argument("--proxy", help="Define a proxy server to use")
    auth_group.add_argument(
        "--auth", help="Define HTTP Basic credentials in format username:password"
    )
    auth_group.add_argument(
        "--cookies",
        help='define cookies to send with request in the format "cookie1=foo; cookie2=bar"',
    )

    req_group = parser_dl.add_argument_group("request behaviour")
    req_group.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Stop waiting for a response after a given number of seconds (default: %(default)s)",
    )
    req_group.add_argument(
        "--wait",
        "-w",
        type=float,
        help="Wait the specified number of seconds between retrievals",
    )
    req_group.add_argument(
        "--random-wait",
        action="store_true",
        help="Randomly varies the time between requests to between 0.5 and 1.5 times the number of seconds set by --wait",
    )
    req_group.set_defaults(random_wait=False)
    req_group.add_argument(
        "--max-retries",
        type=int,
        default=10,
        help="Maximum number of retries before giving up (default: %(default)s)",
    )
    req_group.add_argument(
        "--backoff-factor",
        type=float,
        default=0.1,
        help="Factor to apply delaying retries. Default will sleep for 0.0, 0.2, 0.4, 0.8,... (default: %(default)s)",
    )
    req_group.add_argument(
        "--max-redirects",
        type=int,
        default=20,
        help="Maximum number of redirects before giving up (default: %(default)s)",
    )


def do_dl(parser, args: Namespace):
    """Perform the `dl` subcommand."""
    types_to_dl = [dl_type for dl_type in dl_types if vars(args)[dl_type]]

    if args.random_wait and args.wait is None:
        parser.error(
            "argument --random-wait: cannot be used unless --wait/-w is also set"
        )

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

    session = RequestSession(
        proxy=args.proxy,
        cookies=args.cookies,
        authorization=auth,
        timeout=args.timeout,
        wait=args.wait,
        random_wait=args.random_wait,
        max_retries=args.max_retries,
        backoff_factor=args.backoff_factor,
    )

    downloader = WPDownloader(
        target=args.target,
        out_path=args.out_json,
        data_types=types_to_dl,
        session=session,
        json_prefix=args.json_prefix,
    )

    downloader.download()

    if args.media_dest:
        downloader.download_media_files(session, args.media_dest)
