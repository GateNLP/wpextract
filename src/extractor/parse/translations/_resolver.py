from dataclasses import dataclass

from langcodes import Language

from extractor.extractors.data.links import ResolvableLink


@dataclass
class TranslationLink(ResolvableLink):
    """A link to an alternative version of this article in a different language."""

    lang: str
    """Raw language code."""
    language: Language
    """Parsed and normalized language. Populated automatically post-init."""

    def __post_init__(self) -> None:
        """Parse string lang into normalised language."""
        self.language = Language.get(self.lang, normalize=True)
