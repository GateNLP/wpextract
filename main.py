from pathlib import Path

from tqdm.auto import tqdm

from extractor.links import LinkRegistry
from extractor.posts import load_posts

tqdm.pandas()

links = LinkRegistry()
load_posts(
    Path("json/20221125-waronfakes/20221125-waronfakes-posts.json"),
    links,
    Path("web/20221125-waronfakes"),
)

print(links.links)
