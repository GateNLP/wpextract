# Changelog

## 1.1.0 (2024-08-13)

**Features & Improvements**

- WPextract is now completely type-annotated, and ships a `py.typed` file to indicate this
- Added `--user-agent` argument to `wpextract download` to allow customisation of the user agent string
- HTTP errors raised when downloading now all inherit from a common `HTTPError` class
- If an HTTP error is encountered while downloading, it will no longer end the whole scrape process. A warning will be logged and the scrape will continue, and if some data was obtained for that type, it will be saved as normal. HTTP transit errors (e.g. connection timeouts) will still end the scrape process.
- Improved the resiliency of HTML parsing and extraction by better checking for edge cases like missing attributes
  - Translation picker extractors will now raise an exception if elements are missing during the extraction process.
- Simplified the WordPress API library by removing now-unused cache functionality. This will likely improve memory usage of the download process.
- Significantly more tests have been added, particularly for the download process


**Fixes**

- Fixed the scrape crawling step crashing if a page didn't have a canonical link or `og:url` meta tag
- Fixed the scrape crawling not correctly recognising when duplicate URLs were encountered. Previously duplicates would be included, but only one would be used. Now, they will be correctly logged. As a result of this change, the `SCRAPE_CRAWL_VERSION` has been incremented, meaning running extraction on a scrape will cause it to be re-crawled.
- Fixed the return type annotation `LangPicker.get_root()`: it is now annotated as (`bs4.Tag` or `None`) instead of `bs4.PageElement`. This shouldn't be a breaking change, as the expected return type of this function was always a `Tag` object or `None`.
- Type of `TranslationLink.lang` changed to reflect that it can accept a string to resolve or an already resolved `Language` instance
- Fixed downloading throwing an error stating the WordPress v2 API was not supported in other error cases
- Fixed the maximum redirects permitted not being set properly, meaning the effective value was always 30

**Documentation**

- Improved guide on translation parsing, correcting some errors and adding information on parse robustness and performance

## 1.0.3 (2024-08-06)

**Changes**

- Added missing `wpextract.__version__` attribute (!36)
- Added `<table>`s to the elements to be ignored when extracting article text (!40)

**Fixes**

- Fixed incorrect behaviour extracting article text where only the first element to ignore (e.g. `figcaption`) would be ignored (!40)

**Documentation**

- Added proper references to the documentation of the [`langcodes`](https://github.com/georgkrause/langcodes) library (!38)

## 1.0.2 (2024-07-12)

- Fixed not explicitly declaring dependency on `urllib3` (!32)
- Improved CLI performance with lazy imports of library functionality (!33)

## 1.0.1 (2024-07-11)

- Fixed an incorrect repository URL in the package metadata and CLI epilog (!29)

## 1.0.0 (2024-07-11)

This release is a major overhaul of the tool including built-in download functionality.

- Moved the extraction functionality to the `wpextract extract` subcommand
- Integrate a heavily modified version of [WPJsonScraper](`https://github.com/MickaelWalter/wp-json-scraper`) as the `wpextract download` subcommand
- Renamed the main package of this library to `wpextract` to match the CLI tool name
- Support extraction without an HTML scrape if translations aren't needed
- Support extracting only some of the possible data types
- Support sites without Yoast SEO plugin
- Added [online documentation](https://wpextract.readthedocs.io/)
