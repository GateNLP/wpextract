import copy
import logging
import math
from json.decoder import JSONDecodeError
from typing import Any, Literal, Optional, Union

from tqdm.auto import tqdm

from wpextract.download.exceptions import (
    NoWordpressApi,
    NSNotFoundException,
    WordPressApiNotV2,
)
from wpextract.download.requestsession import (
    HTTPError,
    HTTPError404,
    HTTPErrorInvalidPage,
    RequestSession,
)
from wpextract.download.utils import (
    get_by_id,
    get_content_as_json,
    url_path_join,
)

WPObject = dict[str, Any]
ObjectsAndTotal = tuple[list[WPObject], Optional[int]]


class WPApi:
    """Queries the WordPress API to retrieve information."""

    # Object types
    POST = 0
    """The post type"""
    POST_REVISION = 1
    """The post revision type"""
    WP_BLOCK = 2
    """The Gutenberg block type"""
    CATEGORY = 3
    """The category type"""
    TAG = 4
    """The tag type"""
    PAGE = 5
    """The page type"""
    COMMENT = 6
    """The comment type"""
    MEDIA = 7
    """The media type"""
    USER = 8
    """The user type"""
    THEME = 9
    """The theme type"""
    NAMESPACE = 10
    """The namespace type"""
    # SEARCH_RESULT = 10
    ALL_TYPES = 20
    """Constant representing all types"""

    def __init__(
        self,
        target: str,
        api_path: str = "wp-json/",
        session: Optional[RequestSession] = None,
    ) -> None:
        """Creates a new instance of WPApi.

        Args:
            target: the target of the scan
            api_path: the api path, if non-default
            session: the requests session object to use for HTTP requests
        """
        self.api_path = api_path
        self.has_v2: Optional[bool] = None
        self.name = None
        self.description = None
        self.url = target
        self.basic_info: Optional[dict[str, Any]] = None

        if session is not None:
            self.s = session
        else:
            self.s = RequestSession()

    def get_basic_info(self) -> dict[Any, Any]:
        """Collects and stores basic information about the target.

        Raises:
            NoWordpressApi: The target does not have a reachable WordPress API

        Returns:
            The basic information about the target
        """
        rest_url = url_path_join(self.url, self.api_path)
        if self.basic_info is not None:
            return self.basic_info

        try:
            req = self.s.get(rest_url)
        except Exception as e:
            raise NoWordpressApi from e
        if req.status_code >= 400:
            raise NoWordpressApi

        try:
            self.basic_info = get_content_as_json(req)
        except JSONDecodeError as e:
            raise NoWordpressApi from e

        if "name" in self.basic_info.keys():
            self.name = self.basic_info["name"]

        if "description" in self.basic_info.keys():
            self.description = self.basic_info["description"]

        if (
            "namespaces" in self.basic_info.keys()
            and "wp/v2" in self.basic_info["namespaces"]
        ):
            self.has_v2 = True

        return self.basic_info

    def crawl_pages(
        self,
        url: str,
        start: Optional[int] = None,
        num: Optional[int] = None,
        display_progress: bool = True,
    ) -> tuple[list[WPObject], int]:
        """Crawls all pages while there is at least one result for the given endpoint or tries to get pages from start to end.

        Args:
            url: the URL to crawl
            start: the start index
            num: the number of entries to retrieve
            display_progress: whether to display a progress bar

        Raises:
            WordPressApiNotV2: The target does not support the WordPress API v2
            HTTPError: An HTTP error is encountered before any content is retrieved

        Returns:
            A tuple containing the list of entries and the total number of entries
        """
        page = 1
        total_entries = 0
        total_pages = 0
        more_entries = True
        entries: list[WPObject] = []
        base_url = url
        entries_left = 1
        per_page = 10
        if start is not None:
            page = math.floor(start / per_page) + 1
        if num is not None:
            entries_left = num

        # Initialise placeholder for progress bar
        pbar = None

        while more_entries and entries_left > 0:
            rest_url = url_path_join(self.url, self.api_path, (base_url % page))
            if start is not None:
                rest_url += "&per_page=%d" % per_page
            try:
                req = self.s.get(rest_url)
                if (
                    page == 1
                    or (start is not None and page == math.floor(start / per_page) + 1)
                ) and "X-WP-Total" in req.headers:
                    total_entries = int(req.headers["X-WP-Total"])
                    total_pages = int(req.headers["X-WP-TotalPages"])
                    logging.info("Total number of entries: %d" % total_entries)
                    if start is not None and total_entries < start:
                        start = total_entries - 1
            except HTTPErrorInvalidPage:
                logging.debug(
                    "Received HTTP 400 error which appears to be an invalid page error, probably reached the end."
                )
                break
            except HTTPError as e:
                if len(entries) == 0:
                    raise e

                logging.exception(
                    f"Error while fetching page {page}. Stopping at {len(entries)} entries."
                )
                break
            except Exception as e:
                logging.error(f"Error while fetching page {page}.")
                raise e

            try:
                json_content = get_content_as_json(req)
                if type(json_content) is list and len(json_content) > 0:
                    if (
                        start is None
                        or (
                            start is not None
                            and page > math.floor(start / per_page) + 1
                        )
                    ) and num is None:
                        entries += json_content
                        if start is not None:
                            entries_left -= len(json_content)
                    elif start is not None and page == math.floor(start / per_page) + 1:
                        first_idx = start % per_page
                        if num is None or (
                            num is not None and len(json_content[first_idx:]) < num
                        ):
                            entries += json_content[first_idx:]
                            if num is not None:
                                entries_left -= len(json_content[first_idx:])
                        else:
                            entries += json_content[first_idx : first_idx + num]
                            entries_left = 0
                    else:
                        if num is not None and entries_left > len(json_content):
                            entries += json_content
                            entries_left -= len(json_content)
                        else:
                            entries += json_content[:entries_left]
                            entries_left = 0

                    if display_progress:
                        if num is None and start is None and total_entries >= 0:
                            if pbar is None:
                                pbar = tqdm(total=total_pages)
                            pbar.update(page - pbar.n)

                        elif num is None and start is not None and total_entries >= 0:
                            if pbar is None:
                                pbar = tqdm(total=total_entries - start)
                            pbar.update(total_entries - start - entries_left - pbar.n)
                        elif num is not None and total_entries > 0:
                            if pbar is None:
                                pbar = tqdm(total=total_entries)
                            pbar.update(num - entries_left - pbar.n)
                else:
                    more_entries = False
            except JSONDecodeError:
                more_entries = False

            page += 1

        if pbar is not None:
            pbar.close()

        return (entries, total_entries)

    def crawl_single_page(self, url: str) -> Any:
        """Crawls a single URL.

        Args:
            url: the URL to crawl

        Raises:
            WordPressApiNotV2: The target does not support the WordPress API v2

        Returns:
            The content of the page
        """
        content = None
        rest_url = url_path_join(self.url, self.api_path, url)
        try:
            req = self.s.get(rest_url)
        except HTTPErrorInvalidPage:
            return None
        except HTTPError404:
            return None

        try:
            content = get_content_as_json(req)
        except JSONDecodeError:
            pass

        return content

    def get_comments(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all comments.

        Args:
            start: the start index
            num: the number of entries to retrieve

        Returns:
            The list of comments and total number of comments available
        """
        return self.crawl_pages("wp/v2/comments?page=%d", start, num)

    def get_posts(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all posts.

        Args:
            comments: whether to retrieve comments
            start: the start index
            num: the number of entries to retrieve

        Raises:
            WordPressApiNotV2: The target does not support the WordPress API v2

        Returns:
            The list of posts and total number of posts available
        """
        if self.has_v2 is None:
            self.get_basic_info()
        if not self.has_v2:
            raise WordPressApiNotV2

        return self.crawl_pages("wp/v2/posts?page=%d", start=start, num=num)

    def get_tags(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all tags.

        Args:
            start: the start index
            num: the number of entries to retrieve

        Returns:
            The list of tags and total number of tags available
        """
        return self.crawl_pages("wp/v2/tags?page=%d", start, num)

    def get_categories(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all categories.

        Args:
            start: the start index
            num: the number of entries to retrieve

        Returns:
            The list of categories and total number of categories available
        """
        return self.crawl_pages("wp/v2/categories?page=%d", start=start, num=num)

    def get_users(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all users.

        Args:
            start: the start index
            num: the number of entries to retrieve

        Returns:
            The list of users and total number of users available
        """
        return self.crawl_pages("wp/v2/users?page=%d", start=start, num=num)

    def get_media(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all media objects.

        Args:
            start: the start index
            num: the number of entries to retrieve

        Returns:
            The list of media objects
        """
        return self.crawl_pages("wp/v2/media?page=%d", start=start, num=num)

    def get_media_urls(
        self,
        ids: Union[Literal["all"], str],
        media_cache: Optional[list[WPObject]] = None,
    ) -> tuple[list[str], list[str]]:
        """Retrieves the media download URLs for specified IDs or all or from cache.

        Args:
            ids: the IDs of the media objects to retrieve, "all" for all, "cache" for cached, or a comma-separated list of IDs
            media_cache: a list of previously retrieved media to use

        Returns:
            A tuple containing the list of URLs and the list of slugs
        """
        media: list[WPObject] = []
        if ids == "all":
            if media_cache is None:
                media, _ = self.get_media()
            else:
                media = media_cache
        else:
            id_list = ids.split(",")
            media = []
            for i in id_list:
                try:
                    if int(i) > 0:
                        m = self.get_obj_by_id(
                            WPApi.MEDIA,
                            int(i),
                            media_cache,
                        )
                        if m is not None and len(m) > 0 and type(m[0]) is dict:
                            media.append(m[0])
                except ValueError:
                    pass
        urls = []
        slugs = []
        if media is None:
            return [], []
        for m_item in media:
            if (
                m_item is not None
                and type(m_item) is dict
                and "source_url" in m_item.keys()
                and "slug" in m_item.keys()
            ):
                urls.append(m_item["source_url"])
                slugs.append(m_item["slug"])
        return urls, slugs

    def get_pages(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> ObjectsAndTotal:
        """Retrieves all pages.

        Args:
            start: the start index
            num: the number of entries to retrieve
            force: ignore cache and force a re-fetch

        Returns:
            The list of pages
        """
        return self.crawl_pages("wp/v2/pages?page=%d", start=start, num=num)

    def get_namespaces(
        self,
        start: Optional[int] = None,
        num: Optional[int] = None,
    ) -> list[str]:
        """Retrieves an array of namespaces.

        Args:
            start: the start index
            num: the number of entries to retrieve
            force: ignore cache and force a re-fetch

        Returns:
            The list of namespaces
        """
        if self.has_v2 is None:
            self.get_basic_info()
        if self.basic_info is None:
            return []
        if "namespaces" in self.basic_info.keys():
            if start is None and num is None:
                return self.basic_info["namespaces"]  # type: ignore[no-any-return]
            namespaces = copy.deepcopy(self.basic_info["namespaces"])
            if start is not None and start < len(namespaces):
                namespaces = namespaces[start:]
            if num is not None and num <= len(namespaces):
                namespaces = namespaces[:num]
            return namespaces  # type: ignore[no-any-return]
        return []

    def get_routes(self) -> dict[str, Any]:
        """Retrieves a dictionary of routes.

        Returns:
            The dictionary of routes
        """
        if self.has_v2 is None:
            self.get_basic_info()
        if self.basic_info is None:
            return {}
        if "routes" in self.basic_info.keys():
            return self.basic_info["routes"]  # type: ignore[no-any-return]
        return {}

    def crawl_namespaces(self, ns: Union[Literal["all"], str]) -> dict[str, Any]:
        """Crawls all accessible get routes defined for the specified namespace.

        Args:
            ns: the namespace to crawl, or "all" for all namespaces

        Raises:
            NSNotFoundException: If a namespace was specified but not found

        Returns:
            A dictionary containing the data for the specified namespace
        """
        namespaces = self.get_namespaces()
        routes = self.get_routes()
        ns_data = {}
        if ns != "all" and ns not in namespaces:
            raise NSNotFoundException
        for url, route in routes.items():
            if "namespace" not in route.keys() or "endpoints" not in route.keys():
                continue
            url_as_ns = url.lstrip("/")
            if "(?P<" in url or url_as_ns in namespaces:
                continue
            if (ns != "all" and route["namespace"] != ns) or route["namespace"] in [
                "wp/v2",
                "",
            ]:
                continue
            for endpoint in route["endpoints"]:
                if "GET" not in endpoint["methods"]:
                    continue
                keep = True
                if len(endpoint["args"]) > 0 and type(endpoint["args"]) is dict:
                    for name, arg in endpoint["args"].items():  # noqa: B007
                        if arg["required"]:
                            keep = False
                if keep:
                    rest_url = url_path_join(self.url, self.api_path, url)
                    try:
                        ns_request = self.s.get(rest_url)
                        ns_data[url] = get_content_as_json(ns_request)
                    except Exception:
                        continue
        return ns_data

    def get_obj_by_id_helper(
        self, obj_id: int, url: str, cache: list[WPObject]
    ) -> list[WPObject]:
        """Retrieve an object from the cache or get it if not present.

        Args:
            cache: list of objects to use as cache
            obj_id: id of the object to fetch
            url: URL formatting template containing "%d" where the ID should be substituted
            use_cache: whether to use the cache or force a re-fetch

        Returns:
            A list containing the returned object, empty if not retrievable.
        """
        obj = get_by_id(cache, obj_id)
        if obj is not None:
            return [obj]

        obj = self.crawl_single_page(url % obj_id)
        if type(obj) is dict:
            return [obj]
        return []

    def get_obj_by_id(
        self, obj_type: int, obj_id: int, obj_cache: Optional[list[WPObject]]
    ) -> list[WPObject]:
        """Returns a list of maximum one object specified by its type and ID.

        Also returns an empty list if the ID does not exist.

        Args:
            obj_type: the type of the object (ex. POST)
            obj_id: the ID of the object to fetch
            obj_cache: a list of cached objects

        Returns:
            A list containing the returned object, empty if not retrievable.
        """
        obj_cache = [] if obj_cache is None else obj_cache

        if obj_type == WPApi.USER:
            return self.get_obj_by_id_helper(obj_id, "wp/v2/users/%d", obj_cache)
        if obj_type == WPApi.TAG:
            return self.get_obj_by_id_helper(obj_id, "wp/v2/tags/%d", obj_cache)
        if obj_type == WPApi.CATEGORY:
            return self.get_obj_by_id_helper(
                obj_id,
                "wp/v2/categories/%d",
                obj_cache,
            )
        if obj_type == WPApi.POST:
            return self.get_obj_by_id_helper(
                obj_id,
                "wp/v2/posts/%d",
                obj_cache,
            )
        if obj_type == WPApi.PAGE:
            return self.get_obj_by_id_helper(
                obj_id,
                "wp/v2/pages/%d",
                obj_cache,
            )
        if obj_type == WPApi.COMMENT:
            return self.get_obj_by_id_helper(
                obj_id,
                "wp/v2/comments/%d",
                obj_cache,
            )
        if obj_type == WPApi.MEDIA:
            return self.get_obj_by_id_helper(
                obj_id,
                "wp/v2/media/%d",
                obj_cache,
            )
        return []

    def get_obj_list(
        self,
        obj_type: int,
        start: Optional[int],
        limit: Optional[int],
    ) -> ObjectsAndTotal:
        """Returns a list of maximum limit objects specified by the starting object offset.

        Args:
            obj_type: the type of the object (ex. POST)
            start: the offset of the first object to return
            limit: the maximum number of objects to return


        Returns:
            A list of the returned objects
        """
        get_func = None
        if obj_type == WPApi.USER:
            get_func = self.get_users
        elif obj_type == WPApi.TAG:
            get_func = self.get_tags
        elif obj_type == WPApi.CATEGORY:
            get_func = self.get_categories
        elif obj_type == WPApi.PAGE:
            get_func = self.get_pages
        elif obj_type == WPApi.POST:
            get_func = self.get_posts
        elif obj_type == WPApi.COMMENT:
            get_func = self.get_comments
        elif obj_type == WPApi.MEDIA:
            get_func = self.get_media
        elif obj_type == WPApi.NAMESPACE:
            get_func = self.get_namespaces  # type: ignore[assignment]

        if get_func is not None:
            return get_func(start=start, num=limit)

        return [], None
