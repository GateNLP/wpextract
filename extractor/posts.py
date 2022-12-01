from pathlib import Path

import pandas as pd

from extractor.links import LinkRegistry
from extractor.parse.content import extract_content_data
from extractor.parse.translations import extract_translations
from extractor.scrape import load_scrape
from extractor.util.file import load_df
from extractor.util.html import extract_html_text, parse_html
from extractor.util.locale import extract_locale


def load_posts(path: Path, link_registry: LinkRegistry, scrape_root: Path) -> None:
    """Load the posts from a JSON file.

    The JSON file is expected to be in the response format of the WordPress posts API.

    Args:
        path: The path to the JSON file on disk
        link_registry: The Link Registry to populate
        scrape_root: The root directory of the site scrape
    """
    posts_df = load_df(path)

    # Convert times
    posts_df["date_gmt"] = pd.to_datetime(posts_df["date_gmt"])
    posts_df["modified_gmt"] = pd.to_datetime(posts_df["modified_gmt"])
    posts_df = posts_df.drop(["date", "modified"], axis=1)

    # yoast_head_json.og_image is a list containing 0 or 1 image dictionaries
    # Get the "url" property if there is an image
    posts_df["og_image_url"] = posts_df["yoast_head_json.og_image"].apply(
        lambda image: image[0]["url"] if len(image) > 0 else None
    )

    posts_df["link_locale"] = posts_df["link"].apply(extract_locale)

    posts_df["title.text"] = posts_df["title.rendered"].apply(extract_html_text)
    posts_df["excerpt.text"] = posts_df["excerpt.rendered"].apply(extract_html_text)

    posts_df["content.bs"] = posts_df["content.rendered"].progress_apply(parse_html)

    posts_df["scrape_bs"] = posts_df["link"].progress_apply(
        lambda link: load_scrape(scrape_root, link)
    )
    posts_df[["language", "translations"]] = posts_df["scrape_bs"].apply(
        extract_translations
    )

    link_registry.add_linkables(
        "post", posts_df["link"].to_list(), posts_df.index.to_list()
    )

    posts_df[
        ["content.text", "links.internal", "links.external", "embeds", "images"]
    ] = posts_df.progress_apply(
        lambda r: extract_content_data(r["content.bs"], r["link"]), axis=1
    )

    posts_df.to_csv("test_out.csv")
