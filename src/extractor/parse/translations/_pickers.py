from abc import ABC, abstractmethod
from typing import List

from bs4 import BeautifulSoup, PageElement, Tag
from langcodes import Language

from extractor.parse.translations._resolver import TranslationLink


class LangPicker(ABC):
    """Abstract class of a language picker style."""

    root_el: Tag
    translations: List[TranslationLink] = []
    current_language: Language

    def __init__(self, page_doc: BeautifulSoup):
        """Inits a language picker searcher.

        Args:
            page_doc: The document to extract a language picker from.
        """
        self.page_doc = page_doc

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

        if type(root) is Tag or len(root.children) == 1:
            self.root_el = root
        else:
            raise TypeError(f"Root is not a tag, is {type(root)}")

    @abstractmethod
    def get_root(self) -> PageElement:
        """Retrieve the root element of the translation picker.

        Should contain the element which indicates the current language
        and lists translations.

        Returns:
            The root element.
        """
        pass

    @abstractmethod
    def extract(self) -> None:
        """Extract the current language and translations from the doc."""
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


class Polylang(LangPicker):
    """Language picker from the plugin \
    `Polylang <https://wordpress.org/plugins/polylang/>`.

    Has the structure::

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

    """

    def get_root(self) -> PageElement:
        """Get the root element.

        Returns:
            The .widget_polylang tag
        """
        return self.page_doc.find(".widget_polylang")

    def extract(self) -> None:
        """Extract the translation links.

        Retrieves the current language by checking the ``lang`` attribute of a
        link within an `li` with the class `.lang-item.current-lang`.

        Retrieves translations by searching for links within ``.lang-item`` unless they:
        * have the ``.no-translation`` class - this language is missing and the link \
            will usually go to the language's homepage
        * have the ``.current-lang`` class - this is the current language.
        """
        current_lang = self.root_el.find(".lang-item.current-lang a")
        self.set_current_lang(current_lang["lang"])

        other_langs = self.root_el.select(
            ".lang-item:not(.no-translation):not(.current-lang) a"
        )

        for lang_a in other_langs:
            href = lang_a["href"]
            lang = lang_a["lang"]

            self.add_translation(href, lang)


class GenericLangSwitcher(LangPicker):
    """A language picker in Polylang-style but using some different markup.

    Finds language pickers in the form:::

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
    """

    def get_root(self) -> PageElement:
        """Get the root element of the picker.

        Returns:
            The lang switcher root.
        """
        return self.page_doc.find(".header-lang_switcher")

    def extract(self) -> None:
        """Extract the translation links.

        Retrieves all links in a ``.lang-item`` unless they:
        * have the ``.no-translation`` class
        * have the ``current-lang`` class
        """
        current_lang = self.root_el.find(".current-lang-switcher")
        self.set_current_lang(current_lang.get_text())

        other_langs = self.root_el.select(".lang-item:not(.no-translation)")

        for lang_a in other_langs:
            href = lang_a["href"]
            lang = lang_a["lang"]

            self.add_translation(href, lang)
