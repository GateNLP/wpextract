def register_dl_parser(subparsers):
    """Register the `dl` subcommand."""
    parser_dl = subparsers.add_parser("dl")
    parser_dl.add_argument(
        "target",
        type=str,
        help="the base path of the WordPress installation to examine",
    )


def do_dl(args):
    """Perform the `dl` subcommand."""
    print(args)
