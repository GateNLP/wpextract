import pandas as pd
from wpextract.extractors.io import (
    df_denormalize_to_dict,
    export_df,
    load_df,
    load_from_path,
)
from helpers.df import ordered_col


def test_load_from_path(datadir):
    loaded = load_from_path(datadir / "example.json")

    assert len(loaded) == 2
    assert loaded[0]["entry"] == "one"


def test_load_df(datadir):
    df = load_df(datadir / "example.json")

    assert df.columns.to_list() == ["entry", "nested1.nested2"]

    assert df["entry"].equals(ordered_col(["one", "two"]))
    assert df["nested1.nested2"].equals(ordered_col(["value1", "value2"]))


def test_df_denormalize(datadir):
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
