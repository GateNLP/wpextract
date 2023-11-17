from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest
from bs4 import BeautifulSoup
from helpers.df import ordered_col
from pytest_mock import MockerFixture

import extractor
from extractor.extractors.data.links import Linkable, LinkRegistry
from extractor.extractors.posts import (
    ensure_translations_undirected,
    load_posts,
    resolve_post_media,
    resolve_post_translations,
)
from extractor.parse.translations._resolver import TranslationLink


def mock_translation_extractor(post_bs: BeautifulSoup, link: str, translation_pickers):
    id_meta = post_bs.find("meta", attrs={"name": "post_id_for_mock"})
    post_id = int(id_meta["content"])
    if post_id == 1:
        current_lang = "en"
        translation = {
            "href": "https://example.org/fr/an-example-post-translation/",
            "lang": "fr",
        }
    elif post_id == 2:
        current_lang = "fr"
        translation = {"href": "https://example.org/an-example-post/", "lang": "en"}
    elif post_id == 3:
        return pd.Series([None, []])
    else:
        raise RuntimeError(f"Unknown mock post id {post_id} (type {type(post_id)})")

    return pd.Series(
        [
            current_lang,
            [
                TranslationLink(
                    **translation,
                    text=None,
                    destination=None,
                )
            ],
        ]
    )


@pytest.fixture
def _do_mock_translation_extractor(mocker: MockerFixture):
    mocker.patch(
        "extractor.extractors.posts.extract_translations", mock_translation_extractor
    )


@pytest.fixture
def scrape_urls_files(datadir: Path):
    def _scrape_path(slug):
        return (datadir / "scrape" / slug / "index.html").resolve()

    return {
        "https://example.org/an-example-post/": _scrape_path("an-example-post"),
        "https://example.org/fr/an-example-post-translation/": _scrape_path(
            "fr/an-example-post-translation"
        ),
        "https://example.org/an-unrelated-post/": _scrape_path("an-unrelated-post"),
    }


@pytest.fixture
def posts_df_and_registry(_do_mock_translation_extractor, datadir, scrape_urls_files):
    link_registry = LinkRegistry()
    return (
        load_posts(datadir / "posts.json", link_registry, scrape_urls_files, None),
        link_registry,
    )


@pytest.fixture
def posts_df(posts_df_and_registry):
    posts_df, _ = posts_df_and_registry
    return posts_df


def test_post_times(posts_df):
    post_1 = posts_df.loc[1]
    assert type(post_1.date_gmt) == pd.Timestamp
    assert type(post_1.modified_gmt) == pd.Timestamp

    assert post_1.date_gmt.tzinfo is None, "date_gmt had timezone information"
    assert post_1.modified_gmt.tzinfo is None, "modified_gmt had timezone information"

    assert post_1.date_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=6, hour=10, minute=0, second=0
    )
    assert post_1.modified_gmt.to_pydatetime() == datetime(
        year=2022, month=12, day=6, hour=10, minute=0, second=0
    )

    assert (
        len(posts_df.columns.intersection(["date", "modified"])) == 0
    ), "non-GMT time columns present"


def test_og_image_url(posts_df):
    assert posts_df.loc[1].og_image_url.endswith("og-image.jpg")
    assert posts_df.loc[2].og_image_url.endswith(
        "og-image-large.jpg"
    ), "not using first og image url"
    assert posts_df.loc[3].og_image_url is None


def test_link_locale(posts_df):
    assert posts_df["link_locale"].equals(ordered_col([None, "fr", None]))


def test_title_extract(posts_df):
    assert posts_df.loc[1]["title.text"] == "An Example Post"


def test_excerpt_extract(posts_df):
    assert posts_df.loc[1]["excerpt.text"] == "An excerpt about this post"


def test_language(posts_df):
    assert posts_df["language"].equals(ordered_col(["en", "fr", None]))


@pytest.fixture
def spy_extractor_data(mocker: MockerFixture):
    return mocker.spy(extractor.extractors.posts, "extract_content_data")


def test_extract_content_call(spy_extractor_data, posts_df):
    assert spy_extractor_data.call_count == 3


def test_columns_removed(posts_df):
    assert "_links" not in posts_df.columns


def test_adds_link_registry(posts_df_and_registry):
    posts_df, registry = posts_df_and_registry

    assert len(registry.links) == 3


def test_translations(posts_df_and_registry):
    posts_df, registry = posts_df_and_registry
    posts_df = resolve_post_translations(registry, posts_df)

    assert len(posts_df.loc[1]["translations"]) == 1
    assert posts_df.loc[1]["translations"][0].destination == Linkable(
        link="https://example.org/fr/an-example-post-translation/",
        data_type="post",
        idx=2,
    )
    assert posts_df.loc[1]["translations"][0].lang == "fr"

    assert len(posts_df.loc[2]["translations"]) == 1
    assert posts_df.loc[2]["translations"][0].destination == Linkable(
        link="https://example.org/an-example-post/", data_type="post", idx=1
    )
    assert posts_df.loc[2]["translations"][0].lang == "en"

    assert len(posts_df.loc[3]["translations"]) == 0


def test_translations_bidirectional(posts_df_and_registry):
    posts_df, registry = posts_df_and_registry
    posts_df = resolve_post_translations(registry, posts_df)
    # Currently 1 <-> 2, let's remove 1 <- 2
    posts_df.at[2, "translations"] = []

    posts_df = ensure_translations_undirected(posts_df)

    assert len(posts_df.loc[2, "translations"]) == 1

    posts_df = resolve_post_translations(registry, posts_df)
    assert posts_df.loc[2]["translations"][0].lang == "en"
    assert posts_df.loc[2]["translations"][0].destination == Linkable(
        link="https://example.org/an-example-post/", data_type="post", idx=1
    )


def test_resolves_media(posts_df_and_registry):
    posts_df, registry = posts_df_and_registry
    registry.add_linkable(
        "https://example.org/wp-content/uploads/2022/12/test-image.jpg", "media", 1
    )

    posts_df = resolve_post_media(registry, posts_df)

    assert posts_df.loc[1]["images"][0].destination == Linkable(
        link="https://example.org/wp-content/uploads/2022/12/test-image.jpg",
        data_type="media",
        idx=1,
    )
