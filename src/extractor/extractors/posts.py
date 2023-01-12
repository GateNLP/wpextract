from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from pandas import DataFrame
from tqdm.auto import tqdm

from extractor.extractors.data.link_resolver import resolve_links
from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.io import load_df
from extractor.parse.content import extract_content_data
from extractor.parse.html import extract_html_text, parse_html
from extractor.parse.translations import extract_translations
from extractor.scrape.scrape import load_scrape
from extractor.util.locale import extract_locale

EXPORT_COLUMNS = [
    "author",
    "categories",
    "comment_status",
    "content.rendered",
    "content.text",
    "date_gmt",
    "embeds",
    "excerpt.rendered",
    "excerpt.text",
    "featured_media",
    "images",
    "language",
    "link",
    "link_locale",
    "links.external",
    "links.internal",
    "modified_gmt",
    "og_image_url",
    "slug",
    "status",
    "sticky",
    "tags",
    "title.rendered",
    "title.text",
    "translations",
    "yoast_head_json.title",
]

RENAME_COLUMNS = {
    "title.rendered": "title.html",
    "content.rendered": "content.html",
    "excerpt.rendered": "excerpt.html",
    "yoast_head_json.title": "page_title",
}


def load_posts(
    path: Path, link_registry: LinkRegistry, scrape_urls_files: Dict[str, Path]
) -> Optional[pd.DataFrame]:
    """Load the posts from a JSON file.

    The JSON file is expected to be in the response format of the WordPress posts API.

    Args:
        path: The path to the JSON file
        link_registry: The Link Registry to populate
        scrape_urls_files: A dictionary of site URLs to scrape file paths

    Returns:
        A dataframe of the posts.
    """
    posts_df = load_df(path)

    if posts_df is None:
        return None

    # Convert times
    posts_df["date_gmt"] = pd.to_datetime(posts_df["date_gmt"])
    posts_df["modified_gmt"] = pd.to_datetime(posts_df["modified_gmt"])
    posts_df = posts_df.drop(["date", "modified"], axis=1)

    # yoast_head_json.og_image is a list containing 0 or 1 image dictionaries
    # Get the "url" property if there is an image
    posts_df["og_image_url"] = posts_df["yoast_head_json.og_image"].apply(
        lambda image: image[0]["url"]
        if type(image) != float and len(image) > 0
        else None
    )

    posts_df["link_locale"] = posts_df["link"].apply(extract_locale)

    posts_df["title.text"] = posts_df["title.rendered"].apply(extract_html_text)
    posts_df["excerpt.text"] = posts_df["excerpt.rendered"].apply(extract_html_text)

    tqdm.pandas(desc="Parsing Content")
    posts_df["content.bs"] = posts_df["content.rendered"].progress_apply(parse_html)

    tqdm.pandas(desc="Parsing Scrape")
    posts_df["scrape_bs"] = posts_df["link"].progress_apply(
        lambda link: load_scrape(scrape_urls_files, link)
    )
    posts_df[["language", "translations"]] = posts_df.apply(
        lambda r: extract_translations(r["scrape_bs"], r["link"]), axis=1
    )

    link_registry.add_linkables(
        "post", posts_df["link"].to_list(), posts_df.index.to_list()
    )

    tqdm.pandas(desc="Extracting scrape")
    posts_df[
        ["content.text", "links.internal", "links.external", "embeds", "images"]
    ] = posts_df.progress_apply(
        lambda r: extract_content_data(r["content.bs"], r["link"]), axis=1
    )

    posts_df = posts_df[EXPORT_COLUMNS]
    posts_df = posts_df.rename(columns=RENAME_COLUMNS)

    return posts_df


def resolve_post_links(registry: LinkRegistry, posts_df: DataFrame) -> DataFrame:
    """Look up the internal links of each post in the registry.

    Args:
        registry: A filled link registry
        posts_df: The processed posts dataframe

    Returns:
        The posts dataframe with link data resolved.
    """
    posts_df["links.internal"] = posts_df["links.internal"].apply(
        lambda links: resolve_links(registry, links)
    )

    return posts_df


def resolve_post_translations(registry: LinkRegistry, posts_df: DataFrame) -> DataFrame:
    """Look up the translation links of each post in the registry.

    Args:
        registry: A filled link registry
        posts_df: The processed posts dataframe

    Returns:
        The posts dataframe with link data resolved
    """
    posts_df["translations"] = posts_df["translations"].apply(
        lambda ts: resolve_links(registry, ts)
    )

    return posts_df
