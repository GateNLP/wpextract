from datetime import datetime

import pandas as pd
import pytest
from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.pages import load_pages
from helpers.df import ordered_col


@pytest.fixture()
def pages_df_and_registry(datadir):
    link_registry = LinkRegistry()
    return load_pages(datadir / "pages.json", link_registry), link_registry


@pytest.fixture()
def pages_df(pages_df_and_registry):
    pages_df, _ = pages_df_and_registry
    return pages_df


def test_equals_expected(datadir, pages_df):
    expected_df = pd.read_json(datadir / "pages_df_out.json", orient="table")

    assert pages_df.equals(expected_df)


def test_post_times(pages_df):
    post_1 = pages_df.loc[1]
    assert type(post_1.date_gmt) == pd.Timestamp
    assert type(post_1.modified_gmt) == pd.Timestamp

    assert post_1.date_gmt.tzinfo is None, "date_gmt had timezone information"
    assert post_1.modified_gmt.tzinfo is None, "modified_gmt had timezone information"

    assert post_1.date_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=11, hour=10, minute=0, second=0
    )
    assert post_1.modified_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=11, hour=10, minute=0, second=0
    )

    assert (
        len(pages_df.columns.intersection(["date", "modified"])) == 0
    ), "non-GMT time columns present"


def test_link_locale(pages_df):
    assert pages_df["link_locale"].equals(ordered_col([None, "fr"]))


def test_columns_removed(pages_df):
    assert "_links" not in pages_df.columns


def test_adds_link_registry(pages_df_and_registry):
    tags_df, registry = pages_df_and_registry

    assert len(registry.links) == 2
