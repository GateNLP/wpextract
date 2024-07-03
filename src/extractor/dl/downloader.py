from pathlib import Path
from typing import List

from extractor.dl.console import Console
from extractor.dl.exceptions import WordPressApiNotV2
from extractor.dl.exporter import Exporter
from extractor.dl.infodisplayer import InfoDisplayer
from extractor.dl.interactive import InteractiveShell
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

    def _get_fetch_or_list_type(self, obj_type, plural=False):
        """Returns a dict containing all necessary metadata about the obj_type to list and fetch data

        Args:
            obj_type: the type of the object
            plural: whether the name must be plural or not
        """
        display_func = None
        export_func = None
        additional_info = {}
        obj_name = ""
        if obj_type == WPApi.USER:
            display_func = InfoDisplayer.display_users
            export_func = Exporter.export_users
            additional_info = {}
            obj_name = "Users" if plural else "User"
        elif obj_type == WPApi.TAG:
            display_func = InfoDisplayer.display_tags
            export_func = Exporter.export_tags
            additional_info = {}
            obj_name = "Tags" if plural else "Tag"
        elif obj_type == WPApi.CATEGORY:
            display_func = InfoDisplayer.display_categories
            export_func = Exporter.export_categories
            additional_info = {"category_list": self.scanner.categories}
            obj_name = "Categories" if plural else "Category"
        elif obj_type == WPApi.POST:
            display_func = InfoDisplayer.display_posts
            export_func = Exporter.export_posts
            additional_info = {
                "tags_list": self.scanner.tags,
                "categories_list": self.scanner.categories,
                "users_list": self.scanner.users,
            }
            obj_name = "Posts" if plural else "Post"
        elif obj_type == WPApi.PAGE:
            display_func = InfoDisplayer.display_pages
            export_func = Exporter.export_pages
            additional_info = {
                "parent_pages": self.scanner.pages,
                "users": self.scanner.users,
            }
            obj_name = "Pages" if plural else "Page"
        elif obj_type == WPApi.COMMENT:
            display_func = InfoDisplayer.display_comments
            export_func = Exporter.export_comments_interactive
            additional_info = {
                #'parent_posts': self.scanner.posts, # May be too verbose
                "users": self.scanner.users
            }
            obj_name = "Comments" if plural else "Comment"
        elif obj_type == WPApi.MEDIA:
            display_func = InfoDisplayer.display_media
            export_func = Exporter.export_media
            additional_info = {"users": self.scanner.users}
            obj_name = "Media"
        elif obj_type == WPApi.NAMESPACE:
            display_func = InfoDisplayer.display_namespaces
            export_func = Exporter.export_namespaces
            additional_info = {}
            obj_name = "Namespaces" if plural else "Namespace"

        return {
            "display_func": display_func,
            "export_func": export_func,
            "additional_info": additional_info,
            "obj_name": obj_name,
        }

    def _list_obj(self, obj_type, start=None, limit=None, is_all=True, cache=True):
        prop = self._get_fetch_or_list_type(obj_type, plural=True)
        print(prop["obj_name"] + " details")

        try:
            kwargs = {}
            if obj_type == WPApi.POST:
                kwargs = {"comments": False}
            obj_list = self.scanner.get_obj_list(
                obj_type, start, limit, cache, kwargs=kwargs
            )
            prop["display_func"](obj_list)
            InteractiveShell.export_decorator(
                prop["export_func"],
                is_all,
                prop["obj_name"].lower(),
                self.out_path,
                csv=None,
                values=obj_list,
            )
        except WordPressApiNotV2:
            Console.log_error("The API does not support WP V2")
        except IOError as e:
            Console.log_error("Could not open %s for writing" % e.filename)
        print()
