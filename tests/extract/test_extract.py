from pathlib import Path

import pandas as pd
from extractor.extract import WPExtractor


def _assert_extractor_valid(extractor: WPExtractor):
    assert isinstance(extractor.posts, pd.DataFrame)
    assert isinstance(extractor.media, pd.DataFrame)
    assert isinstance(extractor.tags, pd.DataFrame)
    assert isinstance(extractor.categories, pd.DataFrame)
    assert isinstance(extractor.users, pd.DataFrame)
    assert isinstance(extractor.pages, pd.DataFrame)


def _assert_output_valid(out_dir: Path):
    assert (out_dir / "posts.json").is_file()
    assert (out_dir / "media.json").is_file()
    assert (out_dir / "tags.json").is_file()
    assert (out_dir / "categories.json").is_file()
    assert (out_dir / "users.json").is_file()
    assert (out_dir / "pages.json").is_file()


def test_extract_no_scrape(datadir):
    extractor = WPExtractor(json_root=datadir / "json")

    extractor.extract()
    _assert_extractor_valid(extractor)

    out_dir = datadir / "out_json"
    out_dir.mkdir()
    extractor.export(out_dir)
    _assert_output_valid(out_dir)


def test_extract_scrape(datadir):
    extractor = WPExtractor(json_root=datadir / "json", scrape_root=datadir / "scrape")

    extractor.extract()
    _assert_extractor_valid(extractor)

    assert "translations" in extractor.posts.columns

    out_dir = datadir / "out_json"
    out_dir.mkdir()
    extractor.export(out_dir)
    _assert_output_valid(out_dir)
