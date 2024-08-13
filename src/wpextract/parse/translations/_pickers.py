from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Optional

from bs4 import BeautifulSoup, Tag
from langcodes import Language

from wpextract.parse.translations._resolver import TranslationLink
from wpextract.util.html import attr_concat
from wpextract.util.str import squash_whitespace


class ExtractionFailedError(Exception):
    pass


class LangPicker(ABC):
    """Abstract class of a language picker style.

    Support for a new language picker can be added by creating a new class inheriting from this one.

    See Also:
        * [Creating a new picker](../advanced/multilingual.md#adding-support) guide
    """

    page_doc: BeautifulSoup
    """The document to extract the language picker from."""
    root_el: Tag
    """The root element of the language picker, populated if [`LangPicker.matches`][wpextract.parse.translations.LangPicker.matches] is succesful."""
    translations: list[TranslationLink]
    """A list of translation links, populated by calling [`LangPicker.add_translation`][wpextract.parse.translations.LangPicker.add_translation] within [`LangPicker.extract`][wpextract.parse.translations.LangPicker.extract]."""
    current_language: Language
    """The current language of the page, populated by calling [`LangPicker.set_current_lang`][wpextract.parse.translations.LangPicker.set_current_lang] within [`LangPicker.extract`][wpextract.parse.translations.LangPicker.extract]."""

    def __init__(self, page_doc: BeautifulSoup):
        """Inits a language picker searcher.

        Args:
            page_doc: The document to extract a language picker from.
        """
        self.page_doc = page_doc
        self.translations = []

    def matches(self) -> bool:
        """Checks if this picker can extract from the document.

        Returns:
            If the page uses this type of matcher.

        Raises:
            TypeError: If the root element that has been retrieved is not a tag,
                or has 0 children.
                This may happen if it accidentally retrieves a text node.
        """
        root = self.get_root()

        if root is None:
            return False

        if isinstance(root, Tag):
            self.root_el = root
            return True
        else:
            raise TypeError(f"Root is not a tag, is {type(root)}")

    @abstractmethod
    def get_root(self) -> Optional[Tag]:
        """Retrieve the root element of the translation picker.

        Using the [`LangPicker.page_doc`][wpextract.parse.translations.LangPicker.page_doc] attribute (a [`bs4.BeautifulSoup`][bs4.BeautifulSoup] object representing the whole page), the root element of the picker shoudl be found and returned.

        Returns:
            The root element, or None if this picker is not found on the page.
        """
        pass

    @abstractmethod
    def extract(self) -> None:
        """Extract the current language and translations from the doc.

        Instead of directly selecting on `root_el`, consider using the helper methods
        [`_root_select`][wpextract.parse.translations.LangPicker._root_select] and
        [`_root_select_one`][wpextract.parse.translations.LangPicker._root_select_one]
        to extract elements. These are the equivalent of directly calling `select` or `select_one`, but
        will raise a formatted error if the element is not found. Don't use these methods if no results is an expected
        outcome, e.g. a post may have no translations.

        If using other selectors, you can construct the exception using the helper
        [`_build_extraction_fail_err`][wpextract.parse.translations.LangPicker._build_extraction_fail_err].

        Raises:
            ExtractionFailedError: If the picker is unable to find an element it expects to be present.
        """
        pass

    def set_current_lang(self, lang: str) -> None:
        """Set the language of this doc.

        Args:
            lang: The locale string
        """
        self.current_language = Language.get(lang, normalize=True)

    def add_translation(self, href: str, lang: str) -> None:
        """Add a translation from the picker.

        Args:
            href: The link to the translated page.
            lang: The provided language code.
        """
        self.translations.append(
            TranslationLink(text=None, href=href, destination=None, lang=lang)
        )

    def _build_extraction_fail_err(self, selector: str) -> ExtractionFailedError:
        """Create an error for when an expected element is missing.

        Args:
            selector: a string describing the attempted selection criteria

        Returns:
            An instance of the exception to be raised.
        """
        message = f"{self.__class__.__name__} reported it could extract but failed to select element with: {selector}"
        return ExtractionFailedError(message)

    def _root_select(self, selector: str) -> Sequence[Tag]:
        """Helper to extract elements from the root element.

        Args:
            selector: a CSS selector to be passed to `Tag.select`

        Raises:
            ExtractionFailedError: If no matching elements were found. This indicates this picker was activated when it should not have been.

        Returns:
            The elements found by the selector.
        """
        els = self.root_el.select(selector)

        if len(els) == 0:
            raise self._build_extraction_fail_err(selector)

        return els

    def _root_select_one(self, selector: str) -> Tag:
        """Helper to extract an element from the root element.

        Args:
            selector: a CSS selector to be passed to `Tag.select_one`

        Raises:
            ExtractionFailedError: If the element was not found. This indicates this picker was activated when it should not have been.

        Returns:
            The element found by the selector.
        """
        el = self.root_el.select_one(selector)

        if el is None:
            raise self._build_extraction_fail_err(selector)

        return el


