from pathlib import Path
from typing import Optional

import pandas as pd

from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import load_df
from wpextract.util.locale import extract_locale

EXPORT_COLUMNS = [
    "count",
    "description",
    "link",
    "link_locale",
    "name",
    "slug",
]


def load_tags(path: Path, link_registry: LinkRegistry) -> Optional[pd.DataFrame]:
    """Load the tags from a JSON file.

    The JSON file is expected to be in the response format of the WordPress tags API.

    Args:
        path: The path of the JSON file
        link_registry: A link registry to populate

    Returns:
        A dataframe of the tags.
    """
    tags_df = load_df(path)

    if tags_df is None:
        return None

    tags_df["link_locale"] = tags_df["link"].apply(extract_locale)
    tags_df = tags_df[tags_df.columns.intersection(EXPORT_COLUMNS)]

    link_registry.add_linkables(
        "tag", tags_df["link"].to_list(), tags_df.index.to_list()
    )

    return tags_df
