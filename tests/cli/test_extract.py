from wpextract.cli import cli


def mock_cls_invoke(mocker, runner, datadir, args=None, mkdirs=True):
    in_dir = datadir / "json_in"
    out_dir = datadir / "json_out"
    if mkdirs:
        in_dir.mkdir()
        out_dir.mkdir()

    if args is None:
        args = []
    dl_mock = mocker.patch("wpextract.cli._extract.WPExtractor")

    result = runner.invoke(cli, ['extract', str(in_dir), str(out_dir), *args])

    return dl_mock, result

def test_default_args(mocker, runner, datadir):
    dl_mock, result = mock_cls_invoke(mocker, runner, datadir)
    assert result.exit_code == 0

    assert dl_mock.call_args.kwargs['json_root'] == datadir / "json_in"
    assert dl_mock.call_args.kwargs['scrape_root'] is None
    assert dl_mock.call_args.kwargs['json_prefix'] is None

    dl_mock.return_value.extract.assert_called_once()
    dl_mock.return_value.export.assert_called_once_with(datadir / "json_out")