import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from pandas import DataFrame
from tqdm.auto import tqdm

from wpextract.extractors.data.images import resolve_images
from wpextract.extractors.data.link_resolver import resolve_links
from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import load_df
from wpextract.parse.content import extract_content_data
from wpextract.parse.html import extract_html_text, parse_html
from wpextract.parse.translations import PickerListType, extract_translations
from wpextract.parse.translations._resolver import TranslationLink
from wpextract.scrape.scrape import load_scrape
from wpextract.util.locale import extract_locale

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
    path: Path,
    link_registry: LinkRegistry,
    scrape_urls_files: dict[str, Path],
    translation_pickers: Optional[PickerListType] = None,
) -> Optional[pd.DataFrame]:
    """Load the posts from a JSON file.

    The JSON file is expected to be in the response format of the WordPress posts API.

    Args:
        path: The path to the JSON file
        link_registry: The Link Registry to populate
        scrape_urls_files: A dictionary of site URLs to scrape file paths
        translation_pickers: Custom list of translation pickers.

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
    if "yoast_head_json.title" in posts_df.columns:
        posts_df["og_image_url"] = posts_df["yoast_head_json.og_image"].apply(
            lambda image: image[0]["url"]
            if not isinstance(image, float) and len(image) > 0
            else None
        )
    else:
        posts_df["og_image_url"] = None

    posts_df["link_locale"] = posts_df["link"].apply(extract_locale)

    posts_df["title.text"] = posts_df["title.rendered"].apply(extract_html_text)
    posts_df["excerpt.text"] = posts_df["excerpt.rendered"].apply(extract_html_text)

    tqdm.pandas(desc="Parsing Content")
    posts_df["content.bs"] = posts_df["content.rendered"].progress_apply(parse_html)

    if scrape_urls_files != {}:
        tqdm.pandas(desc="Parsing Scrape")
        posts_df["scrape_bs"] = posts_df["link"].progress_apply(
            lambda link: load_scrape(scrape_urls_files, link)
        )
        posts_df[["language", "translations"]] = posts_df.apply(
            lambda r: extract_translations(
                r["scrape_bs"], r["link"], translation_pickers
            ),
            axis=1,
        )
    else:
        logging.info("SKipping translation extraction")

    link_registry.add_linkables(
        "post", posts_df["link"].to_list(), posts_df.index.to_list()
    )

    tqdm.pandas(desc="Extracting from text")
    posts_df[
        ["content.text", "links.internal", "links.external", "embeds", "images"]
    ] = posts_df.progress_apply(
        lambda r: extract_content_data(r["content.bs"], r["link"]), axis=1
    )

    posts_df = posts_df[posts_df.columns.intersection(EXPORT_COLUMNS)]
    posts_df = posts_df.rename(columns=RENAME_COLUMNS, errors="ignore")

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


def resolve_post_media(registry: LinkRegistry, posts_df: DataFrame) -> DataFrame:
    """Look up the images of each post.

    Args:
        registry: A filled link registry
        posts_df: The processed posts dataframe

    Returns:
        The posts dataframe with link data resolved.
    """
    posts_df["images"] = posts_df["images"].apply(
        lambda media: resolve_images(registry, media)
    )

    return posts_df


def ensure_translations_undirected(posts_df: DataFrame) -> DataFrame:
    """Create translation relationships if they are not bidirectional.

    For example, if A -> B, but B -> A does not exist, then create B -> A.

    Translations will need to be resolved again after this step.

    Args:
        posts_df: A processed posts dataframe.

    Returns:
        The posts dataframe with bidirectional translations.
    """
    new_translations = []
    for post in posts_df.itertuples():
        for translation_obj in post.translations:
            if translation_obj.destination is None:
                logging.debug(
                    f"Unable to verify translation for {post.Index}, unresolved."
                )
                continue

            translation_id = translation_obj.destination.idx
            translation_post = posts_df.loc[translation_id]

            if not any(
                [
                    translation.destination is not None
                    and translation.destination.idx == post.Index
                    for translation in translation_post.translations
                ]
            ):
                logging.debug(
                    f"{post.Index} -> {translation_obj.destination.idx} existed "
                    "but reverse did not"
                )
                new_translations.append(
                    (
                        translation_id,
                        TranslationLink(
                            text=None,
                            href=post.link,
                            lang=post.language,
                            destination=None,
                        ),
                    )
                )

    for new_t_id, new_t_link in new_translations:
        posts_df.loc[new_t_id, "translations"].append(new_t_link)

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
