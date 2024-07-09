from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import load_df
from wpextract.util.locale import extract_locale

EXPORT_COLUMNS = [
    "name",
    "slug",
    "description",
    "count",
    "link",
    "link_locale",
    "parent",
]


def load_categories(path: Path, link_registry: LinkRegistry) -> Optional[pd.DataFrame]:
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

    if categories_df is None:
        return None

    categories_df["parent"] = categories_df["parent"].replace(0, np.nan)
    categories_df["link_locale"] = categories_df["link"].apply(extract_locale)

    categories_df = categories_df[categories_df.columns.intersection(EXPORT_COLUMNS)]

    link_registry.add_linkables(
        "category", categories_df["link"].to_list(), categories_df.index.to_list()
    )

    return categories_df
