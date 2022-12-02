from pathlib import Path
from typing import Dict, Optional

from pandas import DataFrame

from extractor.links import LinkRegistry
from extractor.posts import load_posts
from extractor.scrape.crawler import ScrapeCrawl
from extractor.util.file import prefix_filename
from extractor.util.json import export_df


class WPExtractor:
    """Main class to extract data."""

    posts: DataFrame
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
        self._crawl_scrape()
        self._extract_posts()

    def _crawl_scrape(self):
        crawl = ScrapeCrawl(self.scrape_root)
        crawl.crawl()
        self.scrape_url_mapping = crawl.get_link_abs_path()

    def _extract_posts(self):
        json_file = self.json_root / prefix_filename("posts.json", self.json_prefix)
        self.posts = load_posts(json_file, self.link_registry, self.scrape_url_mapping)

    def export(self, out_dir: Path) -> None:
        """Save scrape results to ``out_dir``."""
        export_df(self.posts, out_dir / "posts.json")
