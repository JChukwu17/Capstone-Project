#!/usr/bin/env python3
"""Run the FreshMart data pipeline end to end.

Usage:
    .venv/Scripts/python.exe scripts/run_pipeline.py

Steps:
1. Load and clean the CSV.
2. Print summary statistics.
3. (Optionally) open/write to the database and query back the top 10 rows.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on sys.path when run directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import DB_PATH, DB_DRIVER
from src.data_loader import load_and_clean
from src.analysis import summary, by_category
from src.database import _get_connection, init_db, upsert_products, query_products


def main() -> int:
    print("=== FreshMart Product Data Pipeline ===\n")

    # 1. Load and clean
    print("[1/4] Loading and cleaning CSV …")
    df = load_and_clean()
    print(f"      Loaded {len(df)} products across {df['Category'].nunique()} categories\n")

    # 2. Summary
    print("[2/4] Summary statistics …")
    s = summary(df)
    for k, v in s.items():
        if isinstance(v, float):
            print(f"      {k:24}: {v:,.2f}")
        else:
            print(f"      {k:24}: {v}")
    print()

    print("[3/4] Category breakdown …")
    cat = by_category(df)
    # Print a compact table
    header = f"{'Category':<14} {'Count':>6} {'AvgPrice':>10} {'TotalQty':>10} {'TotalValue':>12}"
    print(header)
    print("-" * len(header))
    for _, r in cat.iterrows():
        print(f"{r['Category']:<14} {r['product_count']:>6} {r['avg_price']:>10.2f} {r['total_stock_quantity']:>10,.0f} {r['total_stock_value']:>12,.2f}")
    print()

    # 4. Database
    print(f"[4/4] Writing to {DB_DRIVER.upper()} database at {DB_PATH} …")
    conn = _get_connection()
    try:
        init_db(conn)
        n = upsert_products(conn, df)
        print(f"      Upserted {n} rows into the products table\n")

        print("      Top 10 products by stock value:")
        top = query_products(conn)
        for _, r in top.iterrows():
            print(f"        {r['product_name']:<20} {r['category']:<12} ${r['price']:>7.2f}  qty {int(r['stock_quantity']):>5}  value ${r['stock_value']:>9,.2f}")
    finally:
        if DB_DRIVER == "sqlite":
            conn.close()
        else:
            conn.close()

    print("\n=== Pipeline complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
