from pathlib import Path
from typing import Optional

import pandas as pd

from wpextract.extractors.io import load_df

EXPORT_COLUMNS = ["avatar", "description", "link", "name", "slug", "url"]


def load_users(path: Path) -> Optional[pd.DataFrame]:
    """Load the users from a JSON file.

    Args:
        path: Path to file.

    Returns:
        Dataframe of users
    """
    users_df = load_df(path)

    if users_df is None:
        return None

    if "yoast_head_json.og_image" in users_df.columns:
        users_df["avatar"] = users_df["yoast_head_json.og_image"].apply(
            lambda image: image[0]["url"] if len(image) > 0 else None
        )
    else:
        users_df["avatar"] = None

    users_df = users_df[users_df.columns.intersection(EXPORT_COLUMNS)]

    return users_df
