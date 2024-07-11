import copy
import logging
import math
from json.decoder import JSONDecodeError
from urllib.parse import urlencode

from tqdm.auto import tqdm

from wpextract.download.exceptions import (
    NoWordpressApi,
    NSNotFoundException,
    WordPressApiNotV2,
)
from wpextract.download.requestsession import (
    HTTPError404,
    HTTPErrorInvalidPage,
    RequestSession,
)
from wpextract.download.utils import (
    get_by_id,
    get_content_as_json,
    url_path_join,
)


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

    def __init__(self, target, api_path="wp-json/", session=None, search_terms=None):
        """Creates a new instance of WPApi.

        Args:
            target: the target of the scan
            api_path: the api path, if non-default
            session: the requests session object to use for HTTP requests
            search_terms : the terms of the keyword search, if any
        """
        self.api_path = api_path
        self.search_terms = search_terms
        self.has_v2 = None
        self.name = None
        self.description = None
        self.url = target
        self.basic_info = None
        self.posts = None
        self.tags = None
        self.categories = None
        self.users = None
        self.media = None
        self.pages = None
        self.s = None
        self.comments_loaded = False
        self.orphan_comments = []
        self.comments = None

        if session is not None:
            self.s = session
        else:
            self.s = RequestSession()

    def get_orphans_comments(self):
        """Returns the list of comments for which a post hasn't been found."""
        return self.orphan_comments

    def get_basic_info(self):
        """Collects and stores basic information about the target."""
        rest_url = url_path_join(self.url, self.api_path)
        if self.basic_info is not None:
            return self.basic_info

        try:
            req = self.s.get(rest_url)
        except Exception as e:
            raise NoWordpressApi from e
        if req.status_code >= 400:
            raise NoWordpressApi
        self.basic_info = get_content_as_json(req)

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
        self, url, start=None, num=None, search_terms=None, display_progress=True
    ):
        """Crawls all pages while there is at least one result for the given endpoint or tries to get pages from start to end."""
        if search_terms is None:
            search_terms = self.search_terms
        page = 1
        total_entries = 0
        total_pages = 0
        more_entries = True
        entries = []
        base_url = url
        entries_left = 1
        per_page = 10
        if search_terms is not None:
            if "?" in base_url:
                base_url += "&" + urlencode({"search": search_terms})
            else:
                base_url += "?" + urlencode({"search": search_terms})
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
                    or start is not None
                    and page == math.floor(start / per_page) + 1
                ) and "X-WP-Total" in req.headers:
                    total_entries = int(req.headers["X-WP-Total"])
                    total_pages = int(req.headers["X-WP-TotalPages"])
                    logging.info("Total number of entries: %d" % total_entries)
                    if start is not None and total_entries < start:
                        start = total_entries - 1
            except HTTPErrorInvalidPage:
                break
            except Exception as e:
                raise WordPressApiNotV2 from e

            try:
                json_content = get_content_as_json(req)
                if type(json_content) is list and len(json_content) > 0:
                    if (
                        start is None
                        or start is not None
                        and page > math.floor(start / per_page) + 1
                    ) and num is None:
                        entries += json_content
                        if start is not None:
                            entries_left -= len(json_content)
                    elif start is not None and page == math.floor(start / per_page) + 1:
                        if (
                            num is None
                            or num is not None
                            and len(json_content[start % per_page :]) < num
                        ):
                            entries += json_content[start % per_page :]
                            if num is not None:
                                entries_left -= len(json_content[start % per_page :])
                        else:
                            entries += json_content[
                                start % per_page : (start % per_page) + num
                            ]
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

    def crawl_single_page(self, url):
        """Crawls a single URL."""
        content = None
        rest_url = url_path_join(self.url, self.api_path, url)
        try:
            req = self.s.get(rest_url)
        except HTTPErrorInvalidPage:
            return None
        except HTTPError404:
            return None
        except Exception as e:
            raise WordPressApiNotV2 from e
        try:
            content = get_content_as_json(req)
        except JSONDecodeError:
            pass

        return content

    def get_from_cache(self, cache, start=None, num=None, force=False):
        """Tries to fetch data from the given cache, also verifies first if WP-JSON is supported."""
        if self.has_v2 is None:
            self.get_basic_info()
        if not self.has_v2:
            raise WordPressApiNotV2
        if cache is not None and start is not None and len(cache) <= start:
            start = len(cache) - 1
        if cache is not None and not force:
            if (
                start is not None
                and num is None
                and len(cache) > start
                and None not in cache[start:]
            ):
                # If start is specified and not num, we want to return the posts in cache only if they were already cached
                return cache[start:]
            elif (
                start is None
                and num is not None
                and len(cache) > num
                and None not in cache[:num]
            ):
                # If num is specified and not start, we want to do something similar to the above
                return cache[:num]
            elif (
                start is not None
                and num is not None
                and len(cache) > start + num
                and None not in cache[start:num]
            ):
                return cache[start : start + num]
            elif (
                start is None and (num is None or num > len(cache))
            ) and None not in cache:
                return cache

        return None

    def update_cache(self, cache, values, total_entries, start=None, num=None):
        """Push new values to the cache."""
        if cache is None:
            cache = values
        elif len(values) > 0:
            s = start
            if start is None:
                s = 0
            if start >= total_entries:
                s = total_entries - 1
            n = num
            if n is not None and s + n > total_entries:
                n = total_entries - s
            if num is None:
                n = total_entries
            if n > len(cache):
                cache += [None] * (n - len(cache))
            for el in values:
                cache[s] = el
                s += 1
                if s == n:
                    break
        if len(cache) != total_entries:
            if start is not None and start < total_entries:
                cache = [None] * start + cache
            if num is not None:
                cache += [None] * (total_entries - len(cache))
        return cache

    def get_comments(self, start=None, num=None, force=False):
        """Retrieves all comments."""
        comments = self.get_from_cache(self.comments, start, num, force)
        if comments is not None:
            return comments

        comments, total_entries = self.crawl_pages("wp/v2/comments?page=%d", start, num)
        self.comments = self.update_cache(
            self.comments, comments, total_entries, start, num
        )
        return comments

    def get_posts(self, comments=False, start=None, num=None, force=False):
        """Retrieves all posts or the specified ones."""
        if self.has_v2 is None:
            self.get_basic_info()
        if not self.has_v2:
            raise WordPressApiNotV2
        if self.posts is not None and start is not None and len(self.posts) < start:
            start = len(self.posts) - 1
        if (
            self.posts is not None
            and (self.comments_loaded and comments or not comments)
            and not force
        ):
            posts = self.get_from_cache(self.posts, start, num)
            if posts is not None:
                return posts
        posts, total_entries = self.crawl_pages(
            "wp/v2/posts?page=%d", start=start, num=num
        )

        self.posts = self.update_cache(self.posts, posts, total_entries, start, num)

        if not self.comments_loaded and comments:
            # Load comments
            comment_list = self.crawl_pages("wp/v2/comments?page=%d")[0]
            for comment in comment_list:
                found_post = False
                for i in range(0, len(self.posts)):
                    if self.posts[i]["id"] == comment["post"]:
                        if "comments" not in self.posts[i]:
                            self.posts[i]["comments"] = []
                        self.posts[i]["comments"].append(comment)
                        found_post = True
                        break
                if not found_post:
                    self.orphan_comments.append(comment)
            self.comments_loaded = True

        return_posts = self.posts
        if start is not None and start < len(return_posts):
            return_posts = return_posts[start:]
        if num is not None and num < len(return_posts):
            return_posts = return_posts[:num]
        return return_posts

    def get_tags(self, start=None, num=None, force=False):
        """Retrieves all tags."""
        tags = self.get_from_cache(self.tags, start, num, force)
        if tags is not None:
            return tags

        tags, total_entries = self.crawl_pages("wp/v2/tags?page=%d", start, num)
        self.tags = self.update_cache(self.tags, tags, total_entries, start, num)
        return tags

    def get_categories(self, start=None, num=None, force=False):
        """Retrieves all categories or the specified ones."""
        categories = self.get_from_cache(self.categories, start, num, force)
        if categories is not None:
            return categories

        categories, total_entries = self.crawl_pages(
            "wp/v2/categories?page=%d", start=start, num=num
        )
        self.categories = self.update_cache(
            self.categories, categories, total_entries, start, num
        )
        return categories

    def get_users(self, start=None, num=None, force=False):
        """Retrieves all users or the specified ones."""
        users = self.get_from_cache(self.users, start, num, force)
        if users is not None:
            return users

        users, total_entries = self.crawl_pages(
            "wp/v2/users?page=%d", start=start, num=num
        )
        self.users = self.update_cache(self.users, users, total_entries, start, num)
        return users

    def get_media(self, start=None, num=None, force=False):
        """Retrieves all media objects."""
        media = self.get_from_cache(self.media, start, num, force)
        if media is not None:
            return media

        media, total_entries = self.crawl_pages(
            "wp/v2/media?page=%d", start=start, num=num
        )
        self.media = self.update_cache(self.media, media, total_entries, start, num)
        return media

    def get_media_urls(self, ids, cache=True):
        """Retrieves the media download URLs for specified IDs or all or from cache."""
        media = []
        if ids == "all":
            media = self.get_media(force=(not cache))
        elif ids == "cache":
            media = self.get_from_cache(self.media, force=(not cache))
        else:
            id_list = ids.split(",")
            media = []
            for i in id_list:
                try:
                    if int(i) > 0:
                        m = self.get_obj_by_id(WPApi.MEDIA, int(i), cache)
                        if m is not None and len(m) > 0 and type(m[0]) is dict:
                            media.append(m[0])
                except ValueError:
                    pass
        urls = []
        slugs = []
        if media is None:
            return []
        for m in media:
            if (
                m is not None
                and type(m) is dict
                and "source_url" in m.keys()
                and "slug" in m.keys()
            ):
                urls.append(m["source_url"])
                slugs.append(m["slug"])
        return urls, slugs

    def get_pages(self, start=None, num=None, force=False):
        """Retrieves all pages."""
        pages = self.get_from_cache(self.pages, start, num, force)
        if pages is not None:
            return pages

        pages, total_entries = self.crawl_pages(
            "wp/v2/pages?page=%d", start=start, num=num
        )
        self.pages = self.update_cache(self.pages, pages, total_entries, start, num)
        return pages

    def get_namespaces(self, start=None, num=None, force=False):
        """Retrieves an array of namespaces."""
        if self.has_v2 is None or force:
            self.get_basic_info()
        if "namespaces" in self.basic_info.keys():
            if start is None and num is None:
                return self.basic_info["namespaces"]
            namespaces = copy.deepcopy(self.basic_info["namespaces"])
            if start is not None and start < len(namespaces):
                namespaces = namespaces[start:]
            if num <= len(namespaces):
                namespaces = namespaces[:num]
            return namespaces
        return []

    def get_routes(self):
        """Retrieves an array of routes."""
        if self.has_v2 is None:
            self.get_basic_info()
        if "routes" in self.basic_info.keys():
            return self.basic_info["routes"]
        return []

    def crawl_namespaces(self, ns):
        """Crawls all accessible get routes defined for the specified namespace."""
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
            if (
                ns != "all"
                and route["namespace"] != ns
                or route["namespace"] in ["wp/v2", ""]
            ):
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

    def get_obj_by_id_helper(self, cache, obj_id, url, use_cache=True) -> list[dict]:
        """Retrieve an object from the cache or get it if not present.

        Args:
            cache: cache object for this type
            obj_id: id of the object to fetch
            url: URL formatting template containing "%d" where the ID should be substituted
            use_cache: whether to use the cache or force a re-fetch

        Returns:
            A list containing the returned object, empty if not retrievable.
        """
        if use_cache and cache is not None:
            obj = get_by_id(cache, obj_id)
            if obj is not None:
                return [obj]
        obj = self.crawl_single_page(url % obj_id)
        if type(obj) is dict:
            return [obj]
        return []

    def get_obj_by_id(self, obj_type, obj_id, use_cache=True):
        """Returns a list of maximum one object specified by its type and ID.

        Also returns an empty list if the ID does not exist.

        Args:
            obj_type: the type of the object (ex. POST)
            obj_id: the ID of the object to fetch
            use_cache: if the cache should be used to avoid useless
                requests
        """
        if obj_type == WPApi.USER:
            return self.get_obj_by_id_helper(
                self.users, obj_id, "wp/v2/users/%d", use_cache
            )
        if obj_type == WPApi.TAG:
            return self.get_obj_by_id_helper(
                self.tags, obj_id, "wp/v2/tags/%d", use_cache
            )
        if obj_type == WPApi.CATEGORY:
            return self.get_obj_by_id_helper(
                self.categories, obj_id, "wp/v2/categories/%d", use_cache
            )
        if obj_type == WPApi.POST:
            return self.get_obj_by_id_helper(
                self.posts, obj_id, "wp/v2/posts/%d", use_cache
            )
        if obj_type == WPApi.PAGE:
            return self.get_obj_by_id_helper(
                self.pages, obj_id, "wp/v2/pages/%d", use_cache
            )
        if obj_type == WPApi.COMMENT:
            return self.get_obj_by_id_helper(
                self.comments, obj_id, "wp/v2/comments/%d", use_cache
            )
        if obj_type == WPApi.MEDIA:
            return self.get_obj_by_id_helper(
                self.comments, obj_id, "wp/v2/media/%d", use_cache
            )
        return []

    def get_obj_list(self, obj_type, start, limit, cache, kwargs=None):
        """Returns a list of maximum limit objects specified by the starting object offset.

        Args:
            obj_type: the type of the object (ex. POST)
            start: the offset of the first object to return
            limit: the maximum number of objects to return
            cache: if the cache should be used to avoid useless requests
            kwargs: additional parameters to pass to the function (for
                POST only)
        """
        kwargs = kwargs or {}

        get_func = None
        if obj_type == WPApi.USER:
            get_func = self.get_users
        elif obj_type == WPApi.TAG:
            get_func = self.get_tags
        elif obj_type == WPApi.CATEGORY:
            get_func = self.get_categories
        elif obj_type == WPApi.PAGE:
            get_func = self.get_pages
        elif obj_type == WPApi.COMMENT:
            get_func = self.get_comments
        elif obj_type == WPApi.MEDIA:
            get_func = self.get_media
        elif obj_type == WPApi.NAMESPACE:
            get_func = self.get_namespaces

        if get_func is not None:
            return get_func(start=start, num=limit, force=not cache)
        elif obj_type == WPApi.POST:
            return self.get_posts(start=start, num=limit, force=not cache, **kwargs)
        return []

    def search(self, obj_types, keywords, start, limit):
        """Looks for data with the specified keywords of the given types.

        Args:
            obj_types: a list of the desired object types to look for
            keywords: the keywords to look for
            start: a start index
            limit: the max number to return

        Returns:
            a dict of lists of objects sorted by types
        """
        out = {}
        if WPApi.ALL_TYPES in obj_types or len(obj_types) == 0:
            obj_types = [
                WPApi.POST,
                WPApi.CATEGORY,
                WPApi.TAG,
                WPApi.PAGE,
                WPApi.COMMENT,
                WPApi.MEDIA,
                WPApi.USER,
            ]  # All supported types for search
        for t in obj_types:
            if t == WPApi.POST:
                out[t] = self.crawl_pages(
                    "wp/v2/posts?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.CATEGORY:
                out[t] = self.crawl_pages(
                    "wp/v2/categories?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.TAG:
                out[t] = self.crawl_pages(
                    "wp/v2/tags?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.PAGE:
                out[t] = self.crawl_pages(
                    "wp/v2/pages?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.COMMENT:
                out[t] = self.crawl_pages(
                    "wp/v2/comments?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.MEDIA:
                out[t] = self.crawl_pages(
                    "wp/v2/media?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
            elif t == WPApi.USER:
                out[t] = self.crawl_pages(
                    "wp/v2/users?page=%d",
                    start=start,
                    num=limit,
                    search_terms=keywords,
                    display_progress=False,
                )[0]
        return out
