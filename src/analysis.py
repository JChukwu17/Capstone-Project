"""Exploratory analysis helpers for the FreshMart products dataset.

Provides summary statistics and category-level aggregations that mirror
the notebook EDA but are now reusable and testable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def summary(df: pd.DataFrame) -> dict:
    """Return a dictionary of high-level summary statistics.

    Mirrors the notebook cells:
    - Average price
    - Total stock quantity
    - Total stock value
    - Number of products
    - Number of categories
    """
    return {
        "num_products": int(len(df)),
        "num_categories": int(df["Category"].nunique()),
        "avg_price": float(df["Price"].mean()),
        "total_stock_quantity": float(df["StockQuantity"].sum()),
        "total_stock_value": float(df["StockValue"].sum()),
        "min_price": float(df["Price"].min()),
        "max_price": float(df["Price"].max()),
    }


def by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product stats grouped by Category.

    Returns a DataFrame with columns:
    Category, product_count, avg_price, total_stock_quantity,
    total_stock_value, avg_stock_value_per_product
    """
    agg = df.groupby("Category").agg(
        product_count=("ProductID", "count"),
        avg_price=("Price", "mean"),
        total_stock_quantity=("StockQuantity", "sum"),
        total_stock_value=("StockValue", "sum"),
    ).reset_index()

    agg["avg_stock_value_per_product"] = agg["total_stock_value"] / agg["product_count"]
    return agg.sort_values("total_stock_value", ascending=False).reset_index(drop=True)


def price_buckets(df: pd.DataFrame, bins: int = 5) -> pd.DataFrame:
    """Bin products into price buckets and count per bucket.

    Returns a DataFrame with columns: price_min, price_max, count.
    """
    # Build bin edges from quantiles for even population buckets
    edges = df["Price"].quantile(q=np.linspace(0, 1, bins + 1)).tolist()
    # Avoid duplicate edges when many products share a price
    edges = sorted(set(edges))
    if len(edges) < 2:
        edges = [df["Price"].min(), df["Price"].max()]
    df_tmp = df.copy()
    df_tmp["bucket"] = pd.cut(df_tmp["Price"], bins=edges, include_lowest=True)
    counts = df_tmp.groupby("bucket", observed=False).size().reset_index(name="count")
    counts["price_min"] = counts["bucket"].apply(lambda b: b.left if pd.notna(b) else None)
    counts["price_max"] = counts["bucket"].apply(lambda b: b.right if pd.notna(b) else None)
    return counts[["price_min", "price_max", "count"]].sort_values("price_min").reset_index(drop=True)
