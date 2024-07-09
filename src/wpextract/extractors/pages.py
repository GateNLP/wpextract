from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm.auto import tqdm

from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import load_df
from wpextract.parse.content import extract_content_data
from wpextract.parse.html import extract_html_text, parse_html
from wpextract.util.locale import extract_locale

EXPORT_COLUMNS = [
    "author",
    "content.rendered",
    "content.text",
    "date_gmt",
    "embeds",
    "excerpt.rendered",
    "excerpt.text",
    "featured_media",
    "images",
    "link",
    "link_locale",
    "links.external",
    "links.internal",
    "modified_gmt",
    "parent",
    "slug",
    "template",
    "title.rendered",
    "yoast_head_json.title",
]


RENAME_COLUMNS = {
    "content.rendered": "content.html",
    "title.rendered": "title.html",
    "excerpt.rendered": "excerpt.html",
    "yoast_head_json.title": "page_title",
}


def load_pages(path: Path, link_registry: LinkRegistry) -> Optional[pd.DataFrame]:
    """Load the pages from a JSON file.

    The JSON file is expected to be in the response format of the WordPress posts API.

    Args:
        path: The path to the JSON file
        link_registry: The link registry to populate

    Returns:
        A dataframe of the pages
    """
    pages_df = load_df(path)

    if pages_df is None:
        return None

    pages_df["date_gmt"] = pd.to_datetime(pages_df["date_gmt"])
    pages_df["modified_gmt"] = pd.to_datetime(pages_df["modified_gmt"])
    pages_df = pages_df.drop(["date", "modified"], axis=1)

    pages_df["link_locale"] = pages_df["link"].apply(extract_locale)

    pages_df["title.text"] = pages_df["title.rendered"].apply(extract_html_text)
    pages_df["excerpt.text"] = pages_df["excerpt.rendered"].apply(extract_html_text)

    tqdm.pandas(desc="Parsing post content")
    pages_df["content.bs"] = pages_df["content.rendered"].progress_apply(parse_html)

    tqdm.pandas(desc="Extracting post content")
    pages_df[
        ["content.text", "links.internal", "links.external", "embeds", "images"]
    ] = pages_df.progress_apply(
        lambda r: extract_content_data(r["content.bs"], r["link"]), axis=1
    )

    pages_df = pages_df[pages_df.columns.intersection(EXPORT_COLUMNS)]
    pages_df = pages_df.rename(columns=RENAME_COLUMNS, errors="ignore")

    link_registry.add_linkables(
        "pages", pages_df["link"].to_list(), pages_df.index.to_list()
    )

    return pages_df
