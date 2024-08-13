from wpextract.download.exporter import Exporter


def test_setup_escaping():
    entries = [{"id": 1, "field": "&lt;test&gt;"}, {"id": 2, "field": "unencoded"}]

    unencoded = Exporter.setup_export(entries, ["field"])
    assert unencoded == [{"id": 1, "field": "<test>"}, {"id": 2, "field": "unencoded"}]

    unencoded2 = Exporter.setup_export(entries, [["field"]])
    assert unencoded2 == [{"id": 1, "field": "<test>"}, {"id": 2, "field": "unencoded"}]


def test_setup_escaping_nested():
    entries = [{"id": 1, "parent": {"child": "&lt;test&gt;", "sibling": "test"}}]

    unencoded = Exporter.setup_export(entries, [["parent", "child"]])
    assert unencoded == [{"id": 1, "parent": {"child": "<test>", "sibling": "test"}}]


def test_escape_unescapable():
    entries = [{"id": 1, "parent": {"child": 1, "sibling": "test"}}]
    unencoded = Exporter.setup_export(entries, [["parent", "child"]])
    assert unencoded == [{"id": 1, "parent": {"child": 1, "sibling": "test"}}]
