import urllib.parse
from pathlib import Path
from typing import Dict, Optional

from bs4 import BeautifulSoup

from extractor.util.str import ensure_suffix, remove_prefix


def find_path(scrape_root: Path, link: str) -> Optional[Path]:
    """Find the scrape of a link.

    Extracts the path from the link and from the scrape root, checks if there is a
    matching HTML file.

    A number of different files are tried due to wget's behaviour with long URLs.

    Examples:
        >>> find_path("/scrape", "https://example.org/my/path/")
        # Checks:
        # /scrape/my/path/index.html
        # /scrape/my/path/index..html
        # /scrape/my/path/.html
        PosixPath('/scrape/my/path.index.html')

    # TODO: Eliminate this by pre-crawling scrape and collecting canonical URLs

    Args:
        scrape_root: The path of a scrape folder
        link: The page link

    Returns:
        The resolved path or None if it could not be found.
    """
    link_parsed = urllib.parse.urlparse(link)
    link_path = remove_prefix(link_parsed.path, "/")

    link_as_dir_path = scrape_root / ensure_suffix(link_path, "/")
    if link_as_dir_path.is_dir():
        dir_index_path = link_as_dir_path / "index.html"
        if dir_index_path.is_file():
            return dir_index_path
        else:
            print("is not a file", dir_index_path)

        double_dot_index_path = link_as_dir_path / "index..html"
        if double_dot_index_path.is_file():
            return double_dot_index_path
        else:
            print("is not a file", double_dot_index_path)

        no_name_html_file = link_as_dir_path / ".html"
        if no_name_html_file.is_file():
            return no_name_html_file
        else:
            print("is not a file", no_name_html_file)

    else:
        print("is not a directory", link_as_dir_path)

    return None


def load_scrape(
    scrape_urls_files: Dict[str, Path], link: str
) -> Optional[BeautifulSoup]:
    """Find, load and parse the scrape of a link.

    Args:
        scrape_urls_files: A dictionary of site URLs to scrape file paths
        link: The link of the page to find.

    Returns:
        The parsed document or None if it ould not be found.
    """
    path = scrape_urls_files.get(link)

    if path is None:
        print("Failed to resolve link", link)
        return None

    html_raw = path.read_text()
    doc = BeautifulSoup(html_raw, "lxml")
    return doc
