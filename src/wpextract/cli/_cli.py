import platform

import click

from wpextract.cli._download import download
from wpextract.cli._extract import extract
from wpextract.cli._shared import CMD_ARGS

PYTHON_VERSION = platform.python_version()


@click.group(context_settings=dict(help_option_names=["-h", "--help"]), **CMD_ARGS)
@click.version_option(
    package_name="wpextract",
    message=f"%(prog)s, version %(version)s (Python {PYTHON_VERSION})",
)
def cli():
    """WPextract is a tool to create datasets from WordPress sites."""


cli.add_command(download)
cli.add_command(extract)
