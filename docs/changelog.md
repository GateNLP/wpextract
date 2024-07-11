# Changelog

## 1.0.0

_Released: 11th July 2024_

This release is a major overhaul of the tool including built-in download functionality.

- Moved the extraction functionality to the `wpextract extract` subcommand
- Integrate a heavily modified version of [WPJsonScraper](`https://github.com/MickaelWalter/wp-json-scraper`) as the `wpextract download` subcommand
- Renamed the main package of this library to `wpextract` to match the CLI tool name
- Support extraction without an HTML scrape if translations aren't needed
- Support extracting only some of the possible data types
- Support sites without Yoast SEO plugin
- Added [online documentation](https://gatenlp.github.io/wpextract/)
