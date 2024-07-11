from wpextract.cli import cli


def test_cli_root(runner):
    result = runner.invoke(cli)
    assert result.exit_code == 0
