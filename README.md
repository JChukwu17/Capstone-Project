# FreshMart Product Data Pipeline

A small end-to-end data pipeline that loads a retail product catalogue, cleans and enriches it, runs exploratory analysis, and persists the results to a database.

## What it does

1. **Load** — reads `data/raw/freshmart_products_csv.csv` (205 products, 6 columns).
2. **Clean** — strips whitespace, coerces numeric columns, derives `StockValue = Price × StockQuantity`, fills or drops missing values.
3. **Analyse** — summary statistics (avg price, total stock, total value) and a category-level breakdown.
4. **Persist** — writes the cleaned data to a database and queries back the top products by stock value.

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
```

On first run the SQLite database is created automatically.

## Project structure

```
Capstone-Project/
├── data/
│   ├── raw/                  # freshmart_products_csv.csv
│   └── processed/            # freshmart.db (generated)
├── notebooks/                # exploratory Jupyter notebook (optional)
├── src/
│   ├── __init__.py
│   ├── config.py             # paths, DB params, cleaning config
│   ├── data_loader.py        # CSV load + cleaning logic
│   ├── analysis.py           # summary stats + category breakdown
│   └── database.py           # SQLite/PostgreSQL connection, upsert, query
├── tests/
│   └── test_data_loader.py   # unit tests for cleaning logic
├── scripts/
│   └── run_pipeline.py       # CLI entry point
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
