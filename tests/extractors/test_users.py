import pandas as pd
import pytest
from extractor.extractors.users import load_users


@pytest.fixture()
def users_df(datadir):
    return load_users(datadir / "users.json")


def test_user_load(datadir, users_df):
    expected_df = pd.read_json(datadir / "users_df_out.json", orient="table")
    assert users_df.equals(expected_df)
