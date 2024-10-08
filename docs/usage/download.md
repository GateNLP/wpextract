# Download Command

The `wpextract download` command downloads the content of a site using the REST API.

## Command Usage

```shell-session
$ wpextract download TARGET OUT_JSON
```

`TARGET`
:  The base path of the WordPress installation, e.g.
  "https://example.org/"

`OUT_JSON`
: Directory to output the downloaded JSON to. It must be an
  existing empty directory or a non-existent directory which will be created.

**optional arguments**
`--media-dest`
: Path to a directory to download media files to, skipped if not supplied

`--json-prefix JSON_PREFIX`
:  Prefix to add to output file names, e.g. supplying _20240101-example_ will output posts to `out_dir/20240101-example-posts.json`

**skip data**

`--skip-type [categories|media|pages|posts|tags|users]`
:  Don't download the provided types. All others will be downloaded, default is to download all.

**authentication**

`--proxy PROXY`
: Proxy server for requests

`--auth AUTH`
: HTTP Basic credentials for requests (format `username:password`)

`--cookies COOKIES`
:  Cookies for requests (format `cookie1=foo; cookie2=bar`)

**request behaviour**

`--timeout TIMEOUT`
: Timeout for request in seconds (default: 30)

`--wait WAIT`
:  Time to wait between requests in seconds. Does not affect retries. (default: 0)

`--random-wait`
: Randomly varies the time between requests to between 0.5 and 1.5 times the number of seconds set by --wait

`--max-retries MAX_RETRIES`
: Maximum number of retries before giving up (default: 10)

`--backoff-factor BACKOFF_FACTOR`
: Factor to apply delaying retries. Default will sleep for 0.0, 0.2, 0.4, 0.8,… (default: 0.1)

`--max-redirects MAX_REDIRECTS`
: Maximum number of redirects before giving up (default: 20)

`--user-agent USER_AGENT`
: User agent to use for requests. Default is a recent version of Chrome on Linux (see [`requestsession.DEFAULT_UA`][wpextract.download.requestsession.DEFAULT_UA])

**logging**

`--log FILE`, `-l FILE`
: File to log to, will suppress stdout.

`--verbose`, `-v`
: Increase log level to include debug logs

## Download Process

For each enabled data type (categories, media, pages, posts, tags, users; all by default), the command will use the REST API to download the data. The API is paginated and the command will show a progress bar for each page of data.

## Endpoints

To produce each file, the following list endpoints are used:

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

### Bot Protection and Considerate Scraping

It's unlikely this will trigger bot protection mechanisms for the following reasons:

- it is accessing intended API endpoints, which are likely to have lower levels of bot protection
- it has been configured to use a browser user agent

The following measures are taken to be considerate to the server:

- a backoff factor is applied to retries

We would also suggest enabling the following options, with consideration for how they will affect the download speed:

- `--wait` to space out requests
- `--random-wait` to vary the time between requests to avoid patterns

You may also wish to consider:

- The reputation of the IP used to make requests. IPs in ranges belonging to common VPS providers, e.g. DigitalOcean or AWS, may be more likely to be rate limited.
- `--user-agent` to set a custom user agent. The default is a recent version of Chrome on Linux, but this may become outdated. If using authentication, this may need to match the user agent of the browser used to log in.

### Error Handling

If an HTTP error occurs, the command will retry the request up to `--max-retries` times, with the backoff set by `--backoff-factor`. If the maximum number of retries is reached, the command will output the error, stop collecting the given data type, and start collecting the following data type. This is because it's presumed that if a given page is non-functional, the following one will be too.

To ensure the integrity of the scrape, it is suggested to check the logs for errors afterwards.

There is currently no mechanism to resume interrupted downloads.