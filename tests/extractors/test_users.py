import pandas as pd
import pytest
from extractor.extractors.users import load_users
from helpers.file import json_without_cols


@pytest.fixture()
def users_df(datadir):
    return load_users(datadir / "users.json")


def test_user_load(datadir, users_df):
    expected_df = pd.read_json(datadir / "users_df_out.json", orient="table")
    assert users_df.equals(expected_df)


def test_no_yoast_columns(datadir):
    path = json_without_cols(datadir / "users.json", {"yoast_head", "yoast_head_json"})
    users_df = load_users(path)
    assert users_df.iloc[0].avatar is None
