import os
import pandas as pd


VALIDATION_FILE = "output/validation_failures.csv"


def test_validation_file_exists():
    assert os.path.exists(VALIDATION_FILE)


def test_validation_file_not_empty():
    df = pd.read_csv(VALIDATION_FILE)
    assert len(df) > 0


def test_required_columns_exist():
    df = pd.read_csv(VALIDATION_FILE)

    expected = ["Rule", "Table", "Issue", "Severity"]

    for col in expected:
        assert col in df.columns


def test_rule_column_not_null():
    df = pd.read_csv(VALIDATION_FILE)
    assert df["Rule"].notna().all()


def test_severity_values():
    df = pd.read_csv(VALIDATION_FILE)

    valid = ["CRITICAL", "WARNING"]

    assert df["Severity"].isin(valid).all()