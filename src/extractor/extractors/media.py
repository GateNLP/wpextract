from pathlib import Path

import pandas as pd

from extractor.util.html import extract_html_text
from extractor.util.json import load_df

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
    "media_details.file": "file_path",
    "media_details.parent_image.attachment_id": "parent_image_id",
    "yoast_head_json.og_url": "og_url",
}


def load_media(path: Path) -> pd.DataFrame:
    """Load media from a JSON file.

    The JSON file is expected to be in the response format of the WordPress media API.

    Args:
        path: The path to the JSON file

    Returns:
        A dataframe of the media
    """
    media_df = load_df(path)

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

    media_df = media_df.rename(columns=RENAME_COLUMNS)

    return media_df
