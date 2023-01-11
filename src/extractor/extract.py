import logging
from pathlib import Path
from typing import Dict, Optional

from pandas import DataFrame

from extractor.extractors.data.links import LinkRegistry
from extractor.extractors.io import export_df
from extractor.extractors.media import load_media
from extractor.extractors.pages import load_pages
from extractor.extractors.posts import (
    load_posts,
    resolve_post_links,
    resolve_post_translations,
)
from extractor.extractors.tags import load_tags
from extractor.extractors.users import load_users
from extractor.scrape.crawler import ScrapeCrawl
from extractor.util.file import prefix_filename


class WPExtractor:
    """Main class to extract data."""

    link_registry: LinkRegistry
    posts: Optional[DataFrame]
    media: Optional[DataFrame]
    tags: Optional[DataFrame]
    categories: Optional[DataFrame]
    users: Optional[DataFrame]
    pages: Optional[DataFrame]
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
        logging.info("Beginning extraction")
        logging.info("Beginning scrape crawl")
        self._crawl_scrape()
        logging.info("Beginning media extraction")
        self._extract_media()
        logging.info("Beginning post extraction")
        self._extract_posts()
        logging.info("Beginning page extraction")
        self._extract_pages()
        logging.info("Beginning tag extraction")
        self._extract_tags()
        logging.info("Beginning categories extraction")
        self._extract_categories()
        logging.info("Beginning user extraction")
        self._extract_users()
        logging.info("Beginning post link matching")
        self._resolve_post_links()
        logging.info("Extraction complete")

    def _prefix_filename(self, file_name):
        return prefix_filename(file_name, self.json_prefix)

    def _crawl_scrape(self):
        crawl = ScrapeCrawl(self.scrape_root)
        crawl.crawl()
        self.scrape_url_mapping = crawl.get_link_abs_path()

    def _extract_posts(self):
        json_file = self.json_root / self._prefix_filename("posts.json")
        self.posts = load_posts(json_file, self.link_registry, self.scrape_url_mapping)

    def _extract_media(self):
        json_file = self.json_root / self._prefix_filename("media.json")
        self.media = load_media(json_file)

    def _extract_tags(self):
        json_file = self.json_root / self._prefix_filename("tags.json")
        self.tags = load_tags(json_file, self.link_registry)

    def _extract_categories(self):
        json_file = self.json_root / self._prefix_filename("categories.json")
        self.categories = load_tags(json_file, self.link_registry)

    def _extract_users(self):
        json_file = self.json_root / self._prefix_filename("users.json")
        self.users = load_users(json_file)

    def _extract_pages(self):
        json_file = self.json_root / self._prefix_filename("pages.json")
        self.pages = load_pages(json_file, self.link_registry)

    def _resolve_post_links(self):
        self.posts = resolve_post_links(self.link_registry, self.posts)
        self.posts = resolve_post_translations(self.link_registry, self.posts)

    def export(self, out_dir: Path) -> None:
        """Save scrape results to ``out_dir``."""
        logging.info("Beginning export")
        export_df(self.posts, out_dir / self._prefix_filename("posts.json"))
        export_df(self.pages, out_dir / self._prefix_filename("pages.json"))
        export_df(self.media, out_dir / self._prefix_filename("media.json"))
        export_df(self.tags, out_dir / self._prefix_filename("tags.json"))
        export_df(self.categories, out_dir / self._prefix_filename("categories.json"))
        export_df(self.users, out_dir / self._prefix_filename("users.json"))
        logging.info("Completed export")
