# WordPress Site Extractor

Processes a scraped WordPress site, including text extraction and internal link resolution

## Installing

1. Download and extract the project
2. Create a virtual environment (with `venv`, `Pipenv` or a similar tool)
3. Run `python setup.py` to install the package and dependencies
4. Check it has installed with `wpextract --help`

### Installing Development Environment

**Prerequisites**:

- Python 3.8
- Pipenv

1. Clone the repository
2. Run `pipenv install --dev`
   - You may need to add the argument `--python path/to/bin/python` if Python 3.8 is not on your path
3. Run the CLI with the `wpextract-dev` helper

## Input Format

This tool takes a scrape of the API JSON and HTML pages of the site.

### API Scrape

The scrape should be in a 'merged pages' format, i.e. the pages of the list endpoint should be iterated and each page merged together into one list. This can be done by a tool such as [WPJSONScraper](https://github.com/freddyheppell/wp-json-scraper).

The following files should be placed in a directory. They names may be prefixed by a consistent string (e.g. to record the date).

| File Name         | Endpoint                               |
| ----------------- | -------------------------------------- |
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

Currently, this is limited to translations of posts. If the site you are scraping does not have translations, the scrape is not required and an empty directory can be used.

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

An example usage is available in the CLI script ([`extractor.cli`](src/extractor/cli.py))
