from pathlib import Path

from tqdm.auto import tqdm

from extractor.links import LinkRegistry
from extractor.posts import load_posts

tqdm.pandas()

links = LinkRegistry()
df = load_posts(
    Path("test_site/json/20221125-waronfakes/20221125-waronfakes-posts.json"),
    links,
    Path("test_site/web/20221125-waronfakes"),
)
