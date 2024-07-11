import pytest
from wpextract.util.str import (
    ensure_suffix,
    remove_ends,
    remove_prefix,
    remove_suffix,
    squash_whitespace, ensure_prefix, ensure_prefixes,
)


def test_remove_prefix():
    assert remove_prefix("pypython", "py") == "python"
    assert remove_prefix("python", "foo") == "python"


def test_remove_suffix():
    assert remove_suffix("pythonpy", "py") == "python"
    assert remove_suffix("python", "py") == "python"


def test_remove_ends():
    assert remove_ends("pypythonpy", "py") == "python"
    assert remove_ends("python", "foo") == "python"


def test_ensure_prefixes():
    assert ensure_prefixes("http://example.org", ("http://", "https://"), "http://") == "http://example.org"
    assert ensure_prefixes("https://example.org", ("http://", "https://"), "http://") == "https://example.org"
    assert ensure_prefixes("example.org", ("http://", "https://"), "http://") == "http://example.org"


def test_ensure_prefix():
    assert ensure_prefix("python", "foo") == "foopython"
    assert ensure_prefix("foopython", "foo") == "foopython"

def test_ensure_suffix():
    assert ensure_suffix("python", "foo") == "pythonfoo"
    assert ensure_suffix("pythonfoo", "foo") == "pythonfoo"

@pytest.mark.parametrize(
    ("trial", "expected", "message"),
    [
        ("foo\n\nbar", "foo\nbar", "should remove adjacent newlines"),
        ("  foo  ", "foo", "should remove start and end whitespace"),
        ("foo\n bar", "foo\nbar", "should remove start of line whitespace"),
        ("foo\n\t\tbar", "foo\nbar", "should remove tabs"),
        ("foo\n  \nbar", "foo\nbar", "should remove whitespace-only lines"),
    ],
)
def test_squash_whitespace(trial, expected, message):
    assert squash_whitespace(trial) == expected, message
