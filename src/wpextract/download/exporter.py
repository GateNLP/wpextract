import copy
import html
import json
from pathlib import Path
from urllib import parse as urlparse

from tqdm.auto import tqdm

from wpextract.download.requestsession import RequestSession


class Exporter:
    """Utility functions to export data."""

    CHUNK_SIZE = 2048
    """The size of chunks to download large files"""

    @staticmethod
    def download_media(
        session: RequestSession, media: list[str], out_path: Path
    ) -> int:
        """Downloads the media files based on the given URLs.

        Args:
            session: the request session to use
            media: the URLs as a list
            out_path: the path to the folder where the files are being saved, it is assumed as existing

        Returns:
            the number of files written
        """
        files_number = 0
        for m in tqdm(media, unit="media"):
            r = session.do_request("get", m, stream=True)
            if r.status_code == 200:
                http_path = urlparse.urlparse(m).path.split("/")
                local_path = out_path
                if len(http_path) > 1:
                    for el in http_path[:-1]:
                        local_path = local_path / el
                        local_path.mkdir(exist_ok=True)
                local_path = local_path / http_path[-1]
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
    def write_file(filename, data):
        """Writes content to the given file in JSON format.

        The key mapping must be a dict of keys or lists of keys to ensure proper mapping.

        Args:
            filename: the path of the file
            data: the actual data to export
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def export_posts(
        posts: list[dict],
        filename: str,
    ):
        """Exports posts to the specified file.

        Args:
            posts: the posts to export
            filename: filename to use

        Returns:
            the length of the list written to the file
        """
        exported_posts = Exporter.setup_export(
            posts,
            [["title", "rendered"], ["content", "rendered"], ["excerpt", "rendered"]],
        )

        Exporter.write_file(filename, exported_posts)
        return len(exported_posts)

    @staticmethod
    def export_categories(categories, filename):
        """Exports categories to the specified file.

        Args:
            categories: the categories to export
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        exported_categories = Exporter.setup_export(
            categories,  # TODO
            [],
        )

        Exporter.write_file(filename, exported_categories)
        return len(exported_categories)

    @staticmethod
    def export_tags(tags, filename):
        """Exports tags to the specified file.

        Args:
            tags: the tags to export
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        exported_tags = tags  # It seems that no modification will be done for this one, so no deepcopy
        Exporter.write_file(filename, exported_tags)
        return len(exported_tags)

    @staticmethod
    def export_users(users, filename):
        """Exports users to the specified file.

        Args:
            users: the users to export
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        exported_users = users  # It seems that no modification will be done for this one, so no deepcopy
        Exporter.write_file(filename, exported_users)
        return len(exported_users)

    @staticmethod
    def export_pages(pages, filename):
        """Exports pages to the specified file.

        Args:
            pages: the pages to export
            filename: the path to the file to write

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

        Exporter.write_file(filename, exported_pages)
        return len(exported_pages)

    @staticmethod
    def export_media(media, filename):
        """Exports media to the specified file.

        Args:
            media: the media to export
            filename: file to export to

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

        Exporter.write_file(filename, exported_media)
        return len(exported_media)

    # FIXME to be refactored
    @staticmethod
    def export_comments_interactive(comments, filename):
        """Exports comments to the specified file.

        Args:
            comments: the comments to export
            filename: the path to the file to write

        Returns:
            the length of the list written to the file
        """
        exported_comments = Exporter.setup_export(
            comments,
            [["content", "rendered"]],
        )

        Exporter.write_file(filename, exported_comments)
        return len(exported_comments)
