import json
import logging
from pathlib import Path

import pytest
from wpextract.scrape.crawler import ScrapeCrawl

EXPECTED_PAGES = {
    "an-example-post/index.html": "https://example.org/an-example-post/",
    "an-unrelated-post/index.html": "https://example.org/an-unrelated-post/",
    "fr/an-example-post-translation/index.html": "https://example.org/fr/an-example-post-translation/",
}


def expected_link_abs_path(root_dir: Path):
    root_path = str(root_dir.resolve())
    return {link: Path(root_path + "/" + path) for path, link in EXPECTED_PAGES.items()}


def test_scrape_crawl(shared_datadir):
    root_path = shared_datadir / "scrape"

    crawl = ScrapeCrawl(root_path)

    crawl.crawl()

    assert crawl.found_pages == EXPECTED_PAGES

    assert crawl.failed_docs == ["no-self-url.html"]

    assert crawl.get_link_abs_path() == expected_link_abs_path(root_path)

    assert (root_path / "url_cache.json").is_file()
    assert json.loads((root_path / "url_cache.json").read_text()) == json.loads((shared_datadir / "expected_url_cache.json" ).read_text())


def test_recrawl_different_version(caplog, shared_datadir: Path):
    root_path = shared_datadir / "scrape"
    (shared_datadir / "diff_version_url_cache.json").rename(
        root_path / "url_cache.json"
    )

    with caplog.at_level(logging.INFO):
        crawl = ScrapeCrawl(root_path)
        crawl.crawl()

    assert crawl.found_pages != {}
    assert "out of date" in caplog.text


def test_scrape_crawl_cached(shared_datadir: Path):
    root_path = shared_datadir / "scrape"
    crawl = ScrapeCrawl(root_path)
    crawl.crawl()

    (root_path / "an-example-post/index.html").unlink()

    crawl2 = ScrapeCrawl(root_path)
    crawl2.crawl()
    assert crawl2.found_pages == EXPECTED_PAGES


def test_duplicate_url(caplog, shared_datadir: Path):
    root_path = shared_datadir / "scrape"
    (root_path / "dupe.html").write_text(
        (root_path / "an-example-post/index.html").read_text()
    )

    with caplog.at_level(logging.INFO):
        crawl = ScrapeCrawl(root_path)
        crawl.crawl()

    assert "but has already been found" in caplog.text
    assert "https://example.org/an-example-post/" in crawl.found_pages.values()


def test_crawl_non_dir(shared_datadir: Path):
    with pytest.raises(ValueError, match="is not a directory"):
        ScrapeCrawl(shared_datadir / "notreal")
