"""Database layer for the FreshMart pipeline.

Supports SQLite (default, zero-setup) and PostgreSQL (when configured via
environment variables). The public API is driver-agnostic: callers use
init_db, upsert_products, and query_products without knowing which backend
is active.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DB_DRIVER, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT


def _get_connection() -> Any:
    """Open and return a connection to the configured database.

    Returns:
        sqlite3.Connection when DRIVER == 'sqlite'.
        psycopg2 connection otherwise (requires psycopg2-binary installed).
    """
    if DB_DRIVER == "sqlite":
        path = Path(DB_NAME)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # PostgreSQL path
    try:
        import psycopg2
    except ImportError:
        raise RuntimeError(
            "PostgreSQL driver requested but psycopg2-binary is not installed. "
            "Run: pip install psycopg2-binary"
        )
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.autocommit = False
    return conn


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,          -- ignored for SQLite; see below
    product_name VARCHAR(255),
    category VARCHAR(100),
    price NUMERIC,
    stock_quantity INT,
    stock_value NUMERIC
);
"""

CREATE_TABLE_SQLITE = """
CREATE TABLE IF NOT EXISTS products (
    product_name TEXT,
    category TEXT,
    price REAL,
    stock_quantity INTEGER,
    stock_value REAL
);
"""


def init_db(conn: Any) -> None:
    """Create the products table if it does not already exist.

    Args:
        conn: Database connection from _get_connection().
    """
    if DB_DRIVER == "sqlite":
        conn.execute(CREATE_TABLE_SQLITE)
    else:
        conn.cursor().execute(CREATE_TABLE_SQL)
    conn.commit()


def upsert_products(conn: Any, df: pd.DataFrame) -> int:
    """Insert (or replace) all rows from a DataFrame into the products table.

    For SQLite we use INSERT OR REPLACE on a natural key (product_name, category)
    so re-running the pipeline is idempotent. For PostgreSQL we use ON CONFLICT
    on the same key.

    Args:
        conn: Database connection from _get_connection().
        df: Cleaned DataFrame with columns ProductName, Category, Price,
            StockQuantity, StockValue.

    Returns:
        Number of rows inserted/updated.
    """
    required = {"ProductName", "Category", "Price", "StockQuantity", "StockValue"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing columns: {missing}")

    rows = df[["ProductName", "Category", "Price", "StockQuantity", "StockValue"]].copy()
    # Round to avoid floating-point noise in the DB
    for col in ["Price", "StockValue"]:
        rows[col] = rows[col].round(2)

    count = 0
    if DB_DRIVER == "sqlite":
        conn.execute("DELETE FROM products")  # simple idempotent strategy for a capstone
        for _, r in rows.iterrows():
            conn.execute(
                "INSERT INTO products (product_name, category, price, stock_quantity, stock_value) "
                "VALUES (?, ?, ?, ?, ?)",
                (r["ProductName"], r["Category"], r["Price"], int(r["StockQuantity"]), r["StockValue"]),
            )
        conn.commit()
        count = len(rows)
    else:
        cur = conn.cursor()
        cur.execute("DELETE FROM products")
        for _, r in rows.iterrows():
            cur.execute(
                """INSERT INTO products (product_name, category, price, stock_quantity, stock_value)
                   VALUES (%s, %s, %s, %s, %s)
                   ON CONFLICT (product_name, category) DO UPDATE SET
                       price = EXCLUDED.price,
                       stock_quantity = EXCLUDED.stock_quantity,
                       stock_value = EXCLUDED.stock_value""",
                (r["ProductName"], r["Category"], r["Price"], int(r["StockQuantity"]), r["StockValue"]),
            )
        conn.commit()
        count = cur.rowcount if cur.rowcount > 0 else len(rows)

    return count


def query_products(conn: Any, sql: str = "SELECT * FROM products ORDER BY stock_value DESC LIMIT 10") -> pd.DataFrame:
    """Run an arbitrary SELECT and return results as a DataFrame.

    Args:
        conn: Database connection from _get_connection().
        sql: SQL query to execute.

    Returns:
        DataFrame of query results.
    """
    if DB_DRIVER == "sqlite":
        cur = conn.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
    else:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=columns) if columns else pd.DataFrame()
