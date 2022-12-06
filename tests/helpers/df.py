import pandas as pd


def ordered_col(values):
    return pd.Series(values, index=range(1, len(values) + 1))
