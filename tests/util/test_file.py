from extractor.util.file import prefix_filename


def test_prefix_filename():
    assert prefix_filename("test.txt", "prefix-") == "prefix-test.txt"


def test_prefix_filename_none():
    assert prefix_filename("test.txt", None) == "test.txt"
