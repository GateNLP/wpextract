# Changelog

## 1.1.0 (upcoming)

**Fixes**

- Fixed the scrape crawling step crashing if a page didn't have a canonical link or `og:url` meta tag
- Fixed the scrape crawling not correctly recognising when duplicate URLs were encountered. Previously duplicates would be included, but only one would be used. Now, they will be correctly logged. As a result of this change, the `SCRAPE_CRAWL_VERSION` has been incremented, meaning running extraction on a scrape will cause it to be re-crawled.

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
