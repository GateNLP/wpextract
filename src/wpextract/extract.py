import logging
from pathlib import Path
from typing import Optional

from pandas import DataFrame

from wpextract.extractors.categories import load_categories
from wpextract.extractors.data.links import LinkRegistry
from wpextract.extractors.io import export_df
from wpextract.extractors.media import load_media
from wpextract.extractors.pages import load_pages
from wpextract.extractors.posts import (
    ensure_translations_undirected,
    load_posts,
    resolve_post_links,
    resolve_post_translations,
)
from wpextract.extractors.tags import load_tags
from wpextract.extractors.users import load_users
from wpextract.parse.translations import PickerListType
from wpextract.scrape.crawler import ScrapeCrawl
from wpextract.util.file import prefix_filename


class WPExtractor:
    """Manages the extraction of data from a WordPress site."""

    json_root: Path
    scrape_root: Optional[Path]
    json_prefix: Optional[str]
    translation_pickers: Optional[PickerListType]

    link_registry: LinkRegistry
    """Registry of known URLs and their corresponding data items."""

    posts: Optional[DataFrame]
    """DataFrame of extracted posts."""
    media: Optional[DataFrame]
    """DataFrame of extracted media."""
    tags: Optional[DataFrame]
    """DataFrame of extracted tags."""
    categories: Optional[DataFrame]
    """DataFrame of extracted categories."""
    users: Optional[DataFrame]
    """DataFrame of extracted users."""
    pages: Optional[DataFrame]
    """DataFrame of extracted pages."""

    scrape_url_mapping: dict[str, Path]

    def __init__(
        self,
        json_root: Path,
        scrape_root: Optional[Path] = None,
        json_prefix: Optional[str] = None,
        translation_pickers: Optional[PickerListType] = None,
    ):
        """Create a new extractor.

        Args:
            json_root: Path to directory of JSON files
            scrape_root: Path to scrape directory
            json_prefix: Prefix of files in ``json_root``
            translation_pickers: Supply a custom list of translation pickers
        """
        self.json_root = json_root
        self.scrape_root = scrape_root
        self.json_prefix = json_prefix
        self.link_registry = LinkRegistry()
        self.translation_pickers = translation_pickers

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
        if self.scrape_root is None:
            logging.info("No scrape root specified, skipping")
            self.scrape_url_mapping = {}
            return

        crawl = ScrapeCrawl(self.scrape_root)
        crawl.crawl()
        self.scrape_url_mapping = crawl.get_link_abs_path()

    def _extract_posts(self):
        json_file = self.json_root / self._prefix_filename("posts.json")
        self.posts = load_posts(
            path=json_file,
            link_registry=self.link_registry,
            scrape_urls_files=self.scrape_url_mapping,
            translation_pickers=self.translation_pickers,
        )

    def _extract_media(self):
        json_file = self.json_root / self._prefix_filename("media.json")
        self.media = load_media(json_file, self.link_registry)

    def _extract_tags(self):
        json_file = self.json_root / self._prefix_filename("tags.json")
        self.tags = load_tags(json_file, self.link_registry)

    def _extract_categories(self):
        json_file = self.json_root / self._prefix_filename("categories.json")
        self.categories = load_categories(json_file, self.link_registry)

    def _extract_users(self):
        json_file = self.json_root / self._prefix_filename("users.json")
        self.users = load_users(json_file)

    def _extract_pages(self):
        json_file = self.json_root / self._prefix_filename("pages.json")
        self.pages = load_pages(json_file, self.link_registry)

    def _resolve_post_links(self):
        self.posts = resolve_post_links(self.link_registry, self.posts)
        if "translations" in self.posts.columns:
            self.posts = resolve_post_translations(self.link_registry, self.posts)
            self.posts = ensure_translations_undirected(self.posts)
            self.posts = resolve_post_translations(self.link_registry, self.posts)

    def export(self, out_dir: Path) -> None:
        """Save scrape results!

        Args:
            out_dir: Path to output directory
        """
        logging.info("Beginning export")
        export_df(self.posts, out_dir / self._prefix_filename("posts.json"))
        export_df(self.pages, out_dir / self._prefix_filename("pages.json"))
        export_df(self.media, out_dir / self._prefix_filename("media.json"))
        export_df(self.tags, out_dir / self._prefix_filename("tags.json"))
        export_df(self.categories, out_dir / self._prefix_filename("categories.json"))
        export_df(self.users, out_dir / self._prefix_filename("users.json"))
        logging.info("Completed export")
