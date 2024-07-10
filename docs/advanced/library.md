# Using as a Library

The extractor can also be used as a library instead of on the command line.

Typically, you would:

- instantiate a [`WPDownloader`][wpextract.WPDownloader] instance and call its [`download`][wpextract.WPDownloader.download] method.
- instantiate a [`WPExtractor`][wpextract.WPExtractor] instance and call its `extract` method. The dataframes can then be accessed as class attributes or exported with the `export` method.

Examples of usage are available in the CLI scripts in the `wpextract.cli` module.



## Downloader

Use the [`wpextract.WPDownloader`][wpextract.WPDownloader] class.

Compared to the CLI, you can:

- implement highly custom request behaviour by subclassing [`RequestSession`][wpextract.dl.RequestSession] and passing to the `session` argument.


## Extractor

Use the [`wpextract.WPExtractor`][wpextract.WPExtractor] class.

Compared to the CLI, you can:

 - set [customised translation pickers](../advanced/multilingual.md#adding-support) by passing subclasses of [`LanguagePicker`][wpextract.parse.translations.LangPicker] to the `translation_pickers` argument.
