from dataclasses import dataclass

from langcodes import Language

from extractor.extractors.data.links import ResolvableLink


@dataclass
class TranslationLink(ResolvableLink):
    """A link to an alternative version of this article in a different language."""

    def __init__(self, lang: str, *args, **kwargs):
        """Initialise a new translation link.

        Args:
            lang: The language code, which will be normalised.
            *args: will be passed to :class:ResolvableLink
            **kwargs: will be passed to :class:ResolvableLink
        """
        self.language = Language.get(lang, normalize=True)
        super().__init__(*args, **kwargs)
