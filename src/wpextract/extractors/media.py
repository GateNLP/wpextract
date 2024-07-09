from pathlib import Path
from typing import Optional

import pandas as pd
from bs4 import Tag

from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import load_df
from wpextract.parse.html import extract_html_text

EXPORT_COLUMNS = [
    "alt_text",
    "author",
    "caption.rendered",
    "caption.text",
    "date_gmt",
    "description.rendered",
    "description.text",
    "guid.rendered",
    "media_details.bitrate",
    "media_details.file",
    "media_details.image_meta.camera",
    "media_details.image_meta.created_timestamp",
    "media_details.image_meta.credit",
    "media_details.image_meta.focal_length",
    "media_details.image_meta.iso",
    "media_details.image_meta.orientation",
    "media_details.length",
    "media_details.mime_type",
    "media_details.original_image",
    "media_details.parent_image.attachment_id",
    "media_type",
    "mime_type",
    "modified_gmt",
    "post",
    "slug",
    "source_url",
    "title.rendered",
    "title.text",
    "yoast_head_json.og_url",
    "yoast_head_json.title",
]

RENAME_COLUMNS = {
    "caption.rendered": "caption.html",
    "description.rendered": "description.html",
    "guid.rendered": "guid",
    "post": "post_id",
    "title.rendered": "title.html",
    "yoast_head_json.title": "page_title",
    "media_details.parent_image.attachment_id": "parent_image_id",
    "yoast_head_json.og_url": "og_url",
}


def load_media(path: Path, link_registry: LinkRegistry) -> Optional[pd.DataFrame]:
    """Load media from a JSON file.

    The JSON file is expected to be in the response format of the WordPress media API.

    Args:
        path: The path to the JSON file
        link_registry: A link registry to populate

    Returns:
        A dataframe of the media
    """
    media_df = load_df(path)

    if media_df is None:
        return None

    # Convert times
    media_df["date_gmt"] = pd.to_datetime(media_df["date_gmt"])
    media_df["modified_gmt"] = pd.to_datetime(media_df["modified_gmt"])
    media_df = media_df.drop(["date", "modified"], axis=1)

    # Convert post ID to a NA-able integer
    media_df["post"] = media_df["post"].astype("Int64")

    media_df["description.text"] = media_df["description.rendered"].apply(
        extract_html_text
    )
    media_df["caption.text"] = media_df["caption.rendered"].apply(extract_html_text)
    media_df["title.text"] = media_df["title.rendered"].apply(extract_html_text)

    media_df.loc[media_df["description.text"] == "\n", "description.text"] = ""

    media_df = media_df[media_df.columns.intersection(EXPORT_COLUMNS)]

    media_df = media_df.rename(columns=RENAME_COLUMNS, errors="ignore")

    link_registry.add_linkables(
        "media", media_df["source_url"].to_list(), media_df.index.to_list()
    )

    return media_df


def get_caption(img: Tag) -> Optional[str]:
    """Get the caption of an image tag.

    Searches adjacent tags for a <figcaption>.

    TODO: A heuristic to find likely non-figcaption captions.

    Raises:
        ValueError: if a non-image tag is passed.

    Args:
        img: An img tag

    Returns:
        The caption text or None if there is no caption.
    """
    if img.name != "img":
        raise ValueError("Attempting to get caption of non-image")

    parent_caption = img.find_parent("figure")

    if parent_caption is None:
        return None

    caption = parent_caption.find("figcaption")

    if caption is None:
        return None

    return caption.get_text()
