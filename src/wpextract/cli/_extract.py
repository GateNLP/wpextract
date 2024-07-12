from pathlib import Path
from typing import Optional

import click

from wpextract.cli._shared import (
    CMD_ARGS,
    directory,
    empty_directory,
    logging_options,
    setup_logging,
    setup_tqdm_redirect,
)


@click.command(short_help="Extract site to a dataset.", **CMD_ARGS)
@click.argument("json_root", type=directory)
@click.argument(
    "out_dir", type=click.Path(), callback=empty_directory, metavar="DIRECTORY"
)
@click.option(
    "-S", "--scrape-root", help="Root directory of an HTML scrape", type=directory
)
@click.option(
    "-P", "--json-prefix", help="Prefix to use for input and output filenames"
)
@logging_options
def extract(
    json_root: Path,
    out_dir: Path,
    scrape_root: Optional[Path],
    json_prefix: Optional[str],
    log: Optional[Path],
    verbose: bool,
):
    """Converts the downloaded data files into a dataset.

    JSON_ROOT is a directory containing a JSON dump of the data files, such as one generated with wpextract download.

    OUT_DIR is the directory to output the extracted JSON to. It must be an existing empty directory or a non-existent directory which will be created.
    """
    from wpextract import WPExtractor

    setup_logging(verbose, log)

    with setup_tqdm_redirect(log is None):
        extractor = WPExtractor(
            json_root=json_root,
            scrape_root=scrape_root,
            json_prefix=json_prefix,
        )
        extractor.extract()
        extractor.export(out_dir)
