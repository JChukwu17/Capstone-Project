"""Data loading and cleaning for the FreshMart products CSV.

Responsibilities:
- Load the raw CSV into a pandas DataFrame.
- Coerce numeric columns, fill or drop missing values.
- Derive StockValue = Price * StockQuantity when not already present.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path

from .config import CSV_PATH, NUMERIC_COLUMNS, FILL_VALUE

# Sentinel used to distinguish "caller passed fill=None to request dropping"
# from "caller did not pass fill and we should use the config default".
_DROP = object()


def load_csv(path: Path | None = None) -> pd.DataFrame:
    """Load the raw FreshMart products CSV.

    Args:
        path: Path to the CSV file. Defaults to config.CSV_PATH.

    Returns:
        Raw DataFrame as read from disk.
    """
    csv_path = path or CSV_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found at {csv_path}")
    df = pd.read_csv(csv_path)
    return df


def clean(df: pd.DataFrame, fill: float | None = _DROP) -> pd.DataFrame:
    """Clean and normalise the FreshMart products DataFrame.

    - Strips whitespace from string columns.
    - Coerces Price, StockQuantity, StockValue to numeric.
    - Derives StockValue = Price * StockQuantity if missing or all-null.
    - Fills missing numeric values with `fill` if provided.
      If `fill` is None, rows with any missing numeric value are dropped.
      If `fill` is omitted (default), config.FILL_VALUE is used (preserves rows).

    Args:
        df: Raw DataFrame from load_csv().
        fill: Value to use for missing numeric entries, or None to drop rows
            with missing values, or omitted to use config.FILL_VALUE.

    Returns:
        Cleaned DataFrame with consistent dtypes and a populated StockValue.
    """
    # Resolve fill strategy: explicit None -> drop, _DROP sentinel -> config default
    if fill is _DROP:
        fill_value: float | None = FILL_VALUE
    else:
        fill_value = fill  # may be None (drop) or a float (fill)

    # Normalise string columns
    for col in ["ProductName", "Category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Coerce numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Derive StockValue if missing or entirely null
    if "StockValue" not in df.columns or df["StockValue"].isna().all():
        df["StockValue"] = df["Price"] * df["StockQuantity"]
    else:
        # Repopulate any nulls that resulted from coercion
        mask = df["StockValue"].isna() & df["Price"].notna() & df["StockQuantity"].notna()
        df.loc[mask, "StockValue"] = df.loc[mask, "Price"] * df.loc[mask, "StockQuantity"]

    # Handle missing numerics
    if fill_value is None:
        before = len(df)
        df = df.dropna(subset=NUMERIC_COLUMNS)
        dropped = before - len(df)
        if dropped:
            print(f"Dropped {dropped} rows with missing numeric values")
    else:
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = df[col].fillna(fill_value)

    return df.reset_index(drop=True)


def load_and_clean(path: Path | None = None, fill: float | None = _DROP) -> pd.DataFrame:
    """Convenience: load_csv() then clean().

    Args:
        path: Optional path to the CSV (defaults to config.CSV_PATH).
        fill: Passed through to clean(). Omit to use config.FILL_VALUE (preserve
            all rows). Pass None to drop rows with missing numeric values.
    """
    return clean(load_csv(path), fill=fill)
