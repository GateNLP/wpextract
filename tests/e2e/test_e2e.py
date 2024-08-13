import json
import logging
import sys

from wpextract.cli import cli


def _load_data(path):
    with open(path) as f:
        return json.load(f)


def _num_entries(path):
    with open(path) as f:
        return len(json.load(f))


EXPECTED_DATA_LEN = {
    "categories": 15,
    "media": 63,
    "pages": 16,
    "posts": 54,
    "tags": 8,
    "users": 4,
}


def test_download(mocked_responses, caplog, shared_datadir, tmp_path, runner):
    mocked_responses._add_from_file(
        file_path=shared_datadir / "dl_requests_record.yaml"
    )
    out_path = tmp_path / "out_dl_data"
    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(
            cli, ["download", "http://localhost", str(out_path.resolve())]
        )
    sys.stdout.write(result.stdout)

    assert all([log.levelno <= logging.INFO for log in caplog.records])
    assert result.exit_code == 0

    for datatype, n in EXPECTED_DATA_LEN.items():
        assert (
            _num_entries(out_path / f"{datatype}.json") == n
        ), f"{datatype} count mismatch"

        assert _load_data(out_path / f"{datatype}.json") == _load_data(
            shared_datadir / f"download_out/{datatype}.json"
        ), f"{datatype} data mismatch"


def test_extract(runner, shared_datadir, tmp_path, caplog):
    dl_data = (shared_datadir / "download_out").resolve()
    scrape_data = (shared_datadir / "site_scrape").resolve()
    out_path = tmp_path / "out_extract"
    with caplog.at_level(logging.DEBUG):
        result = runner.invoke(
            cli,
            [
                "extract",
                str(dl_data),
                str(out_path.resolve()),
                "--scrape-root",
                str(scrape_data),
            ],
        )
    sys.stdout.write(result.stdout)

    assert all([log.levelno <= logging.INFO for log in caplog.records])
    assert result.exit_code == 0

    for datatype, n in EXPECTED_DATA_LEN.items():
        assert (
            _num_entries(out_path / f"{datatype}.json") == n
        ), f"{datatype} count mismatch"

        assert _load_data(out_path / f"{datatype}.json") == _load_data(
            shared_datadir / f"extract_out/{datatype}.json"
        ), f"{datatype} data mismatch"
