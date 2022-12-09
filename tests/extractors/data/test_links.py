from extractor.extractors.data.links import Linkable, LinkRegistry


def test_add_link():
    r = LinkRegistry()
    r.add_linkable("https://example.org/post", "post", "1")

    assert len(r.links) == 1
    assert r.links[0] == Linkable(
        link="https://example.org/post", data_type="post", idx="1"
    )


IDXES = list(range(1, 4))
LINKS = [f"https://example.org/post{idx}" for idx in IDXES]


def test_add_links():
    r = LinkRegistry()
    r.add_linkables("post", LINKS, IDXES)

    assert len(r.links) == 3
    assert all([link.data_type == "post" for link in r.links])
