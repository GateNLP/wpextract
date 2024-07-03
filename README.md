# WordPress Site Extractor

Processes an API dump of a WordPress site into a dataset, including identifying parallel multilingual articles, and resolving internal links and media.

> [!NOTE]  
> This software was developed for our EMNLP 2023 paper [_Analysing State-Backed Propaganda Websites: a New Dataset and Linguistic Study_](https://aclanthology.org/2023.emnlp-main.349/). The code has been updated since the paper was written; for archival purposes, the precise version used for the study is [available on Zenodo](https://zenodo.org/records/10008086).

## Referencing

We'd love to hear about your use of our tool, you can [email us](mailto:frheppell1@sheffield.ac.uk) to let us know! Feel free to create issues and/or pull requests for new features or bugs.

If you use this tool in published work, please cite [our EMNLP paper](https://aclanthology.org/2023.emnlp-main.349/):


<details>
   <summary>BibTeX Citation</summary>
   
```bibtex
@inproceedings{heppell-etal-2023-analysing,
    title = "Analysing State-Backed Propaganda Websites: a New Dataset and Linguistic Study",
    author = "Heppell, Freddy  and
      Bontcheva, Kalina  and
      Scarton, Carolina",
    editor = "Bouamor, Houda  and
      Pino, Juan  and
      Bali, Kalika",
    booktitle = "Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing",
    month = dec,
    year = "2023",
    address = "Singapore",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.emnlp-main.349",
    pages = "5729--5741",
    doi = "10.18653/v1/2023.emnlp-main.349"
}
```
</details>


## Installing

WordPress Site Extractor is currently not available from PyPI, but can instead be installed from a prebuilt wheel.

1. Go to the [latest release](https://github.com/GateNLP/wordpress-site-extractor/releases/latest) and download the `.whl` file
2. Create a new Python 3.9 or greater virtual environment
3. Install the package with `pip install /path/to/wp_site_extractor-x.y.z-py3-none-any.whl`
4. Run with the `wpextract` command
   
### Installing Development Environment

**Prerequisites**:

- Python 3.9 or greater
- [Poetry](https://python-poetry.org/)

1. Clone the repository
2. Run `poetry install`
   - You may need to first run `poetry env use /path/to/python` if Python 3.8 is not on your path
3. Run the CLI with `poetry run wpextract`

## Input Format

This tool takes a dump of the API JSON and (optionally) HTML pages of the site.

### API Dump

The dump should be in a 'merged pages' format, i.e. the pages of the list endpoint should be iterated and each page merged together into one list. This can be done by a tool such as [WPJSONScraper](https://github.com/freddyheppell/wp-json-scraper).

The following files should be placed in a directory. Their names may be prefixed by a consistent string (e.g. to record the date).

| File Name         | Endpoint                               |
|-------------------|----------------------------------------|
| `categories.json` | [`/wp/v2/categories`][categories_path] |
| `comments.json`   | [`/wp/v2/comments`][comments_path]     |
| `media.json`      | [`/wp/v2/media`][media_path]           |
| `pages.json`      | [`/wp/v2/pages`][pages_path]           |
| `posts.json`      | [`/wp/v2/posts`][posts_path]           |
| `tags.json`       | [`/wp/v2/tags`][tags_path]             |
| `users.json`      | [`/wp/v2/users`][users_path]           |

[categories_path]: https://developer.wordpress.org/rest-api/reference/categories/#list-categories
[comments_path]: https://developer.wordpress.org/rest-api/reference/comments/#list-comments
[media_path]: https://developer.wordpress.org/rest-api/reference/media/#list-media
[pages_path]: https://developer.wordpress.org/rest-api/reference/pages/#list-pages
[posts_path]: https://developer.wordpress.org/rest-api/reference/posts/#list-posts
[tags_path]: https://developer.wordpress.org/rest-api/reference/tags/#list-tags
[users_path]: https://developer.wordpress.org/rest-api/reference/users/#list-users

### HTML Scrape

This should be a scrape of the site's posts (at least), which will be used to extract data which is not present in the API response.

Currently, this is only used to extract translations of posts. If the site you are scraping does not have translations, the scrape is not required and an empty directory can be used.

An example of an easy way to do this (given the `posts.json` file described above) is

```shell
cat posts.json | jq -r '.[] | .link' > url_list.txt
touch rejected.log
wget --adjust-extension --input-file=url_list.txt --random-wait --force-directories --rejected-log=failed.log
```

You could also use a tool such as [Ultimate Sitemap Parser](https://github.com/mediacloud/ultimate-sitemap-parser) to generate a list of URLs from the sitemap and then use `wget`.

```python
from usp.tree import sitemap_tree_for_homepage
tree = sitemap_tree_for_homepage('https://example.org')
urls = set([page.url for page in tree.all_pages()])
with open('url_list.txt') as f:
    f.write('\n'.join(list(urls)))
```

Finally, you could run a standard recursive `wget` scrape, although this is less certain to get all the content needed.

## Running the tool

To run the tool, use the `main.py` script:

```shell
wpextract path_to_json/ path_to_scrape/ path_to_out/
```

### JSON Prefixes

If the JSON files have a name prefix (e.g. `20221209-exampleorg-posts.json`, use the `--json-prefix` argument:

```shell
wpextract path_to_json/ path_to_scrape/ path_to_out/ --json-prefix 202212-09-exampleorg-
```

This prefix will also be added to the output files.

### Logging

Basic progress logging and tqdm progress bars are shown in stdout and stderr respectively.

- To display more logs, including non-critical failures (e.g. unable to extract translations for a page) use the `--verbose`/`-v` argument
- To write logs to a file instead of stdout, use the `--log LOG_FILE`/`-l LOG_FILE` argument. Progress bars will still be sent to stderr.

## Using as a library

The extractor can also be used as a library instead of on the command line.

Typically, you would instantiate a new [`WPExtractor`](src/extractor/extract.py) instance and call its `extract` method. The dataframes can then be accessed as class attributes or exported with the `export` method.

An example usage is available in the CLI script ([`extractor.cli`](src/extractor/cli/cli.py)).

When using this approach, it's possible to use customised translation pickers (see the `translation_pickers` argument of `WPExtractor`). These should be child classes of [`extractor.parse.translations.LangPicker`](src/extractor/parse/translations/_pickers.py).

## Extraction Overview

This section contains an overview of the extraction process for data.

### 1. Scrape Crawling

Website scraping tools may store a webpage at a path that is not easy to derive from the URL (e.g. because of path length limits). For this reason, we crawl the scrape directory and build a mapping of URL to path.

For every html file at any depth in the scrape directory, we:
1. Perform a limited parse of only the link and meta tags in the file's head.
2. Attempt to extract a valid URL from a `link` tag with `rel="alternate"` or `canonical` meta tag
3. Check the URL has not previously been seen, warn and skip if it has
4. Add the URL to the map with the absolute path of the file

This map is then saved as `url_cache.json` in the scrape directory. If an existing cache file is detected, it will be used instead of scraping again, unless a breaking change has been made to the file schema.

### 2. Content Extraction

Each type of content (posts, pages, media etc) is now extracted in turn.

The extraction process is applied to all posts simultaneously in the following order:
1. Extract raw text from the HTML-formatted title and excerpt.
2. Parse the HTML content from the API response input.
3. Parse the HTML content from the scrape file, if it was found for the link during the crawl
4. Extract the post's language and translations from the scrape file
   * Translations are detected using the translation pickers in the [`extractor.parse.translations`](src/extractor/parse/translations) module.
   * Custom pickers can be added by [using this tool as a library](#using-as-a-library)
   * Any extracted translations are stored as unresolved links
5. Add the post's link to the link registry
6. Using the parsed API content response, extract:
   * Internal links (stored as unresolved links)
   * External links (stored as resolved links)
   * Embeds (`iframe` tags)
   * Images (stored as unresolved media if internal, resolved media if external), including their source URL, alt text and caption (if they are in a `figure`)
   * Raw text content, via the following process:
     1. Remove tags which contain unwanted text (e.g. `figcaptions`)
     2. Replace `<br>` tags and `<p>` tags with newline characters
     3. Combine all page text

Other types are extracted in similar ways. Any additional user-supplied fields with HTML formatting (such as media captions) are also extracted as plain text.

### 4. Translation Normalisation and Link Resolution

Translations are normalised by checking that for every translation relation (e.g. `en` -> `fr`), the reverse exists. If not, it will be added.


After all types have been processed, the link registry is used to process the unresolved links, translations and media.

For every resolution, the following steps are performed:
1. Remove the `preview_id` query parameter from the URL if present
2. Attempt to look up the URL in the link registry
3. If unsuccessful, use a heuristic to detect category slugs in the URL and try without them
   * We do this in case sites have removed category slugs from the permalink at some point.
4. If unsuccessful, warn that the URL is unresolvable

For each resolved link, translation, or media, a destination is set containing its normalised URL, data type, and ID.

### 5. Export

The columns of each type are subset and exported as a JSON file each.

## Acknowledgements and License

This software is made available under the terms of the [Apache License version 2.0](LICENSE).

A portion of this software (contained within the `extractor.dl` module) is adapted from [WPJsonScraper](https://github.com/MickaelWalter/wp-json-scraper) by Mickael Walter, made available under the terms of the [MIT license](src/extractor/dl/LICENSE.txt).