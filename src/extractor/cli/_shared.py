def _register_shared(parser):
    log_group = parser.add_argument_group("logging")
    log_group.add_argument(
        "--log",
        "-l",
        help="File to log to. Will suppress stdout.",
        type=str,
        required=False,
        default=None,
    )
    log_group.add_argument(
        "--verbose",
        "-v",
        help="Increase log level to include debug logs",
        action="store_true",
    )