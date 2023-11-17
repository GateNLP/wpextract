from extractor.extractors.data.images import ResolvableMediaUse, resolve_image
from extractor.extractors.data.links import LinkRegistry


def test_image_resolver():
    registry = LinkRegistry()
    registry.add_linkable(
        "https://example.org/wp-content/uploads/2022/12/test-image.jpg", "media", 1
    )

    resolvable = ResolvableMediaUse(
        "https://example.org/wp-content/uploads/2022/12/test-image.jpg", "alt", None
    )

    assert resolve_image(registry, resolvable).destination == registry.links[0]


def test_image_resolver_with_dimensions():
    registry = LinkRegistry()
    registry.add_linkable(
        "https://example.org/wp-content/uploads/2022/12/test-image.jpg", "media", 1
    )

    resolvable = ResolvableMediaUse(
        "https://example.org/wp-content/uploads/2022/12/test-image-300x200.jpg",
        "alt",
        None,
    )

    assert resolve_image(registry, resolvable).destination == registry.links[0]
