from pathlib import Path
from typing import List

from extractor.dl.console import Console
from extractor.dl.exceptions import WordPressApiNotV2
from extractor.dl.exporter import Exporter
from extractor.dl.requestsession import RequestSession
from extractor.dl.wpapi import WPApi


def get_session(target: str, proxy=None, cookies=None, authorization=None):
    session = RequestSession(proxy=proxy, cookies=cookies, authorization=authorization)
    try:
        session.get(target)
        Console.log_success("Connection OK")
    except Exception:
        Console.log_error("Failed to connect to the server")
        exit(0)
    return session


class WPDownloader:
    def __init__(self, target: str, out_path: Path, data_types: List[str]):
        self.target = target
        self.out_path = out_path
        self.data_types = data_types
        self.session = get_session(target)
        self.scanner = WPApi(self.target, session=self.session)

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

    def download_media_files(self, dest):
        """Download site media files.

        Args:
            dest: destination directory for media
        """
        print("Pulling media URLs")
        media, slugs = self.scanner.get_media_urls("all", cache=True)

        if len(media) == 0:
            Console.log_error("No media found corresponding to the criteria")
            return
        print("%d media URLs found" % len(media))
        answer = input("Do you wish to proceed to download? (y/N)")
        if answer.lower() != "y":
            return
        print("Note: Only files over 10MB are logged here")

        number_dl = Exporter.download_media(media, dest)
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
                json=self.out_path,
                values=obj_list,
            )
        except WordPressApiNotV2:
            Console.log_error("The API does not support WP V2")
        except IOError as e:
            Console.log_error("Could not open %s for writing" % e.filename)
        print()

    @staticmethod
    def export_decorator(  # noqa: D102
        export_func, export_str, json, values, kwargs=None
    ):
        kwargs = kwargs or {}
        if json is not None:
            json_file = json + "-" + export_str
            export_func(values, Exporter.JSON, json_file, **kwargs)
