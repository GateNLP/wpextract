# Multilingual Sites

If sites publish in multiple languages and use a plugin to present a list of language versions, wpextract can parse this and add links between translated versions in the output dataset.

## Extraction Process

Extracting multilingual data is performed during the [extract command](../usage/extract.md). This data isn't available in the WordPress REST API response, so instead must be obtained from scraped HTML.

Obtaining the scraped HTML is relatively straightforward, as we already have a list of all posts from the [download command](../usage/download.md).

One way this could be scraped is using `jq` to parse the downloaded posts file and produce a URL list, then `wget` to download each page:

```shell-session
$ cat posts.json | jq -r '.[] | .link' > url_list.txt
$ touch rejected.log
$ wget --adjust-extension --input-file=url_list.txt \
     --wait 1 --random-wait --force-directories \
     --rejected-log=rejected.log
```

When running [the extract command](../usage/extract.md), pass this directory as the `--scrape-root` argument. The scrape will be crawled to match URLs to downloaded HTML files following [this process](../usage/extract.md#1-scrape-crawling-optional).


## Supported Plugins

wpextract uses an extensible system of parsers to find language picker elements and extract their data.

Currently the following plugins are supported:

### Polylang
[Plugin Page](https://wordpress.org/plugins/polylang/) &middot; [Website](https://polylang.pro/)

**Supports**:

- Adding as a widget (e.g. to a sidebar)

    ??? example
        ```html
        --8<-- "tests/parse/translations/data/polylang_widget.html:struct"
        ```


- Adding to the navbar as a custom dropdown[^dropdown]

    ??? example
        ```html
        --8<-- "tests/parse/translations/data/polylang_custom_dropdown.html:struct"
        ```

**Does not support**:

- Methods which show the picker as a `<select>` element

[^dropdown]: This implementation may be overly customised to the site it was added to collect.

## Adding Support

!!! info "Note"
    To use additional pickers, you must [use WPextract as a library](library.md).

Support can be added by creating a new picker definition inheriting from [`LangPicker`][wpextract.parse.translations.LangPicker], and passing to the `translation_pickers` argument of [`WPExtractor`][wpextract.WPExtractor]

This parent class defines two abstract methods which must be implemented:

- [`LangPicker.get_root`][wpextract.parse.translations.LangPicker.get_root] - returns the root element of the picker
- [`LangPicker.extract`][wpextract.parse.translations.LangPicker.extract] - find the languages, call [`LangPicker.set_current_lang`][wpextract.parse.translations.LangPicker.set_current_lang] and call [`LangPicker.add_translation`][wpextract.parse.translations.LangPicker.add_translation] for each

More complicated pickers may need to override additional methods of the class, but should still ultimately populate the [`LangPicker.translations`][wpextract.parse.translations.LangPicker.translations] and [`LangPicker.current_language`][wpextract.parse.translations.LangPicker.current_language] attributes as the parent class does.

This section will show implementing a new picker with the following simplified markup:

!!! example "Example picker markup"
    ```html
    <ul class="translations">
      <li><a href="/page/" class="lang current-lang" lang="en">English</a></li>
      <li><a href="/de/seite/" class="lang" lang="de">Deutsch</a></li>
      <li><a href="/page/" class="lang no-translation" lang="fr">Français</a></li>
    </ul>
    ```

The correct parse of this picker should set the current language to English, add German as a translation, and ignore French.

### `get_root()`

!!! tip "Selector Support"

    The `select()` and `select_one()` methods use [Soup Sieve](https://facelessuser.github.io/soupsieve/) internally.

    This library supports many, but not all, CSS selectors. Supported selectors can be found [here](https://facelessuser.github.io/soupsieve/selectors/). Namespace selection is not supported as we use the `lxml` backend.

Using the `self.page_doc` attribute, a [`BeautifulSoup`][bs4.BeautifulSoup] object representing the page, the root element of the picker should be found and returned.

The `select_one` method is used to find the root element, and will return `None` if no element is found, which will be interpreted as the picker not being present on the page.

If a value is returned, the `self.root_el` attribute will be populated with the result of this method.

!!! example "Example `get_root` implementation"
    ```python

    class MyPicker(LangPicker):
        ...
        def get_root(self):
            return self.page_doc.select_one('ul.translations')
    ```

### `extract()`

Using the `self.root_el` attribute, the languages should be found and added to the dataset.

Be careful to avoid:

- Adding the current language as a translation
- Adding languages which are listed but don't have translations

!!! example "Example `extract` implementation"
    ```python

    class MyPicker(LangPicker):
        ...
        def extract(self):
            for lang_el in self.root_el.select('li'):
                lang_a = lang_el.select_one('a')
                if 'current-lang' in lang_a.get('class'):
                    self.set_current_lang(lang_a.get('lang'))
                elif 'no-translation' not in lang_a.get('class'):
                    self.add_translation(lang_a.get('href'), lang_a.get('lang'))
    ```

### Parsing Robustness

BeautifulSoup's `select` and `select_one` methods will silently fail if no matching elements are found (returning `None` and an empty list respectively). In some cases this may be desirable, e.g. if the picker contains no languages, `select_one` returning an empty list will probably be the correct behaviour.

In cases where this _isn't_ right, like when retrieving an element which should always be present, you can instead use the [`LangPicker._root_select()`][wpextract.parse.translations.LangPicker._root_select] or [`LangPicker._root_select_one()`][wpextract.parse.translations.LangPicker._root_select_one] methods. These will raise an error if no element(s) are found.

Currently, this error will be caught and the page in question will be skipped as if no translation picker could be found. In future, this may instead result in other pickers being tried instead.

!!! example "Example more robust `extract` implementation"
    ```python

    class MyPicker(LangPicker):
        ...
        def extract(self):
            # This should *always* be present, if it isn't this can't be the correct picker.
            current_lang_a = self._root_select_one('li a.current-lang')
            self.set_current_lang(current_lang_a.get('lang'))

            # This could be empty
            for lang_a in self.root_el.select('li a.lang'):
                if (
                    'current-lang' not in lang_a.get('class')
                    and 'no-translation' not in lang_a.get('class')
                ):
                    self.add_translation(lang_a.get('href'), lang_a.get('lang'))
    ```

??? note "Using other selector methods"

    BeautifulSoup's CSS selector methods should cover most use cases. However, if you need to use more complex selection logic, you can generate the same error by using the [`LangPicker._build_extraction_fail_err`][wpextract.parse.translations.LangPicker._build_extraction_fail_err] method.


### Performance

For each post in the site, the `get_root()` method of every `LangPicker` instance selected will be run, so the efficiency of this method is important.

* Try and make the test as specific as possible
* For more complex tests, consider splitting it up and failing early
* Minimise usage of dynamic patterns. SoupSieve internally caches the compiled form of each search pattern to improve performance, but any change will invalidate this. Consider splitting the static and dynamic parts of patterns to work around this.

### Contributing Pickers

We welcome contributions via a GitHub PR so long as the picker is not overly specific to a single site. 
