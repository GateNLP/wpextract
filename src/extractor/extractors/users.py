from pathlib import Path

import pandas as pd

from extractor.extractors.io import load_df

EXPORT_COLUMNS = ["avatar", "description", "link", "name", "slug", "url"]


def load_users(path: Path) -> pd.DataFrame:
    """Load the users from a JSON file.

    Args:
        path: Path to file.

    Returns:
        Dataframe of users
    """
    users_df = load_df(path)

    users_df["avatar"] = users_df["yoast_head_json.og_image"].apply(
        lambda image: image[0]["url"] if len(image) > 0 else None
    )

    users_df = users_df[users_df.columns.intersection(EXPORT_COLUMNS)]

    return users_df
