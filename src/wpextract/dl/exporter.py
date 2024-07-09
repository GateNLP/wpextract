"""Copyright (c) 2018-2020 Mickaël "Kilawyn" Walter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import copy
import html
import json
import logging
import os
from urllib import parse as urlparse

from tqdm.auto import tqdm

from wpextract.dl.requestsession import RequestSession


class Exporter:
    """Utility functions to export data"""

    JSON = 1
    """Represents the JSON format for format choice"""
    CHUNK_SIZE = 2048
    """The size of chunks to download large files"""

    @staticmethod
    def download_media(session: RequestSession, media, output_folder):
        """Downloads the media files based on the given URLs

        Args:
            session: the request session to use
            media: the URLs as a list
            output_folder: the path to the folder where the files are
                being saved, it is assumed as existing

        Returns:
            the number of files wrote
        """
        files_number = 0
        for m in tqdm(media, unit="media"):
            # TODO: make this use the same session as the initial download
            r = session.do_request("get", m, stream=True)
            if r.status_code == 200:
                http_path = urlparse.urlparse(m).path.split("/")
                local_path = output_folder
                if len(http_path) > 1:
                    for el in http_path[:-1]:
                        local_path = os.path.join(local_path, el)
                        if not os.path.isdir(local_path):
                            os.mkdir(local_path)
                local_path = os.path.join(local_path, http_path[-1])
                with open(local_path, "wb") as f:
                    i = 0
                    content_size = int(r.headers.get("Content-Length", -1))
                    chunks_pbar = None
                    if content_size > 0:
                        chunks_pbar = tqdm(
                            total=content_size,
                            unit="B",
                            unit_scale=True,
                            desc=http_path[-1],
                            leave=False,
                        )
                    for chunk in r.iter_content(Exporter.CHUNK_SIZE):
                        if chunks_pbar is not None:
                            chunks_pbar.update(Exporter.CHUNK_SIZE)
                        f.write(chunk)
                        i += 1
                    if chunks_pbar is not None:
                        chunks_pbar.update(content_size - chunks_pbar.n)
                        chunks_pbar.close()
                files_number += 1
        return files_number

    @staticmethod
    def setup_export(vlist, parameters_to_unescape):
        """Sets up the right values for a list export.

        This function flattens alist of objects before its serialization in the expected format.
        It also makes a deepcopy to ensure that the original vlist is not altered.

        Args:
            vlist: the list to prepare for exporting
            parameters_to_unescape: parameters to unescape (ex.
                ["param1", ["param2"]["rendered"]])
        """
        exported_list = []

        for el in vlist:
            if el is not None:
                # First copy the object
                exported_el = copy.deepcopy(el)
                # Look for parameters to HTML unescape
                for key in parameters_to_unescape:
                    if type(key) is str:  # If the parameter is at the root
                        exported_el[key] = html.unescape(exported_el[key])
                    elif type(key) is list:  # If the parameter is nested
                        selected = exported_el
                        siblings = []
                        fullpath = {}
                        # We look for the leaf first, not forgetting sibling branches for rebuilding the tree later
                        for k in key:
                            if type(selected) is dict and k in selected.keys():
                                sib = {}
                                for e in selected.keys():
                                    if e != k:
                                        sib[e] = selected[e]
                                selected = selected[k]
                                siblings.append(sib)
                            else:
                                selected = None
                                break
                        # If we can unescape the parameter, we do it and rebuild the tree starting from the leaf
                        if selected is not None and type(selected) is str:
                            selected = html.unescape(selected)
                            key.reverse()
                            fullpath[key[0]] = selected
                            s = len(siblings) - 1
                            for e in siblings[s].keys():
                                fullpath[e] = siblings[s][e]
                            for k in key[1:]:
                                fullpath = {k: fullpath}
                                s -= 1
                                for e in siblings[s].keys():
                                    fullpath[e] = siblings[s][e]
                            key.reverse()
                            exported_el[key[0]] = fullpath[key[0]]
                # The resulting element is appended to the list of exported elements
                exported_list.append(exported_el)

        return exported_list

    @staticmethod
    def prepare_filename(filename, fmt):
        """Returns a filename with the proper extension according to the given format

        Args:
            filename: the filename to clean
            fmt: the file format

        Returns:
            the cleaned filename
        """
        if filename[-5:] != ".json" and fmt == Exporter.JSON:
            filename += ".json"
        return filename

    @staticmethod
    def write_file(filename, fmt, data):
        """Writes content to the given file using the given format.

        The key mapping must be a dict of keys or lists of keys to ensure proper mapping.

        Args:
            filename: the path of the file
            fmt: the format of the file
            data: the actual data to export
        """
        with open(filename, "w", encoding="utf-8") as f:
            if fmt == Exporter.JSON:
                # The JSON format is straightforward, we dump the flattened objects to JSON
                json.dump(data, f, ensure_ascii=False, indent=4)
            else:
                raise ValueError("Unknown export format")

    @staticmethod
    def export_posts(
        posts,
        fmt,
        filename,
    ):
        """Exports posts in specified format to specified file

        Args:
            posts: the posts to export
            fmt: the export format (JSON or CSV)
            filename: filename to use

        Returns:
            the length of the list written to the file
        """
        exported_posts = Exporter.setup_export(
            posts,
            [["title", "rendered"], ["content", "rendered"], ["excerpt", "rendered"]],
        )

        filename = Exporter.prepare_filename(filename, fmt)
        Exporter.write_file(filename, fmt, exported_posts)
        return len(exported_posts)

    @staticmethod
    def export_categories(categories, fmt, filename):
        """Exports categories in specified format to specified file.

        Args:
            categories: the categories to export
            fmt: the export format (JSON or CSV)
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        exported_categories = Exporter.setup_export(
            categories,  # TODO
            [],
        )

        filename = Exporter.prepare_filename(filename, fmt)
        Exporter.write_file(filename, fmt, exported_categories)
        return len(exported_categories)

    @staticmethod
    def export_tags(tags, fmt, filename):
        """Exports tags in specified format to specified file

        Args:
            tags: the tags to export
            fmt: the export format (JSON or CSV)
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        filename = Exporter.prepare_filename(filename, fmt)

        exported_tags = tags  # It seems that no modification will be done for this one, so no deepcopy
        Exporter.write_file(filename, fmt, exported_tags)
        return len(exported_tags)

    @staticmethod
    def export_users(users, fmt, filename):
        """Exports users in specified format to specified file.

        Args:
            users: the users to export
            fmt: the export format (JSON or CSV)
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        filename = Exporter.prepare_filename(filename, fmt)

        exported_users = users  # It seems that no modification will be done for this one, so no deepcopy
        Exporter.write_file(filename, fmt, exported_users)
        return len(exported_users)

    @staticmethod
    def export_pages(pages, fmt, filename, parent_pages=None, users=None):
        """Exports pages in specified format to specified file.

        Args:
            pages: the pages to export
            fmt: the export format (JSON or CSV)
            filename: the path to the file to write
            parent_pages: the list of all cached pages, to get parents
            users: the list of all cached users, to get users

        Returns:
            the length of the list written to the file
        """
        exported_pages = Exporter.setup_export(
            pages,
            [
                ["guid", "rendered"],
                ["title", "rendered"],
                ["content", "rendered"],
                ["excerpt", "rendered"],
            ],
        )

        filename = Exporter.prepare_filename(filename, fmt)
        Exporter.write_file(filename, fmt, exported_pages)
        return len(exported_pages)

    @staticmethod
    def export_media(media, fmt, filename, users=None):
        """Exports media in specified format to specified file.

        Args:
            media: the media to export
            fmt: the export format (JSON or CSV)
            filename: file to export to
            users: a list of users to associate them with author ids

        Returns:
            the length of the list written to the file
        """
        exported_media = Exporter.setup_export(
            media,
            [
                ["guid", "rendered"],
                ["title", "rendered"],
                ["description", "rendered"],
                ["caption", "rendered"],
            ],
        )

        filename = Exporter.prepare_filename(filename, fmt)
        Exporter.write_file(filename, fmt, exported_media)
        return len(exported_media)

    @staticmethod
    def export_namespaces(namespaces, fmt, filename):
        """**NOT IMPLEMENTED** Exports namespaces in specified format to specified file.

        Args:
            namespaces: the namespaces to export
            fmt: the export format (JSON or CSV)
            filename: file to export to

        Returns:
            the length of the list written to the file
        """
        logging.info("Namespaces export not available yet")
        return 0

    # FIXME to be refactored
    @staticmethod
    def export_comments_interactive(
        comments, fmt, filename, parent_posts=None, users=None
    ):
        """Exports comments in specified format to specified file.

        Args:
            comments: the comments to export
            fmt: the export format (JSON or CSV)
            filename: the path to the file to write
            parent_posts: the list of all cached posts, to get parent
                posts (not used yet because this could be too verbose)
            users: the list of all cached users, to get users

        Returns:
            the length of the list written to the file
        """
        exported_comments = Exporter.setup_export(
            comments,
            [["content", "rendered"]],
        )

        filename = Exporter.prepare_filename(filename, fmt)
        Exporter.write_file(filename, fmt, exported_comments)
        return len(exported_comments)
