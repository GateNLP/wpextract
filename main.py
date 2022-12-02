import argparse

from tqdm.auto import tqdm

from extractor.util.args import directory, empty_directory

tqdm.pandas()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="wordpress-site-extractor",
        description="Extracts posts from wordpress dump",
    )

    parser.add_argument("json_root", help="JSON dump of the site", type=directory)
    parser.add_argument("scrape_dir", help="HTML scrape of the site", type=directory)
    parser.add_argument("out_dir", help="Output directory", type=empty_directory)

    args = parser.parse_args()

    print(args)
