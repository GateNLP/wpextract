from wpextract.dl.exporter import Exporter


def test_setup_escaping():
    entries = [{"id": 1, "field": "&lt;test&gt;"}, {"id": 2, "field": "unencoded"}]

    unencoded = Exporter.setup_export(entries, ["field"])
    assert unencoded[0]["field"] == "<test>"
    assert unencoded[1]["field"] == "unencoded"


def test_setup_escaping_nested():
    entries = [{"id": 1, "parent": {"child": "&lt;test&gt;"}}]

    unencoded = Exporter.setup_export(entries, [["parent", "child"]])
    assert unencoded[0]["parent"]["child"] == "<test>"
