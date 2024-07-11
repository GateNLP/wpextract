from dataclasses import dataclass

from langcodes import Language

from wpextract.extractors.data.links import ResolvableLink


@dataclass
class TranslationLink(ResolvableLink):
    """A link to an alternative version of this article in a different language."""

    lang: str
    """Raw language code."""

    @property
    def language(self) -> Language:
        """Parsed and normalized language. Populated automatically post-init."""
        return Language.get(self.lang, normalize=True)
