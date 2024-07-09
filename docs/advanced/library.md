# Using as a Library

The extractor can also be used as a library instead of on the command line.

Typically, you would:

- instantiate a [`WPDownloader`][extractor.WPDownloader] instance and call its [`download`][extractor.WPDownloader.download] method.
- instantiate a [`WPExtractor`][extractor.WPExtractor] instance and call its `extract` method. The dataframes can then be accessed as class attributes or exported with the `export` method.

Examples of usage are available in the CLI scripts in the `extractor.cli` module.



## Downloader

Use the [`extractor.WPDownloader`][extractor.WPDownloader] class.

Possible customisations include:

- Implement highly custom request behaviour by subclassing [`RequestSession`][extractor.dl.RequestSession] and passing to the `session` parameter.


## Extractor

Use the [`extractor.WPExtractor`][extractor.WPExtractor] class.

When using this approach, it's possible to use [customised translation pickers](../advanced/multilingual.md#adding-support) by passing subclasses of [`LanguagePicker`][extractor.parse.translations.LangPicker] to the 
