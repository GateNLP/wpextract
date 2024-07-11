# Extract Command

The `wpextract extract` command converts the WordPress API response format into a usable dataset for downstream tasks.

## Command Usage

```shell-session
$ wpextract extract json_root out_dir
```

`json_root`
:  A directory containing a JSON dump of the data files, such as one generated with [`wpextract download`](download.md).

`out_dir`
: A path to output the extracted JSON to. It must be an existing empty directory or a non-existent directory which will be created.

**optional arguments**

`--scrape-root SCRAPE_ROOT`
: Root directory of an HTML scrape, see [scrape crawling](#1-scrape-crawling-optional).

`--json-prefix JSON_PREFIX`
: Prefix to use for input and output filenames, e.g. supplying _20240101-example_ will output posts to `out_dir/20240101-example-posts.json`

**logging**

`--log FILE`, `-l FILE`
: File to log to, will suppress stdout.

`--verbose`, `-v`
: Increase log level to include debug logs


## Extraction Process

### 1. Scrape Crawling (optional)

If a scrape is provided with the `--scrape-root` argument, it is first crawled to map the correspondence between the HTML files on disk and the post URLs.

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
   * Translations are detected using the translation pickers (implementing [`LangPicker`][wpextract.parse.translations.LangPicker])
   * Custom pickers can be added if using this tool as a library
   * Any extracted translations are stored as unresolved links
5. Add the post's link to the link registry[^linkregistry]
6. Using the parsed API content response, extract:
   * Internal links (stored as unresolved links)
   * External links (stored as resolved links)
   * Embeds (`iframe` tags)
   * Images (stored as unresolved media if internal, resolved media if external), including their source URL, alt text and caption (if they are in a `figure`)
   * Raw text content, via the following process:
     1. Remove tags which contain unwanted text (e.g. `figcaptions`)
     2. Replace `<br>` tags and `<p>` tags with newline characters
     3. Combine all page text

[^linkregistry]: The link registry stores a map between URLs of posts, pages, media etc. and their data type and ID. This is later used to resolve hyperlinks and media use.

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

The columns of each type are subset and exported as a JSON file each to the specified output path, using a prefix if supplied.
