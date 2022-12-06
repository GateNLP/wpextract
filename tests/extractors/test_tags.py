import pandas as pd
import pytest
from helpers.df import ordered_col

from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.tags import load_tags


@pytest.fixture
def tags_df_and_registry(datadir):
    link_registry = LinkRegistry()
    return load_tags(datadir / "tags.json", link_registry), link_registry


@pytest.fixture
def tags_df(tags_df_and_registry):
    tags_df, _ = tags_df_and_registry
    return tags_df


def test_equals_expected(datadir, tags_df):
    expected_df = pd.read_pickle(datadir / "tags_df_out.pickle")

    assert tags_df.equals(expected_df)


def test_link_locale(tags_df):
    assert tags_df["link_locale"].equals(ordered_col([None, "fr", "fr"]))


def test_columns_removed(tags_df):
    assert "_links" not in tags_df.columns


def test_adds_link_registry(tags_df_and_registry):
    tags_df, registry = tags_df_and_registry

    assert len(registry.links) == 3
