from wpextract.cli import cli


def mock_cls_invoke(mocker, runner, datadir, args=None):
    if args is None:
        args = []
    dl_mock = mocker.patch("wpextract.cli._download.WPDownloader")

    result = runner.invoke(
        cli, ["download", "https://example.org", str(datadir), *args]
    )

    return dl_mock, result


def test_default_args(mocker, runner, datadir):
    dl_mock, result = mock_cls_invoke(mocker, runner, datadir)
    assert result.exit_code == 0

    assert dl_mock.call_args.kwargs["target"] == "https://example.org/"
    assert dl_mock.call_args.kwargs["out_path"] == datadir
    assert len(dl_mock.call_args.kwargs["data_types"]) == 6

    dl_mock.return_value.download.assert_called_once()


def test_disable_type(mocker, runner, datadir):
    dl_mock, result = mock_cls_invoke(mocker, runner, datadir, ["--skip-type", "posts"])

    assert "posts" not in dl_mock.call_args.kwargs["data_types"]


def test_wait_random_validation(mocker, runner, datadir):
    dl_mock, result = mock_cls_invoke(mocker, runner, datadir, ["--random-wait"])
    assert result.exit_code == 2

    dl_mock, result = mock_cls_invoke(
        mocker, runner, datadir, ["--random-wait", "--wait", "1"]
    )
    assert result.exit_code == 0
