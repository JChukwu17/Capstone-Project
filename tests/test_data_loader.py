"""Tests for the FreshMart data pipeline."""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_loader import clean, load_csv
from src.config import CSV_PATH, FILL_VALUE


@pytest.fixture
def raw_df():
    """Load the real CSV once per session for fast repeated tests."""
    return load_csv()


def test_csv_exists():
    assert CSV_PATH.exists(), f"CSV missing at {CSV_PATH}"


def test_load_csv_returns_205_rows(raw_df):
    assert len(raw_df) == 205


def test_clean_preserves_row_count_with_default_fill(raw_df):
    """Default fill preserves all rows (missing numerics filled with config.FILL_VALUE)."""
    expected_rows = len(raw_df)  # 205
    df = clean(raw_df)
    assert len(df) == expected_rows
    # The real CSV has rows with missing Price/StockQuantity; verify fill landed
    assert (df["Price"] == FILL_VALUE).any() or (df["StockQuantity"] == FILL_VALUE).any()


def test_clean_stock_value_derived(raw_df):
    df = clean(raw_df)
    row = df.iloc[0]
    expected = round(row["Price"] * row["StockQuantity"], 2)
    assert abs(row["StockValue"] - expected) < 0.01


def test_clean_numeric_coercion(raw_df):
    df = clean(raw_df)
    for col in ["Price", "StockQuantity", "StockValue"]:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_clean_string_stripped(raw_df):
    df = clean(raw_df)
    assert df["ProductName"].iloc[0] == df["ProductName"].iloc[0].strip()
    assert df["Category"].iloc[0] == df["Category"].iloc[0].strip()


def test_clean_fill_value_respected(raw_df):
    df = raw_df.copy()
    df.loc[0, "Price"] = float("nan")
    cleaned = clean(df, fill=-1.0)
    assert cleaned.loc[0, "Price"] == -1.0


def test_clean_category_normalisation_applied(raw_df):
    """Known misspellings/casing variants are mapped to canonical categories."""
    df = clean(raw_df)
    # Three orphaned categories in the raw CSV should be folded into their canonical form
    assert "dairy" not in df["Category"].unique()
    assert "Bevarages" not in df["Category"].unique()
    assert "snakcs" not in df["Category"].unique()
    # Now we should have exactly 5 distinct categories
    assert df["Category"].nunique() == 5
    assert set(df["Category"].unique()) == {"Beverages", "Produce", "Dairy", "Bakery", "Snacks"}


def test_clean_drop_on_none_drops_rows(raw_df):
    """Passing fill=None drops rows with any missing numeric value.

    The real CSV has some rows with missing Price/StockQuantity; we inject one
    more and verify the total drop reflects all missing rows.
    """
    # Count how many rows already have a missing numeric in the raw CSV
    already_missing = int(
        raw_df[["Price", "StockQuantity"]].isna().any(axis=1).sum()
    )
    df = raw_df.copy()
    # Remember the original row 0's identity
    original_id = int(df.loc[0, "ProductID"])
    df.loc[0, "Price"] = float("nan")
    cleaned = clean(df, fill=None)
    expected_rows = len(raw_df) - already_missing - 1
    assert len(cleaned) == expected_rows
    # The injected NaN row (ProductID == original_id) should no longer be present
    assert int(cleaned["ProductID"].iloc[0]) != original_id
    assert not (cleaned["ProductID"] == original_id).any()