class PolylangWidget(LangPicker):
    """Language picker from the plugin Polylang used as a widget.

    [WordPress plugin page](https://wordpress.org/plugins/polylang/)

    Has the structure:

    ```html
    <div id="polylang" class="widget widget_polylang">
        <ul>
            <li class="lang-item lang-item-en current-lang lang-item-first">
                <a lang="en-US" hreflang="en-US" href="URL">\
                <img><span>English</span></a>
            </li>
            <li class="lang-item lang-item-20 lang-item-fr">
                <a lang="fr-FR" hreflang="fr-FR" href="URL">\
                <img><span>Français</span></a>
            </li>
            ...
        </ul>
    </div>
    ```
    """

    def get_root(self) -> Optional[Tag]:
        """Get the root element.

        Returns:
            The .widget_polylang tag
        """
        return self.page_doc.select_one(".widget_polylang")

    def extract(self) -> None:
        """Extract the translation links.

        Retrieves the current language by checking the ``lang`` attribute of a
        link within an `li` with the class `.lang-item.current-lang`.

        Retrieves translations by searching for links within ``.lang-item`` unless they:
        * have the ``.no-translation`` class - this language is missing and the link \
            will usually go to the language's homepage
        * have the ``.current-lang`` class - this is the current language.
        """
        current_lang = self._root_select_one(".lang-item.current-lang a")

        self.set_current_lang(attr_concat(current_lang["lang"]))

        other_langs = self.root_el.select(
            ".lang-item:not(.no-translation):not(.current-lang) a"
        )

        for lang_a in other_langs:
            href = attr_concat(lang_a["href"])
            lang = attr_concat(lang_a["lang"])

            self.add_translation(href, lang)


class PolylangCustomDropdown(LangPicker):
    """Language picker for an in-the-wild version of polylang.

    This was implemented to support a specific site of interest.

    Finds language pickers in the form:

    ```html
    <div class="header-lang_switcher switcher-ltr">
        <div class="current-lang-switcher">
            <img><span>en</span>
        </div>
        <ul>
            <li class="lang-item lang-item-fr lang-item-first">
                <a lang="fr-FR" hreflang="fr-FR" href="">Français</a>
            </li>
        </ul>
    </div>
    ```
    """

    def get_root(self) -> Optional[Tag]:
        """Get the root element of the picker.

        Returns:
            The lang switcher root.
        """
        return self.page_doc.select_one(".header-lang_switcher")

    def extract(self) -> None:
        """Extract the translation links.

        Retrieves all links in a ``.lang-item`` unless they:
        * have the ``.no-translation`` class
        * have the ``current-lang`` class
        """
        current_lang = self._root_select_one(".current-lang-switcher")
        self.set_current_lang(squash_whitespace(current_lang.get_text()))

        other_langs = self.root_el.select(".lang-item:not(.no-translation) a")

        for lang_a in other_langs:
            href = attr_concat(lang_a["href"])
            lang = attr_concat(lang_a["lang"])

            self.add_translation(href, lang)
