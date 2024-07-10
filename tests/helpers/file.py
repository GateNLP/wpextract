import json
import tempfile
from pathlib import Path


def json_without_cols(in_file: Path, del_cols: set[str]) -> Path:
    in_data = json.loads(in_file.read_text())
    out_data = [
        {key: item[key] for key, value in item.items() if key not in del_cols}
        for item in in_data
    ]

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        json.dump(out_data, f)
        path = f.name

    return Path(path)
