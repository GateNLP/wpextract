import numpy as np
import pandas as pd
import pytest
from helpers.df import ordered_col
from wpextract.extractors.categories import load_categories
from wpextract.extractors.data.links import LinkRegistry


@pytest.fixture()
def categories_df_and_registry(datadir):
    link_registry = LinkRegistry()
    return load_categories(datadir / "categories.json", link_registry), link_registry


@pytest.fixture()
def categories_df(categories_df_and_registry):
    categories_df, _ = categories_df_and_registry
    return categories_df


def test_equals_expected(datadir, categories_df):
    expected_df = pd.read_json(datadir / "categories_df_out.json", orient="table")

    assert categories_df.equals(expected_df)


def test_parent_nan_replacement(categories_df):
    assert categories_df["parent"].equals(ordered_col([np.nan, np.nan, 2]))


def test_link_locale(categories_df):
    assert categories_df["link_locale"].equals(ordered_col([None, "fr", "fr"]))


def test_columns_removed(categories_df):
    assert "_links" not in categories_df.columns


def test_adds_link_registry(categories_df_and_registry):
    categories_df, registry = categories_df_and_registry

    assert len(registry.links) == 3
