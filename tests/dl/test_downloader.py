import pytest
from wpextract import WPDownloader
from wpextract.dl.exporter import Exporter
from wpextract.dl.requestsession import ConnectionRefused
from wpextract.dl.wpapi import WPApi


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
    return [{"id": idx, "title": "dummy return"} for idx in range(20)]


def _export_method(datatype):
    if datatype == "comments":
        return "export_comments_interactive"
    return f"export_{datatype}"


def _mocked_exporter(mocker, datatype):
    cls = "wpextract.dl.exporter.Exporter."
    if datatype == "comments":
        method = cls + "export_comments_interactive"
    else:
        method = cls + f"export_{datatype}"

    return mocker.patch(method)


@pytest.fixture()
def mock_request_session(mocker):
    mock_session_cls = mocker.patch("wpextract.dl.downloader.RequestSession")
    mock_session_cls = mock_session_cls.return_value
    return mock_session_cls


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
    exporter = _mocked_exporter(mocker, datatype)

    downloader.download()

    downloader.scanner.get_obj_list.assert_called_once_with(
        value,
        None,
        None,
        True,
        kwargs={"comments": False} if datatype == "posts" else {},
    )

    exporter.assert_called_once()


def test_prefix(datadir, mocker, mock_request_session):
    downloader = _make_downloader(datadir, mocker, ["pages"], "myprefix")
    exporter = _mocked_exporter(mocker, "pages")

    downloader.download()

    exporter.assert_called_once_with(
        _fake_api_return(),
        Exporter.JSON,
        datadir / "myprefix-pages.json",
    )
