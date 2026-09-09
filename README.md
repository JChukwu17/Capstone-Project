# FreshMart Product Data Pipeline

![CI](https://github.com/JChukwu17/Capstone-Project/actions/workflows/ci.yml/badge.svg)

A small end-to-end data pipeline that loads a retail product catalogue, cleans and enriches it, runs exploratory analysis, and persists the results to a database. Built as a capstone project demonstrating data engineering practice: modular code, automated testing, CI, and reproducible visualisations.

## What it does

The pipeline has four stages, each implemented as a reusable module in `src/`:

1. **Load** — reads `data/raw/freshmart_products_csv.csv` (205 products, 6 columns: ProductID, ProductName, Category, Price, StockQuantity, StockValue).
2. **Clean** — strips whitespace, coerces numeric columns, derives `StockValue = Price × StockQuantity`, fixes known category misspellings, and fills or drops missing values.
3. **Analyse** — summary statistics (average price, total stock, total value, min/max) and a category-level breakdown.
4. **Persist** — writes the cleaned data to a database and queries back the top products by stock value.

Running the pipeline end-to-end is a single command: `scripts/run_pipeline.py`.

## Quick start

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt

# 2. Run the pipeline
.venv/Scripts/python.exe scripts/run_pipeline.py

# 3. (Optional) regenerate the charts
.venv/Scripts/python.exe scripts/export_charts.py

# 4. (Optional) run the tests
.venv/Scripts/python.exe -m pytest tests/ -v
```

On first run the SQLite database is created automatically at `data/processed/freshmart.db`.

## Pipeline output

Running the pipeline prints the full summary to the terminal:

```
=== FreshMart Product Data Pipeline ===

[1/4] Loading and cleaning CSV …
      Loaded 205 products across 5 categories

[2/4] Summary statistics …
      num_products            : 205
      num_categories          : 5
      avg_price               : 23.88
      total_stock_quantity    : 52,805.00
      total_stock_value       : 1,210,530.33
      min_price               : 1.04
      max_price               : 49.51

[3/4] Category breakdown …
Category        Count   AvgPrice   TotalQty   TotalValue
--------------------------------------------------------
Beverages          44      24.17     11,920   288,544.42
Snacks             39      25.22     10,735   280,640.10
Produce            42      23.72     10,073   228,533.54
Bakery             38      22.35      9,960   211,947.61
Dairy              42      23.88     10,117   200,864.66

[4/4] Writing to SQLite database at data/processed/freshmart.db …
      Upserted 205 rows into the products table

      Top 10 products by stock value:
        Carrot 105           Produce      $  49.19  qty   479  value $23,562.01
        Carrot 157           Produce      $  47.08  qty   486  value $22,880.88
        Granola Bar 171      Snacks       $  49.51  qty   459  value $22,725.09
        ...

=== Pipeline complete ===
```

## Data quality

The raw CSV contains three category variants that are normalised automatically during cleaning:

| Raw value | Canonical | Issue      |
|-----------|-----------|------------|
| `dairy`   | `Dairy`   | lowercase  |
| `Bevarages` | `Beverages` | typo   |
| `snakcs`  | `Snacks`  | typo       |

The mapping lives in `src/config.py` (`CATEGORY_NORMALISATION`) and is applied by `src/data_loader.clean()`. After cleaning the dataset has 5 distinct categories: Beverages, Snacks, Produce, Bakery, Dairy.

Note: 10 rows in the raw CSV have missing `Price` or `StockQuantity`. By default the pipeline fills these with `-1` (configurable via `FRESHMART_FILL_VALUE`) to preserve all 205 rows. Pass `fill=None` to `clean()` to drop those rows instead.

## Visualisation

The project ships four charts (in `assets/`) rendered from `src/visualise.py` and shown inline in `notebooks/exploration.ipynb`. All charts share one colour palette defined in `src/config.py`.

### Colour palette

Category colours use the **Okabe-Ito palette** (Okabe & Ito, 2002) — the recognised colourblind-safe palette. All five colours remain distinguishable under protanopia, deuteranopia, and tritanopia, and retain contrast in greyscale print. The assignment below is by total stock value (descending) so the palette order carries business priority across charts.

| Category | Colour | Hex |
|----------|--------|-----|
| Beverages | orange | `#E69F00` |
| Snacks | sky blue | `#56B4E9` |
| Produce | bluish green | `#009E73` |
| Bakery | vermillion | `#D55E00` |
| Dairy | reddish purple | `#CC79A7` |

A neutral dark grey (`#333333`) is used as the single **accent** for non-categorical elements: mean reference lines, the top-10 ranking bars, and annotation text. It is deliberately chosen to never collide with any category colour.

The palette is:

- **Defined once** in `src/config.py` (`CATEGORY_COLORS`, `PLOT_ACCENT`, `CATEGORY_ORDER`).
- **Showcased** in the notebook as a swatch cell so the reader sees the mapping up front.
- **Consumed** by every function in `src/visualise.py` via `CATEGORY_COLORS.get(category, PLOT_ACCENT)`, so adding a new chart cannot introduce an inconsistent colour.

### Charts

| File | Chart | What it answers |
|------|-------|-----------------|
| `assets/chart_price_distribution.png` | Histogram + KDE of product prices | What does the price landscape look like? |
| `assets/chart_category_comparison.png` | Three-panel bar chart (count, avg price, total value) | Which categories matter, and by which metric? |
| `assets/chart_value_vs_price.png` | Scatter of stock value vs. price, coloured by category | Is value driven by price or quantity? |
| `assets/chart_top_products.png` | Horizontal bar — top 10 by stock value | Which individual products hold the most inventory value? |
| `assets/palette_swatch.png` | Colour palette swatch | What is the shared legend? |

To regenerate the charts:

```bash
.venv/Scripts/python.exe scripts/export_charts.py
```

The `data/processed/freshmart.db` file is a generated artifact and is git-ignored; the `assets/*.png` files are tracked deliverables.

## Database

The pipeline defaults to **SQLite** — a file-based database that needs no server, no credentials, and no setup. The database file is written to `data/processed/freshmart.db` on first run.

To switch to PostgreSQL, set these environment variables (see `.env.example`) and install `psycopg2-binary`:

```bash
pip install psycopg2-binary
FRESHMART_DB_DRIVER=postgresql FRESHMART_DB_NAME=freshmart \
FRESHMART_DB_USER=postgres \
FRESHMART_DB_PASSWORD=your_password \
FRESHMART_DB_HOST=localhost \
FRESHMART_DB_PORT=5432 \
.venv/Scripts/python.exe scripts/run_pipeline.py
```

The database layer in `src/database.py` is driver-agnostic — callers use `init_db`, `upsert_products`, and `query_products` without knowing which backend is active.

## Project structure

```
Capstone-Project/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI (pytest + pipeline + charts)
├── assets/                     # Chart PNGs (tracked deliverables)
│   ├── palette_swatch.png
│   ├── chart_price_distribution.png
│   ├── chart_category_comparison.png
│   ├── chart_value_vs_price.png
│   └── chart_top_products.png
├── data/
│   ├── raw/                 # freshmart_products_csv.csv (source data)
│   └── processed/           # freshmart.db (generated, git-ignored)
├── notebooks/
│   └── exploration.ipynb    # exploratory Jupyter notebook (with outputs)
├── src/
│   ├── __init__.py
│   ├── config.py            # paths, DB params, cleaning config, colour palette
│   ├── data_loader.py       # CSV load + cleaning logic (with category normalisation)
│   ├── analysis.py          # summary stats + category breakdown + price buckets
│   ├── visualise.py         # plotting helpers (uses config colour palette)
│   └── database.py          # SQLite/PostgreSQL connection, upsert, query
├── tests/
│   └── test_data_loader.py  # 9 unit tests for cleaning logic
├── scripts/
│   ├── run_pipeline.py      # CLI entry point (load → clean → analyse → persist)
│   └── export_charts.py     # chart export to assets/
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

## CI

The project uses GitHub Actions for continuous integration. The workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. Checks out the repository
2. Sets up Python 3.11
3. Installs dependencies from `requirements.txt`
4. Runs the unit tests (`pytest tests/ -v`)
5. Runs the pipeline as a smoke test (`scripts/run_pipeline.py`)
6. Runs the chart export as a smoke test (`scripts/export_charts.py`)
7. Verifies all five chart PNGs were produced in `assets/`

![CI](https://github.com/JChukwu17/Capstone-Project/actions/workflows/ci.yml/badge.svg)

Both CI runs to date have passed (2026-09-09). The workflow file is validated YAML and follows GitHub Actions best practices: checkout@v4, setup-python@v5, ubuntu-latest.

## Testing

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

The test suite (`tests/test_data_loader.py`) covers:

- CSV file existence and row count (205 rows)
- Row preservation with default fill (all 205 rows kept)
- `StockValue` derivation correctness (`Price × StockQuantity`)
- Numeric column coercion
- String whitespace stripping
- Fill value application
- Category normalisation (3 misspellings folded into 5 canonical categories)
- Row dropping when `fill=None`

All 9 tests pass.

## Requirements

- Python 3.11
- pandas ≥ 2.0, < 3.1
- numpy ≥ 1.24
- pytest ≥ 7.0
- seaborn ≥ 0.12
- matplotlib ≥ 3.6

Optional for PostgreSQL: `psycopg2-binary`.

See `requirements.txt` for the pinned versions and `.env.example` for the environment variables.

## License

Personal capstone project — all rights reserved.

## Live demo

The project is showcased on my portfolio site: [jchukwu17.github.io/Professional-portfolio](https://jchukwu17.github.io/Professional-portfolio/) — see the **Work** section for the FreshMart entry, including the price-distribution chart.
