import json
from pathlib import Path

import pandas as pd


def load_from_path(path: Path) -> dict:
    """Loads and parses a JSON file.

    Args:
        path: The path to load

    Returns:
        The decoded JSON object.
    """
    with open(path, "r") as f:
        return json.load(f)


def load_df(path: Path, index_col: str = "id") -> pd.DataFrame:
    """Load a JSON file from a path into a dataframe and normalize.

    Will flatten the structure an infinite number of levels by
    concatenating child keys with ".".

    Args:
        path: The path to load
        index_col: The key from the JSON to use as the index

    Returns:
        A dataframe with the flattened JSON.
    """
    data_raw = load_from_path(path)

    return pd.json_normalize(data_raw).set_index(index_col)
