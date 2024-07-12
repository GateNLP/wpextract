from pathlib import Path
from typing import Optional

import click
from click import Choice
from click_option_group import optgroup

from wpextract.cli._shared import (
    CMD_ARGS,
    empty_directory,
    logging_options,
    setup_logging,
    setup_tqdm_redirect,
)
from wpextract.util.str import ensure_prefixes, ensure_suffix

dl_types = ["categories", "media", "pages", "posts", "tags", "users"]


def data_type_opts(cmd_func):
    opts = [
        click.option(
            f"--{dl_type}/--no-{dl_type}",
            default=True,
            help=f"Enable or disable downloading {dl_type}",
        )
        for dl_type in dl_types
    ]

    for opt in opts:
        cmd_func = opt(cmd_func)
    return cmd_func


def validate_wait(ctx, param, value):
    if ctx.params.get("wait") is None and value is not False:
        raise click.BadParameter("cannot be used unless --wait/-w is also set.")
    return value


@click.command(short_help="Download a WordPress site.", **CMD_ARGS)
@click.argument("target", type=str)
@click.argument("out_json", type=click.Path(), callback=empty_directory)
@click.option(
    "--media-dest",
    type=click.Path(),
    callback=empty_directory,
    required=False,
    help="Path to a directory to download media files to, skipped if not supplied",
    metavar="DIRECTORY",
)
@click.option(
    "-P", "--json-prefix", type=str, help="Prefix to add to output file names"
)
@click.option(
    "--skip-type",
    "skip_types",
    type=Choice(dl_types, case_sensitive=False),
    default=[],
    multiple=True,
    help="Don't download the provided types. All others will be downloaded, default is to download all.",
)
@optgroup.group("authentication")
@optgroup.option("--proxy", type=str, help="Proxy server for requests")
@optgroup.option(
    "--auth",
    type=str,
    help='HTTP Basic credentials for requests (format "username:password")',
)
@optgroup.option(
    "--cookies",
    type=str,
    help='Cookies for requests (format "cookie1=foo; cookie2=bar")',
)
@optgroup.group("request behaviour")
@optgroup.option(
    "--timeout",
    type=int,
    default=30,
    help="Timeout for request in seconds",
    show_default=True,
)
@optgroup.option(
    "-w",
    "--wait",
    type=int,
    help="Time to wait between requests in seconds. Does not affect retries.",
    is_eager=True,  # to permit --random-wait validation
)
@optgroup.option(
    "--random-wait",
    is_flag=True,
    help="Randomly varies the time between requests to between 0.5 and 1.5 times the number of seconds set by --wait",
    callback=validate_wait,
)
@optgroup.option(
    "--max-retries",
    type=int,
    default=10,
    help="Maximum number of retries before giving up",
    show_default=True,
)
@optgroup.option(
    "--backoff-factor",
    type=float,
    default=0.1,
    help="Factor to apply delaying retries. Default will sleep for 0.0, 0.2, 0.4, 0.8,...",
    show_default=True,
)
@optgroup.option(
    "--max-redirects",
    type=int,
    default=20,
    help="Maximum number of redirects before giving up",
    show_default=True,
)
@logging_options
def download(
    target: str,
    out_json: Path,
    media_dest: Optional[Path],
    json_prefix: Optional[str],
    skip_types: list[str],
    proxy: Optional[str],
    auth: Optional[str],
    cookies: Optional[str],
    timeout: int,
    wait: Optional[int],
    random_wait: bool,
    max_retries: int,
    backoff_factor: float,
    max_redirects: int,
    log: Optional[Path],
    verbose: bool,
):
    """Download a site's content using the WordPress REST API.

    TARGET is the base path of the WordPress installation, e.g. "https://example.org/"

    OUT_JSON is the directory to output the downloaded JSON to. It must be an existing empty directory or a non-existent directory which will be created.
    """
    from wpextract import WPDownloader
    from wpextract.download import RequestSession

    setup_logging(verbose, log)

    types_to_dl = set(dl_types) - set(skip_types)

    target = ensure_prefixes(target, ("http://", "https://"), "http://")
    target = ensure_suffix(target, "/")

    if auth is not None:
        auth_list = auth.split(":")
        if len(auth_list) == 1:
            auth = (auth_list[0], "")
        elif len(auth_list) >= 2:
            auth = (auth_list[0], ":".join(auth_list[1:]))

    session = RequestSession(
        proxy=proxy,
        cookies=cookies,
        authorization=auth,
        timeout=timeout,
        wait=wait,
        random_wait=random_wait,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        max_redirects=max_redirects,
    )

    with setup_tqdm_redirect(log is None):
        downloader = WPDownloader(
            target=target,
            out_path=out_json,
            data_types=list(types_to_dl),
            session=session,
            json_prefix=json_prefix,
        )

        downloader.download()

        if media_dest is not None:
            downloader.download_media_files(session, media_dest)
