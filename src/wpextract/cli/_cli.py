import platform

import click

from wpextract.cli._download import download
from wpextract.cli._extract import extract
from wpextract.cli._shared import EPILOG

PYTHON_VERSION = platform.python_version()


@click.group(context_settings=dict(help_option_names=["-h", "--help"]), epilog=EPILOG)
@click.version_option(
    package_name="wpextract",
    message=f"%(prog)s, version %(version)s (Python {PYTHON_VERSION})",
)
def cli() -> None:
    """WPextract is a tool to create datasets from WordPress sites."""


cli.add_command(download)
cli.add_command(extract)
