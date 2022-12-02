import logging
from pathlib import Path
from typing import Dict, Optional

from pandas import DataFrame

from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.io import export_df
from extractor.extractors.media import load_media
from extractor.extractors.posts import load_posts
from extractor.extractors.tags import load_tags
from extractor.scrape.crawler import ScrapeCrawl
from extractor.util.file import prefix_filename


class WPExtractor:
    """Main class to extract data."""

    posts: DataFrame
    media: DataFrame
    tags: DataFrame
    categories: DataFrame
    scrape_url_mapping: Dict[str, Path]

    def __init__(
        self, json_root: Path, scrape_root: Path, json_prefix: Optional[str] = None
    ):
        """Create a new extractor.

        Args:
            json_root: Path to directory of JSON files
            scrape_root: Path to scrape directory
            json_prefix: Prefix of files in ``json_root``
        """
        self.json_root = json_root
        self.scrape_root = scrape_root
        self.json_prefix = json_prefix
        self.link_registry = LinkRegistry()

    def extract(self) -> None:
        """Perform the extraction."""
        logging.info("Beginning scrape crawl")
        self._crawl_scrape()
        logging.info("Beginning media extraction")
        self._extract_media()
        logging.info("Beginning post extraction")
        self._extract_posts()
        logging.info("Beginning tag extraction")
        self._extract_tags()
        logging.info("Beginning categories extraction")
        self._extract_categories()

    def _crawl_scrape(self):
        crawl = ScrapeCrawl(self.scrape_root)
        crawl.crawl()
        self.scrape_url_mapping = crawl.get_link_abs_path()

    def _extract_posts(self):
        json_file = self.json_root / prefix_filename("posts.json", self.json_prefix)
        self.posts = load_posts(json_file, self.link_registry, self.scrape_url_mapping)

    def _extract_media(self):
        json_file = self.json_root / prefix_filename("media.json", self.json_prefix)
        self.media = load_media(json_file)

    def _extract_tags(self):
        json_file = self.json_root / prefix_filename("tags.json", self.json_prefix)
        self.tags = load_tags(json_file, self.link_registry)

    def _extract_categories(self):
        json_file = self.json_root / prefix_filename(
            "categories.json", self.json_prefix
        )
        self.categories = load_tags(json_file, self.link_registry)

    def export(self, out_dir: Path) -> None:
        """Save scrape results to ``out_dir``."""
        export_df(self.posts, out_dir / "posts.json")
        export_df(self.media, out_dir / "media.json")
        export_df(self.tags, out_dir / "tags.json")
        export_df(self.categories, out_dir / "categories.json")
