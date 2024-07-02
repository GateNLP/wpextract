from datetime import datetime

import pandas as pd
import pytest
from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.media import load_media


@pytest.fixture()
def media_df_and_registry(datadir):
    link_registry = LinkRegistry()
    return load_media(datadir / "media.json", link_registry), link_registry


@pytest.fixture()
def media_df(media_df_and_registry):
    media_df, _ = media_df_and_registry
    return media_df


def test_media_times(media_df):
    media_1 = media_df.loc[1]
    assert isinstance(media_1.date_gmt, pd.Timestamp)
    assert isinstance(media_1.modified_gmt, pd.Timestamp)

    assert media_1.date_gmt.tzinfo is None, "date_gmt had timezone information"
    assert media_1.modified_gmt.tzinfo is None, "modified_gmt had timezone information"

    assert media_1.date_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=7, hour=10, minute=0, second=0
    )
    assert media_1.modified_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=7, hour=10, minute=0, second=0
    )

    assert (
        len(media_df.columns.intersection(["date", "modified"])) == 0
    ), "non-GMT time columns present"


def test_description_extraction(media_df):
    assert media_df.loc[1]["description.text"] == "Some Text"


def test_caption_extraction(media_df):
    assert media_df.loc[1]["caption.text"] == "Some caption text"


def test_title_extraction(media_df):
    assert media_df.loc[1]["title.text"] == "test-image"


def test_columns_removed(media_df):
    assert "_links" not in media_df.columns


def test_adds_link_registry(media_df_and_registry):
    media_df, registry = media_df_and_registry

    assert len(registry.links) == 1
    assert (
        registry.links[0].link
        == "https://example.org/wp-content/uploads/2022/12/test-image.jpg"
    )
