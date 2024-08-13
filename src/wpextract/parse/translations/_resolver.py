from dataclasses import dataclass
from typing import Union

from langcodes import Language

from wpextract.extractors.data.links import ResolvableLink


@dataclass
class TranslationLink(ResolvableLink):
    """A link to an alternative version of this article in a different language."""

    lang: Union[str, Language]
    """Raw language code, or existing language object if derived from another source."""

    @property
    def language(self) -> Language:
        """Parsed and normalized language. Populated automatically post-init.

        See Also:
            [`langcodes` documentation](https://github.com/georgkrause/langcodes?tab=readme-ov-file#language-objects)
        """
        return Language.get(self.lang, normalize=True)
