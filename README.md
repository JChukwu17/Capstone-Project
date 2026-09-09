# FreshMart Product Data Pipeline

A small end-to-end data pipeline that loads a retail product catalogue, cleans and enriches it, runs exploratory analysis, and persists the results to a database.

## What it does

1. **Load** — reads `data/raw/freshmart_products_csv.csv` (205 products, 6 columns).
2. **Clean** — strips whitespace, coerces numeric columns, derives `StockValue = Price × StockQuantity`, fills or drops missing values.
3. **Analyse** — summary statistics (avg price, total stock, total value) and a category-level breakdown.
4. **Persist** — writes the cleaned data to a database and queries back the top products by stock value.

## Data quality

The raw CSV contains three category variants that are normalised automatically during cleaning:

| Raw value | Canonical | Issue      |
|-----------|-----------|------------|
| `dairy`   | `Dairy`   | lowercase  |
| `Bevarages` | `Beverages` | typo   |
| `snakcs`  | `Snacks`  | typo       |

The mapping lives in `src/config.py` (`CATEGORY_NORMALISATION`) and is applied by `src/data_loader.clean()`. After cleaning the dataset has 5 distinct categories.

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
FRESHMART_DB_DRIVER=postgresql FRESHMART_DB_NAME=freshmart \  # etc.
```

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

On first run the SQLite database is created automatically.

## Project structure

```
Capstone-Project/
├── assets/                   # Chart PNGs (tracked deliverables)
│   ├── palette_swatch.png
│   ├── chart_price_distribution.png
│   ├── chart_category_comparison.png
│   ├── chart_value_vs_price.png
│   └── chart_top_products.png
├── data/
│   ├── raw/                 # freshmart_products_csv.csv
│   └── processed/           # freshmart.db (generated, git-ignored)
├── notebooks/               # exploratory Jupyter notebook
│   └── exploration.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py            # paths, DB params, cleaning config, colour palette
│   ├── data_loader.py       # CSV load + cleaning logic
│   ├── analysis.py          # summary stats + category breakdown
│   ├── visualise.py         # plotting helpers (uses config colour palette)
│   └── database.py          # SQLite/PostgreSQL connection, upsert, query
├── tests/
│   └── test_data_loader.py  # unit tests for cleaning logic
├── scripts/
│   ├── run_pipeline.py      # CLI entry point
│   └── export_charts.py     # chart export to assets/
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
```

## Running tests

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

## License

Personal capstone project — all rights reserved.
