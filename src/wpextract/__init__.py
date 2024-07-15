from importlib.metadata import version

from wpextract.downloader import WPDownloader as WPDownloader

from .extract import WPExtractor as WPExtractor

__version__ = version("wpextract")
