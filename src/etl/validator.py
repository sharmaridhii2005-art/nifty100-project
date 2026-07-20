import os
import pandas as pd

VALIDATION_FILE = "output/validation_failures.csv"


def get_df():
    return pd.read_csv(VALIDATION_FILE)


def test_validation_file_exists():
    assert os.path.exists(VALIDATION_FILE)


def test_validation_file_not_empty():
    assert len(get_df()) > 0


def test_required_columns_exist():
    df = get_df()
    expected = ["Rule", "Table", "Issue", "Severity"]
    for col in expected:
        assert col in df.columns


def test_rule_column_not_null():
    assert get_df()["Rule"].notna().all()


def test_severity_values():
    assert get_df()["Severity"].isin(["CRITICAL", "WARNING"]).all()


def test_issue_column_not_null():
    assert get_df()["Issue"].notna().all()


def test_table_column_not_null():
    assert get_df()["Table"].notna().all()


def test_rule_prefix():
    assert get_df()["Rule"].str.startswith("DQ-").all()


def test_dataframe_has_columns():
    assert len(get_df().columns) == 4


def test_dataframe_has_rows():
    assert len(get_df()) > 0