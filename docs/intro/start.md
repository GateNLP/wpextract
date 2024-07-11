# Getting Started

In this guide we will use the command-line interface (CLI) of WPextract to download a copy of a WordPress site and produce a usable cross-referenced dataset. Afterwards, you should be ready to use WPextract for your own research or archiving.

!!! warning "Be considerate when using this tool."

    It is your responsibility to ensure any usage of this tool is ethical and compliant with the law. In general, you should only scrape sites with permission of the owner, or for appropriate research following your institution's ethical guidelines.
    
    You should use the options included in the `download` command to minimise the impact of this tool on servers.


## Installation

See the [installation instructions](install.md) for requirements and alternative methods.


WPExtract can be quickly installed in a sandboxed environment with [pipx](https://pipx.pypa.io/stable/docs/):

```shell-session
$ pipx install wpextract
```

## WPextract Stages

WPextract works in two steps:

1. The **downloader** uses the WordPress REST API to obtain all content on the site, which is stored as a single, long file
2. The **extractor** converts this into a usable dataset by enriching the downloaded content. This includes extracting text, images, resolving links to posts/pages, and finding translated versions[^lang]

[^lang]: {-} See the specific guide for more on multilingual extraction.

We call these two stages using two CLI commands ([`wpextract download`](../usage/download.md#command-usage) and [`wpextract extract`](../usage/extract.md#command-usage)). Alternatively, WPExtract can be integrated into a project by [using it as a library](../advanced/library.md).

## 1. Downloading

For the purposes of this guide, we'll use the URL `https://example.org` - in reality this isn't a WordPress site, so you should replace it with the URL of the site you're interested in.

To download the contents of `https://example.org` to the directory `./example.org`, run:

```shell-session
$ wpextract download "https://example.org" ./example.org
```

Progress bars will be displayed as it iterates through the pages of each content type until completed.

The `./example.org` directory will now contain 6 JSON files containing the categories, media, pages, posts, tags and users data. These are simply all the pages retrieved from the API, concatenated together.

Using this data directly has several issues:

- _Post and page content is provided as rendered HTML_ - although this is cleaner than scraped HTML, it may still contain intermingled content like images.
- _No information on links or media_ - links between posts and pages and media used are only available as `<a>`/`<img>` tags within the source, so can't be directly used for analysis
- _Data may be missing_ - Data from some plugins may not be present in the API response, so an HTML scrape needs to be performed and somehow connected to the API response.

To rectify this, we use the extract command to build a usable dataset.

## 2. Extraction

Now, we call the second command passing in the output directory from the first (`./example.org`) and an output directory for our data (`./example.org-data`)

```shell-session
$ wpextract extract ./example.org ./example.org-data
```

This will again output 6 JSON files containing a modified version of the WordPress API schema. This includes:

- plain text content for posts and pages with normalised paragraph breaks and no stray inline content
- internal links are resolved to the type of data (post, page, media) and its ID
- media is resolved to its associated media ID
- embeds (`<iframe>` tags, e.g. YouTube videos) are listed
- many unnecessary fields are removed
- some fields provided by plugins are kept and used if available

## Further Information

This guide only covered the basic use-case of WPextract, for further information see:

* More comprehensive documentation of the [download](../usage/download.md) and [extract](../usage/extract.md) commands
* How to extract [multilingual data](../advanced/multilingual.md)