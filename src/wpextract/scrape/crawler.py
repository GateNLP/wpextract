import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from tqdm.auto import tqdm

from wpextract.scrape.processor import extract_self_url, self_url_strainer

# Increment to invalidate old caches
SCRAPE_CRAWL_VERSION = 1


class ScrapeCrawl:
    """Crawl a scraped website to get original page URLs.

    Finds the original URL of every HTML file in the crawl from either the canonical
    link tag or the OpenGraph URL meta tag.

    Crawl results are stored in ``url_cache.json`` in the provided ``root_path``.
    If this file is present, the scrape will not be re-crawled. It contains the
    ``found_pages`` and ``failed_docs`` properties.

    Attributes:
        found_pages: Dictionary of path relative to `root_path` and the discovered URL.
        failed_docs: List of paths relative to `root_path` where a URL could
            not be discovered.
    """

    found_pages: dict[str, str]
    failed_docs: list[str]
    crawled = False

    def __init__(self, root_path: Path):
        """Init a new crawl instance.

        Args:
            root_path: The root path of the crawl (i.e. ``/`` on the website)

        Raises:
            ValueError: If the root path is not a directory.
        """
        if not root_path.is_dir():
            raise ValueError(f"Root path {root_path} is not a directory")

        self.root_path = root_path
        self.found_pages = {}
        self.failed_docs = []

        if self._get_cache_path().is_file():
            self._import()

    def _get_cache_path(self) -> Path:
        return self.root_path / "url_cache.json"

    def _export(self):
        with open(self._get_cache_path(), "w") as f:
            json.dump(
                {
                    "found": self.found_pages,
                    "failed": self.failed_docs,
                    "version": SCRAPE_CRAWL_VERSION,
                },
                f,
            )

    def _import(self):
        with open(self._get_cache_path()) as f:
            data = json.load(f)

        if "version" not in data or data["version"] != SCRAPE_CRAWL_VERSION:
            logging.info("Scrape crawl cache is out of date, re-crawling.")
            return

        self.found_pages = data["found"]
        self.failed_docs = data["failed"]
        self.crawled = True

    def crawl(self) -> None:
        """Perform the crawl or use the cached result."""
        if self.crawled:
            logging.info("Skipping scrape crawl, cached results available.")
            return

        files = list(self.root_path.glob("**/*.html"))

        for path in tqdm(files, desc="Crawling Scrape"):
            relative_path = str(path.relative_to(self.root_path))

            doc = BeautifulSoup(
                path.read_text(errors="ignore"),
                "lxml",
                parse_only=self_url_strainer,
            )
            doc_url = extract_self_url(doc)

            if doc_url is None:
                self.failed_docs.append(path)
                logging.warning(f'Failed to find self-URL in doc "{path}"')
                continue

            if doc_url in self.found_pages:
                logging.info(
                    f"URL {doc_url} retrieved for {relative_path}, but has already been"
                    f"found for {self.found_pages[relative_path]}"
                )
                continue

            self.found_pages[relative_path] = doc_url

        self._export()

    def get_link_abs_path(self) -> dict[str, Path]:
        """Get the mapping as original link to absolute file path.

        Absolute paths are resolved with the ``root_path`` and relative path from the
        crawl. Webpages may not exist if the crawl was loaded from cache.

        Returns:
            Dictionary of URLs to absolute paths.
        """
        return {
            link: (self.root_path / Path(relative_path)).resolve()
            for relative_path, link in self.found_pages.items()
        }
