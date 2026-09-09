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

# ---------------------------------------------------------------------------
# Plotting — colour palette (single source of truth for all charts)
# ---------------------------------------------------------------------------
# Category colours use the Okabe-Ito palette (Okabe & Ito, 2002) — the
# recognised colourblind-safe palette.  All five colours remain distinguishable
# under protanopia, deuteranopia, and tritanopia, and retain contrast in
# greyscale print.  The mapping is arbitrary (colour does not encode category
# semantics); the assignment is fixed here and described in README.md so every
# chart shares one consistent legend.
#
# Order: sorted by total stock value descending (Beverages, Snacks, Produce,
# Bakery, Dairy) so that iterating the dict yields business-priority order.
CATEGORY_COLORS: dict[str, str] = {
    "Beverages": "#E69F00",  # orange
    "Snacks":    "#56B4E9",  # sky blue
    "Produce":   "#009E73",  # bluish green
    "Bakery":    "#D55E00",  # vermillion
    "Dairy":     "#CC79A7",  # reddish purple
}

# Single accent colour for non-categorical emphasis (mean line, top-10
# ranking bars, reference elements).  A neutral dark grey is chosen so it
# can never collide with any CATEGORY_COLORS entry, even if more categories
# are added later.  Must read well on white and in greyscale print.
PLOT_ACCENT = "#333333"

# Ordered list of category names by total stock value (descending) — used to
# fix bar/legend ordering across all charts so the eye tracks a category
# consistently from one chart to the next.
CATEGORY_ORDER: list[str] = list(CATEGORY_COLORS.keys())

# Matplotlib style tweaks applied once at the top of any plotting script.
# Kept minimal here; the visualisation functions apply them explicitly.
PLOT_STYLE: dict[str, str] = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#666666",
    "axes.labelcolor": "#222222",
    "axes.titlecolor": "#222222",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "grid.color": "#E5E5E5",
    "text.color": "#222222",
}
