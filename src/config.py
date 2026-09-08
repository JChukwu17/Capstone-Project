"""Configuration for the FreshMart pipeline.

Reads from environment variables with sensible defaults so the project
runs out of the box with SQLite and no external database required.
"""

from pathlib import Path
import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = ROOT / "data" / "raw"
PROCESSED_DATA_DIR = ROOT / "data" / "processed"

# CSV source — placed in data/raw/ by convention
CSV_PATH = RAW_DATA_DIR / "freshmart_products_csv.csv"

# SQLite database file (file-based, no server needed)
DB_PATH = PROCESSED_DATA_DIR / "freshmart.db"

# ---------------------------------------------------------------------------
# Database — defaults to SQLite; swap to PostgreSQL by changing DRIVER
# ---------------------------------------------------------------------------
DB_DRIVER = os.getenv("FRESHMART_DB_DRIVER", "sqlite").lower()

if DB_DRIVER == "sqlite":
    DB_NAME = str(DB_PATH)
    DB_USER = ""
    DB_PASSWORD = ""
    DB_HOST = ""
    DB_PORT = ""
else:
    # PostgreSQL-compatible params (used when FRESHMART_DB_DRIVER=postgresql)
    DB_NAME = os.getenv("FRESHMART_DB_NAME", "freshmart")
    DB_USER = os.getenv("FRESHMART_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("FRESHMART_DB_PASSWORD", "password")
    DB_HOST = os.getenv("FRESHMART_DB_HOST", "localhost")
    DB_PORT = os.getenv("FRESHMART_DB_PORT", "5432")

# ---------------------------------------------------------------------------
# Data cleaning
# ---------------------------------------------------------------------------
# Columns that should be numeric; non-numeric values become NaN then filled.
NUMERIC_COLUMNS = ["Price", "StockQuantity", "StockValue"]

# Value to fill missing numeric entries with (None = drop rows instead).
FILL_VALUE = float(os.getenv("FRESHMART_FILL_VALUE", "-1"))

# Category normalisation: known misspellings / casing variants mapped to the
# canonical category name.  Add entries here as data-quality issues are found.
# Applied in data_loader.clean() after whitespace stripping.
CATEGORY_NORMALISATION: dict[str, str] = {
    "dairy": "Dairy",
    "Bevarages": "Beverages",
    "snakcs": "Snacks",
}
