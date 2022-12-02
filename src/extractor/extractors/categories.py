from pathlib import Path

import numpy as np

from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.io import load_df
from extractor.util.locale import extract_locale

EXPORT_COLUMNS = [
    "name",
    "slug",
    "description",
    "count",
    "link",
    "link_locale",
    "parent",
]


def load_categories(path: Path, link_registry: LinkRegistry):
    """Load the categories from a JSON file.

    The JSON file is expected to be in the response format of the WordPress
    categories API.

    Args:
        path: The path of the JSON file
        link_registry: A link registry to populate

    Returns:
        A dataframe of the categories.
    """
    categories_df = load_df(path)

    categories_df["parent"] = categories_df["parent"].replace(0, np.nan)
    categories_df["link_locale"] = categories_df["link"].apply(extract_locale)

    categories_df = categories_df[categories_df.columns.intersection(EXPORT_COLUMNS)]

    link_registry.add_linkables(
        "tag", categories_df["link"].to_list(), categories_df.index.to_list()
    )

    return categories_df
