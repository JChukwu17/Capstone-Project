#!/usr/bin/env python3
"""Render the project's visualisation charts to PNG files.

Each chart is produced by a function in src/visualise.py and saved to
assets/.  Charts are tracked in version control (unlike the SQLite DB).

Usage:
    .venv/Scripts/python.exe scripts/export_charts.py

Output (assets/):
    palette_swatch.png          Category colour palette swatch
    chart_price_distribution.png   Plot 1 — price histogram + KDE
    chart_category_comparison.png  Plot 2 — three-panel category breakdown
    chart_value_vs_price.png      Plot 3 — scatter, value vs. price
    chart_top_products.png        Plot 4 — top 10 products by stock value
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on sys.path when run directly
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data_loader import load_and_clean
from src.visualise import (
    plot_price_distribution,
    plot_category_comparison,
    plot_value_vs_price,
    plot_top_products,
)


def main() -> int:
    print("=== FreshMart chart export ===")

    df = load_and_clean()
    df_plot = df.loc[df["Price"] > 0].copy()
    print(f"Loaded {len(df)} rows; {len(df_plot)} used for charts "
          f"(rows with Price <= 0 excluded)")

    out_dir = ROOT / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[tuple[str, plt.Figure]] = []

    # Palette swatch
    from src.config import CATEGORY_COLORS, CATEGORY_ORDER, PLOT_ACCENT
    import matplotlib.patches as mpatches
    fig, ax = plt.subplots(figsize=(8, 1.5))
    ax.set_xlim(0, len(CATEGORY_ORDER) + 1.2)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, cat in enumerate(CATEGORY_ORDER):
        ax.add_patch(
            mpatches.Rectangle(
                (i, 0.25), 0.85, 0.5,
                facecolor=CATEGORY_COLORS[cat],
                edgecolor="white",
                linewidth=1.5,
            )
        )
        ax.text(i + 0.425, 0.12, cat, ha="center", va="center",
                fontsize=9, color="#333333")
    ax.text(len(CATEGORY_ORDER) + 0.15, 0.5, f"accent: {PLOT_ACCENT}",
            ha="left", va="center", fontsize=9, color=PLOT_ACCENT)
    ax.set_title(
        "Category colour palette — Okabe & Ito (2002), colourblind-safe",
        fontsize=11, loc="left", pad=10,
    )
    plt.tight_layout()
    outputs.append(("palette_swatch.png", fig))

    # Chart 1
    fig = plot_price_distribution(df_plot)
    outputs.append(("chart_price_distribution.png", fig))

    # Chart 2
    fig = plot_category_comparison(df)
    outputs.append(("chart_category_comparison.png", fig))

    # Chart 3
    fig = plot_value_vs_price(df_plot)
    outputs.append(("chart_value_vs_price.png", fig))

    # Chart 4
    fig = plot_top_products(df_plot, n=10)
    outputs.append(("chart_top_products.png", fig))

    written = 0
    for name, fig in outputs:
        path = out_dir / name
        fig.savefig(str(path), dpi=150, bbox_inches="tight")
        plt.close(fig)
        written += 1
        print(f"  wrote {path.name} ({path.stat().st_size // 1024} KB)")

    print(f"\nWrote {written} charts to {out_dir}")
    print("=== Done ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
