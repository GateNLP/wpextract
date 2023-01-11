import pytest

from extractor.extractors.data.link_resolver import resolve_link
from extractor.extractors.data.links import LinkRegistry, ResolvableLink


def test_link_resolver():
    registry = LinkRegistry()
    registry.add_linkable("https://example.org/post1", "post", "1")
    registry.add_linkable("https://example.or/post2", "post", "2")

    resolvable = ResolvableLink("test", "https://example.org/post1", None)

    assert resolve_link(registry, resolvable).destination == registry.links[0]


def test_link_resolver_not_found():
    registry = LinkRegistry()
    registry.add_linkable("https://example.org/post1", "post", "1")

    resolvable = ResolvableLink("test", "https://example.org/post2", None)

    assert (resolve_link(registry, resolvable)).destination is None


def test_link_resolver_preview_page():
    registry = LinkRegistry()
    registry.add_linkable("https://example.org/post1", "post", "1")

    resolvable = ResolvableLink(
        "test",
        (
            "https://example.org/post1?preview_id=1234"
            "&preview_nonce=3ec34d434&preview=true"
        ),
        None,
    )
    assert resolve_link(registry, resolvable).destination == registry.links[0]


@pytest.mark.skip(reason="TODO: allow relative links")
def test_link_resolver_relative():
    registry = LinkRegistry()
    registry.add_linkable("https://example.org/post1", "post", 1)

    resolvable = ResolvableLink("test", "/post1", None)

    assert resolve_link(registry, resolvable).destination == registry.links[0]


@pytest.mark.skip(reason="TODO: trailing slash resolution")
def test_link_resolver_trailing_slash():
    registry = LinkRegistry()
    registry.add_linkable("https://example.org/with/", "post", 1)
    registry.add_linkable("https://example.org/without", "post", 2)

    resolvable_1 = ResolvableLink("test", "https://example.org/with", None)

    resolvable_2 = ResolvableLink("test", "https://example.org/without/", None)

    assert resolve_link(registry, resolvable_1).destination == registry.links[0]
    assert resolve_link(registry, resolvable_2).destination == registry.links[1]
