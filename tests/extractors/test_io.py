import numpy as np
import pandas as pd
import pytest
from helpers.df import ordered_col
from wpextract.extractors.io import (
    _remove_nan,
    _set_nested_keys,
    df_denormalize_to_dict,
    export_df,
    load_df,
    load_from_path,
)


def test_load_from_path(datadir):
    loaded = load_from_path(datadir / "example.json")

    assert len(loaded) == 2
    assert loaded[0]["entry"] == "one"


def test_load_from_path_doesnt_exist(datadir):
    loaded = load_from_path(datadir / "notreal.json")

    assert loaded is None


def test_load_df(datadir):
    df = load_df(datadir / "example.json")

    assert df.columns.to_list() == ["entry", "nested1.nested2"]

    assert df["entry"].equals(ordered_col(["one", "two"]))
    assert df["nested1.nested2"].equals(ordered_col(["value1", "value2"]))


def test_load_df_from_path_doesnt_exist(datadir):
    df = load_df(datadir / "notreal.json")

    assert df is None


def test_load_df_empty(datadir):
    df = load_df(datadir / "empty.json")

    assert df is None


def test_df_denormalize():
    df = pd.DataFrame(
        [("a", "b"), ("c", "d")], columns=["one", "two.three"], index=[1, 2]
    )

    denormalized = df_denormalize_to_dict(df)

    assert denormalized == [
        {"one": "a", "two": {"three": "b"}},
        {"one": "c", "two": {"three": "d"}},
    ]


def test_export_df(datadir, tmp_path):
    df = load_df(datadir / "example.json")
    out_path = tmp_path / "out.json"
    export_df(df, out_path)
    assert out_path.exists()

    out_loaded = load_df(out_path)
    assert df.equals(out_loaded)


def test_export_df_none(tmp_path):
    out_path = tmp_path / "out.json"
    export_df(None, out_path)

    assert out_path.exists()

    assert out_path.read_text() == "[]"


def test_set_nested_keys():
    res = _set_nested_keys({}, ["one", "two", "three"], "value")
    assert res == {"one": {"two": {"three": "value"}}}

    with pytest.raises(ValueError, match="is already set"):
        _set_nested_keys({"one": "two"}, ["one", "two", "three"], "value")


@pytest.mark.parametrize(
    ("inp", "exp_out"),
    [
        (pd.NA, None),
        (np.nan, None),
        ([1, pd.NA, 2, np.nan], [1, None, 2, None]),
        ({"a": "foo", "b": pd.NA, "c": np.nan}, {"a": "foo", "b": None, "c": None}),
    ],
)
def test_remove_nan(inp, exp_out):
    assert _remove_nan(inp) == exp_out
