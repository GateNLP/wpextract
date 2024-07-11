import dataclasses
import json
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from langcodes import Language
from pandas import DataFrame
from pandas import Timestamp as PdTimestamp


def load_from_path(path: Path) -> Optional[dict]:
    """Loads and parses a JSON file.

    Args:
        path: The path to load

    Returns:
        The decoded JSON object. None if the file does not exist.
    """
    if not path.is_file():
        return None

    with open(path) as f:
        return json.load(f)


def load_df(path: Path, index_col: str = "id") -> Optional[pd.DataFrame]:
    """Load a JSON file from a path into a dataframe and normalize.

    Will flatten the structure an infinite number of levels by
    concatenating child keys with ".".

    Args:
        path: The path to load
        index_col: The key from the JSON to use as the index

    Returns:
        A dataframe with the flattened JSON. None if the file does not exist or is an empty array.
    """
    data_raw = load_from_path(path)

    if data_raw is None:
        logging.info(f"File {path} does not exist, skipping this data type.")
        return None

    if len(data_raw) == 0:
        logging.info(f"File {path} has no data, skipping this data type.")
        return None

    return pd.json_normalize(data_raw).set_index(index_col)


def _set_nested_keys(row_dict: dict, split_key: list[str], val: Any):
    """Set a value in the dictionary with nested keys.

    Args:
        row_dict: The dictionary to set the value
        split_key: A list of 0 or more nested keys
        val: The value to set

    Raises:
        ValueError: If part of the nested key is already set to a value (for example,
            the dataframe has columns ``a`` and ``a.b``)

    Returns:
        The dictionary with the nested value set
    """
    current = row_dict
    for i in range(len(split_key)):
        key = split_key[i]
        if key not in current:
            if i == len(split_key) - 1:
                current[key] = val
            else:
                current[key] = {}
        else:
            if type(current[key]) is not dict:
                raise ValueError(f"Dictionary key {current[key]} is already set.")

        current = current[key]

    return row_dict


def df_denormalize_to_dict(df: pd.DataFrame, sep: str = "."):
    """Unflatten a dataframe with dot notation keys into a nested dictionary.

    Opposite of ``pd.json_normalize``.

    Args:
        df: the dataframe
        sep: the key separator

    Returns:
        A list of dictionaries with unflattened keys.
    """
    result = []
    for _, row in df.iterrows():
        parsed_row = {}
        for idx, val in row.items():
            keys = str(idx).split(sep)
            parsed_row = _set_nested_keys(parsed_row, keys, val)

        result.append(parsed_row)
    return result


def _remove_nan(value: Any) -> Any:
    """Replaces NA and NaN values with None.

    Supports replacing the values of lists and dictionaries.

    Args:
        value: The value to check

    Returns:
        The value with NA and NaN replaced.
    """
    if isinstance(value, dict):
        for dkey, dvalue in value.items():
            value[dkey] = _remove_nan(dvalue)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            value[i] = _remove_nan(item)
    elif isinstance(value, float) and np.isnan(value):
        value = None
    elif value is pd.NA:
        value = None

    return value


class JSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder to serialise site data."""

    def default(self, o: Any) -> Any:
        """Serialise custom objects.

        .. list-table
            :header-rows: 1
            * Type, Strategy
            * - ``pd.Timestamp``, ``isoformat()``
            * - Dataclasses, ``dataclasses.asdict()``
        """
        if type(o) == PdTimestamp:
            return o.isoformat()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if type(o) == Language:
            return str(o)

        return super().default(o)


def _export_file(raw: Any, path: Path):
    with open(path, "w") as f:
        json.dump(raw, f, cls=JSONEncoder, indent=2, allow_nan=False)


def export_df(df: Optional[DataFrame], path: Path) -> None:
    """Export a dataframe to the path as JSON.

    Nests dot-notation columns into nested dictionaries.

    Args:
        df: the dataframe
        path: the destination path
    """
    if df is None:
        _export_file([], path)
    else:
        out_df = df.reset_index(names="id")
        denormalized = _remove_nan(df_denormalize_to_dict(out_df))
        _export_file(denormalized, path)
