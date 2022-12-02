import argparse

from tqdm.auto import tqdm

from extractor.extract import WPExtractor
from extractor.util.args import directory, empty_directory

tqdm.pandas()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="wordpress-site-extractor",
        description="Extracts posts from wordpress dump",
    )

    parser.add_argument("json_root", help="JSON dump of the site", type=directory)
    parser.add_argument("scrape_root", help="HTML scrape of the site", type=directory)
    parser.add_argument("out_dir", help="Output directory", type=empty_directory)
    parser.add_argument(
        "--json_prefix",
        "-P",
        help="Prefix to the JSON files",
        type=str,
        required=False,
        default=None,
    )

    args = parser.parse_args()

    extractor = WPExtractor(
        json_root=args.json_root,
        scrape_root=args.scrape_root,
        json_prefix=args.json_prefix,
    )

    extractor.extract()
    extractor.export(args.out_dir)
