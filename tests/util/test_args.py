from argparse import ArgumentTypeError

import pytest
from wpextract.util.args import directory, empty_directory


def test_directory_when_directory(tmp_path):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    assert directory(str(dir_path)) == dir_path


def test_directory_when_file(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test")

    with pytest.raises(ArgumentTypeError):
        directory(str(file_path))


def test_empty_directory_when_not_exists(tmp_path):
    dir_path = tmp_path / "dir"

    assert empty_directory(str(dir_path)) == dir_path


def test_empty_directory_when_exists_empty(tmp_path):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()

    assert empty_directory(str(dir_path)) == dir_path


def test_empty_directory_when_exists_not_empty(tmp_path):
    dir_path = tmp_path / "dir"
    dir_path.mkdir()
    (dir_path / "file.txt").write_text("test")

    with pytest.raises(ArgumentTypeError):
        empty_directory(str(dir_path))
