import logging
from pathlib import Path
from typing import List, Optional

from wpextract.dl.exceptions import WordPressApiNotV2
from wpextract.dl.exporter import Exporter
from wpextract.dl.requestsession import RequestSession
from wpextract.dl.wpapi import WPApi


class WPDownloader:
    """Manages the download of data from a WordPress site."""

    def __init__(
        self,
        target: str,
        out_path: Path,
        data_types: List[str],
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

    def download_media_files(self, session: RequestSession, dest: str):
        """Download site media files.

        Args:
            session: the request session to use
            dest: destination directory for media
        """
        print("Pulling media URLs")
        media, slugs = self.scanner.get_media_urls("all", cache=True)

        if len(media) == 0:
            logging.warning("No media found corresponding to the criteria")
            return
        print(f"{len(media)} media URLs found")

        number_dl = Exporter.download_media(session, media, dest)
        print(f"Downloaded {number_dl} media files")

    def _get_fetch_or_list_type(self, obj_type, plural=False):
        """Returns a dict containing all necessary metadata about the obj_type to list and fetch data

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
        elif obj_type == WPApi.NAMESPACE:
            export_func = Exporter.export_namespaces
            obj_name = "Namespaces" if plural else "Namespace"

        return {
            "export_func": export_func,
            "obj_name": obj_name,
        }

    def _list_obj(self, obj_type, start=None, limit=None, cache=True):
        prop = self._get_fetch_or_list_type(obj_type, plural=True)
        print(prop["obj_name"] + " details")

        try:
            kwargs = {}
            if obj_type == WPApi.POST:
                kwargs = {"comments": False}
            obj_list = self.scanner.get_obj_list(
                obj_type, start, limit, cache, kwargs=kwargs
            )

            WPDownloader.export_decorator(
                export_func=prop["export_func"],
                export_str=prop["obj_name"].lower(),
                json_path=self.out_path,
                json_prefix=self.json_prefix,
                values=obj_list,
            )
        except WordPressApiNotV2:
            logging.error("The API does not support WP V2")
        except IOError as e:
            logging.error(f"Could not open {e.filename} for writing")
        print()

    @staticmethod
    def export_decorator(  # noqa: D102
        export_func, export_str, json_path: Path, json_prefix: str, values, kwargs=None
    ):
        kwargs = kwargs or {}

        filename = export_str + ".json"
        if json_prefix is not None:
            filename = json_prefix + "-" + filename

        json_file = json_path / filename
        export_func(values, Exporter.JSON, json_file, **kwargs)
