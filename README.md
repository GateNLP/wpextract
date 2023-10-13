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

The following files should be placed in a directory. Their names may be prefixed by a consistent string (e.g. to record the date).

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

An example usage is available in the CLI script ([`extractor.cli`](src/extractor/cli.py)).

When using this approach, it's possible to use customised translation pickers (see the `translation_pickers` argument of `WPExtractor`). These should be child classes of [`extractor.parse.translations.LangPicker`](src/extractor/parse/translations/_pickers.py).

## Extraction Overview

This section contains an overview of the extraction process for data.

### 1. Scrape Crawling

Website scraping tools may store a webpage at path which is not easy to derive from the URL, for reasons such as path length limits. For this reason, we crawl the scrape directory and build a mapping of URL to path.

For every html file at any depth in the scrape directory, we:
1. Perform a limited parse of only the link and meta tags in the file's head.
2. Attempt to extract a valid URL from a `link` tag with `rel="alternate"` or `canonical` meta tag
3. Check the URL has not previously been seen, warn and skip if it has
4. Add the URL to the map with the absolute path of the file

This map is then saved as `url_cache.json` in the scrape directory. If an existing cache file is detected, it will be used instead of scraping again.

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
   * We do this in case sites have removed category slugs from the URL at some point.
4. If unsuccessful, warn that the URL is unresolvable

For each resolved link, translation, or media, a destination is set containing its normalised URL, data type, and ID.

### 5. Export

The columns of each type are subset and exported as a JSON file each.