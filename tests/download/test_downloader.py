import logging

import pytest
from wpextract import WPDownloader
from wpextract.download.exceptions import WordPressApiNotV2
from wpextract.download.requestsession import ConnectionRefused
from wpextract.download.wpapi import WPApi


def _make_downloader(datadir, mocker, datatypes, json_prefix=None):
    downloader = WPDownloader(
        target="https://example.org",
        out_path=datadir,
        data_types=datatypes,
        json_prefix=json_prefix,
    )
    downloader.scanner = mocker.Mock()
    downloader.scanner.get_obj_list.return_value = _fake_api_return()
    return downloader


@pytest.fixture()
def downloader(datadir, mocker):
    return _make_downloader(datadir, mocker, ["posts"])


def _fake_api_return():
    return [{"id": idx, "title": "dummy return"} for idx in range(20)], 20


def _mocked_exporter(mocker, datatype):
    cls = "wpextract.download.exporter.Exporter."
    if datatype == "comments":
        method = cls + "export_comments_interactive"
    elif datatype == "media_files":
        method = cls + "download_media"
    else:
        method = cls + f"export_{datatype}"

    return mocker.patch(method)


def test_session_test_working(mock_request_session, downloader):
    mock_request_session.get.assert_called_once_with("https://example.org")


def test_session_test_fail(datadir, mock_request_session, caplog, mocker):
    mock_request_session.get.side_effect = ConnectionRefused

    with pytest.raises(ConnectionRefused):
        _make_downloader(datadir, mocker, ["comments"])

    assert "Failed to connect" in caplog.text


@pytest.mark.parametrize(
    ("datatype", "value"),
    [
        ("users", WPApi.USER),
        ("tags", WPApi.TAG),
        ("categories", WPApi.CATEGORY),
        ("posts", WPApi.POST),
        ("pages", WPApi.PAGE),
        ("comments", WPApi.COMMENT),
        ("media", WPApi.MEDIA),
    ],
)
def test_download_data_type(datadir, mocker, mock_request_session, datatype, value):
    downloader = _make_downloader(datadir, mocker, [datatype])
    exporter_func = _mocked_exporter(mocker, datatype)

    downloader.download()

    downloader.scanner.get_obj_list.assert_called_once_with(
        value,
        None,
        None,
    )

    exporter_func.assert_called_once()


def test_download_invalid_data_type(datadir, mocker, mock_request_session):
    downloader = _make_downloader(datadir, mocker, ["invalid"])
    downloader._list_obj = mocker.Mock()
    downloader.download()
    downloader._list_obj.assert_not_called()


@pytest.mark.parametrize(
    ("prefix", "expected_name"),
    [("myprefix", "myprefix-pages.json"), (None, "pages.json")],
)
def test_prefix(datadir, mocker, mock_request_session, prefix, expected_name):
    downloader = _make_downloader(datadir, mocker, ["pages"], prefix)
    exporter_func = _mocked_exporter(mocker, "pages")

    downloader.download()

    exporter_func.assert_called_once_with(
        _fake_api_return()[0],
        datadir / expected_name,
    )


def test_wpapi_not_v2(datadir, mocker, caplog, mock_request_session):
    downloader = _make_downloader(datadir, mocker, ["posts"])
    downloader.scanner.get_obj_list.side_effect = WordPressApiNotV2
    with caplog.at_level(logging.ERROR):
        downloader.download()

    assert "The API does not support WP V2" in caplog.text


MEDIA_DATA = (
    [f"https://example.org/wp-content/uploads/2024/01/image{n}.jpg" for n in range(10)],
    [f"image{n}" for n in range(10)],
)


def test_download_media_files(datadir, mocker, mock_request_session):
    downloader = _make_downloader(datadir, mocker, ["media"])
    downloader.scanner.get_media_urls.return_value = MEDIA_DATA
    exporter_func = _mocked_exporter(mocker, "media_files")

    downloader.download_media_files(mock_request_session, datadir)

    exporter_func.assert_called_once_with(mock_request_session, MEDIA_DATA[0], datadir)


def test_download_media_files_no_media(datadir, mocker, caplog, mock_request_session):
    downloader = _make_downloader(datadir, mocker, ["media"])
    downloader.scanner.get_media_urls.return_value = ([], [])

    downloader.download_media_files(mock_request_session, datadir)

    assert "No media found" in caplog.text
