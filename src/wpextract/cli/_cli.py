import click

from wpextract.cli._download import download
from wpextract.cli._extract import extract
from wpextract.cli._shared import CMD_ARGS

@click.group(context_settings=dict(help_option_names=['-h', '--help']), **CMD_ARGS)
def cli():
    """wpextract is a tool to create datasets from WordPress sites."""


cli.add_command(download)
cli.add_command(extract)