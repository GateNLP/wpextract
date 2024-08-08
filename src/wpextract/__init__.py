from importlib.metadata import version

from wpextract.downloader import WPDownloader as WPDownloader
from wpextract.extract import WPExtractor as WPExtractor

__version__ = version("wpextract")
