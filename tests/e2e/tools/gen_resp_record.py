from pathlib import Path

import yaml
from click.testing import CliRunner
from responses import _recorder
from wpextract.cli import cli


@_recorder.record(file_path="gen_record/requests_record.yaml")
def run_download(cli_runner, out_path):
    result = cli_runner.invoke(cli, ["download", "http://localhost", str(out_path)])
    print(result.output)  # noqa: T201


if __name__ == "__main__":
    out_root = Path(__file__).parent / "gen_record"
    temp_out_dir = (out_root / "out_data").resolve()
    temp_out_dir.mkdir(parents=True, exist_ok=True)
    run_download(CliRunner(), temp_out_dir)

    # Open and parse the output file
    out_file = out_root / "requests_record.yaml"
    data = yaml.safe_load(out_file.read_bytes())

    for resp in data["responses"]:
        if "wp-json" in resp["response"]["url"]:
            resp["response"]["content_type"] = "application/json"
        else:
            resp["response"]["content_type"] = "text/html"

    out_file.write_text(yaml.dump(data))
