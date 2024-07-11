import logging
from pathlib import Path
from typing import Any, Callable, Optional

from wpextract.download.exceptions import WordPressApiNotV2
from wpextract.download.exporter import Exporter
from wpextract.download.requestsession import RequestSession
from wpextract.download.wpapi import WPApi


class WPDownloader:
    """Manages the download of data from a WordPress site."""

    def __init__(
        self,
        target: str,
        out_path: Path,
        data_types: list[str],
        session: Optional[RequestSession] = None,
        json_prefix: Optional[str] = None,
    ):
        """Initializes the WPDownloader object.

        Args:
            target: the target WordPress site URL
            out_path: the output path for the downloaded data
            data_types: set of data types to download
            session : request session. Will be created from default constructor if not provided.
            json_prefix: prefix to prepend to JSON file names
        """
        self.target = target
        self.out_path = out_path
        self.data_types = data_types
        self.session = session if session else RequestSession()
        self._test_session()
        self.scanner = WPApi(self.target, session=self.session)
        self.json_prefix = json_prefix

    def _test_session(self):
        try:
            self.session.get(self.target)
            logging.info("Connected successfully")
        except Exception as e:
            logging.error("Failed to connect to the server")
            raise e

    def download(self):
        """Download and export the requested data lists."""
        if "users" in self.data_types:
            self._list_obj(WPApi.USER)
        if "tags" in self.data_types:
            self._list_obj(WPApi.TAG)
        if "categories" in self.data_types:
            self._list_obj(WPApi.CATEGORY)
        if "posts" in self.data_types:
            self._list_obj(WPApi.POST)
        if "pages" in self.data_types:
            self._list_obj(WPApi.PAGE)
        if "comments" in self.data_types:
            self._list_obj(WPApi.COMMENT)
        if "media" in self.data_types:
            self._list_obj(WPApi.MEDIA)

    def download_media_files(self, session: RequestSession, dest: Path):
        """Download site media files.

        Args:
            session: the request session to use
            dest: destination directory for media
        """
        logging.info("Pulling media URLs")
        media, slugs = self.scanner.get_media_urls("all", cache=True)

        if len(media) == 0:
            logging.warning("No media found corresponding to the criteria")
            return
        logging.info(f"{len(media)} media URLs found")

        number_dl = Exporter.download_media(session, media, dest)
        logging.info(f"Downloaded {number_dl} media files")

    def _get_fetch_or_list_type(self, obj_type, plural=False):
        """Returns a dict containing all necessary metadata about the obj_type to list and fetch data.

        Args:
            obj_type: the type of the object
            plural: whether the name must be plural or not
        """
        export_func = None
        obj_name = ""
        if obj_type == WPApi.USER:
            export_func = Exporter.export_users
            obj_name = "Users" if plural else "User"
        elif obj_type == WPApi.TAG:
            export_func = Exporter.export_tags
            obj_name = "Tags" if plural else "Tag"
        elif obj_type == WPApi.CATEGORY:
            export_func = Exporter.export_categories
            obj_name = "Categories" if plural else "Category"
        elif obj_type == WPApi.POST:
            export_func = Exporter.export_posts
            obj_name = "Posts" if plural else "Post"
        elif obj_type == WPApi.PAGE:
            export_func = Exporter.export_pages
            obj_name = "Pages" if plural else "Page"
        elif obj_type == WPApi.COMMENT:
            export_func = Exporter.export_comments_interactive
            obj_name = "Comments" if plural else "Comment"
        elif obj_type == WPApi.MEDIA:
            export_func = Exporter.export_media
            obj_name = "Media"

        return {
            "export_func": export_func,
            "obj_name": obj_name,
        }

    def _list_obj(self, obj_type, start=None, limit=None, cache=True):
        prop = self._get_fetch_or_list_type(obj_type, plural=True)
        logging.info(f"Downloading {prop['obj_name']}")

        try:
            kwargs = {}
            if obj_type == WPApi.POST:
                kwargs = {"comments": False}
            obj_list = self.scanner.get_obj_list(
                obj_type, start, limit, cache, kwargs=kwargs
            )

            WPDownloader.export_decorator(
                export_func=prop["export_func"],
                file_name=prop["obj_name"].lower(),
                json_path=self.out_path,
                json_prefix=self.json_prefix,
                values=obj_list,
            )
        except WordPressApiNotV2:
            logging.error("The API does not support WP V2")
        except OSError as e:
            logging.error(f"Could not open {e.filename} for writing")
        logging.info(f"Completed downloading {prop['obj_name']}")

    @staticmethod
    def export_decorator(
        export_func: Callable,
        file_name: str,
        json_path: Path,
        json_prefix: str,
        values: Any,
        kwargs: Optional[dict] = None,
    ) -> None:
        """Call the export function with a constructed filename.

        Args:
            export_func: the function to run
            file_name: the name of the export file
            json_path: the path to the output directory
            json_prefix: a prefix for the export file
            values: data to be exported
            kwargs: arguments to pass to the export function
        """
        kwargs = kwargs or {}

        filename = file_name + ".json"
        if json_prefix is not None:
            filename = json_prefix + "-" + filename

        json_file = json_path / filename
        export_func(values, json_file, **kwargs)
