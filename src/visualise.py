"""Plotting helpers for the FreshMart product dataset.

Each function takes a cleaned DataFrame (post data_loader.clean) and returns
a matplotlib Figure.  The notebook imports these for inline display; the
export script calls them and saves PNGs.

All colours come from src.config (CATEGORY_COLORS / PLOT_ACCENT) so every
chart shares one palette.  See README.md for the palette rationale.

Rows whose Price or StockValue equals the fill sentinel (-1.0) are excluded
from every chart, because the sentinel is a data-cleaning placeholder and
would otherwise render as nonsensical negative values.
"""

from __future__ import annotations

import numpy as np
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt

from .analysis import by_category
from .config import CATEGORY_COLORS, CATEGORY_ORDER, PLOT_ACCENT, PLOT_STYLE

if TYPE_CHECKING:
    pass


def _apply_style() -> None:
    """Apply the project's matplotlib style tweaks once."""
    plt.rcParams.update(PLOT_STYLE)


def _category_color(category: str) -> str:
    """Return the assigned colour for a category, falling back to accent."""
    return CATEGORY_COLORS.get(category, PLOT_ACCENT)


def _plot_df(df: pd.DataFrame) -> pd.DataFrame:
    """Return the subset of `df` used for plotting.

    Excludes rows whose Price or StockValue is the fill sentinel (<= 0),
    because those are data-cleaning placeholders rather than real values.
    """
    return df.loc[(df["Price"] > 0) & (df["StockValue"] > 0)].copy()


def plot_price_distribution(
    df: pd.DataFrame,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Histogram + KDE of product prices, with a mean reference line.

    Args:
        df: Cleaned DataFrame from data_loader.clean().
        ax: Optional Axes to draw on.  If None, a new figure is created.

    Returns:
        The matplotlib Figure (caller owns show/savefig).
    """
    _apply_style()
    prices = _plot_df(df)["Price"]
    if prices.empty:
        raise ValueError("No rows with Price > 0 to plot")

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.5))
    else:
        fig = ax.figure

    # Explicit, round bin width so the reader can interpret the x-axis.
    bin_width = 5.0
    bin_edges = np.arange(
        np.floor(prices.min() / bin_width) * bin_width,
        np.ceil(prices.max() / bin_width) * bin_width + bin_width,
        bin_width,
    )
    ax.hist(
        prices,
        bins=bin_edges,
        color=CATEGORY_COLORS["Produce"],
        alpha=0.55,
        edgecolor="white",
        linewidth=0.8,
        zorder=2,
    )

    # KDE overlay
    try:
        from seaborn import kdeplot
        kdeplot(prices, color=CATEGORY_COLORS["Snacks"], linewidth=2.0,
                ax=ax, zorder=3)
    except Exception:
        pass

    # Mean reference line — placed relative to a y-limit that definitely
    # clears the tallest bar.
    max_count = int(prices.value_counts(bins=bin_edges).max())
    y_max = max(ax.get_ylim()[1], max_count * 1.18)
    ax.set_ylim(0, y_max)
    ax.axvline(mean_price := float(prices.mean()),
               color=PLOT_ACCENT, linestyle="--", linewidth=1.4, zorder=4)
    ax.text(mean_price, y_max * 0.94, f" mean ${mean_price:.2f}",
            color=PLOT_ACCENT, fontsize=9, ha="left", va="top")

    # X range: 0 to a round number just above the maximum price.
    x_max = np.ceil(prices.max() / 10) * 10 + 10
    ax.set_xlim(0, x_max)

    ax.set_title("Distribution of product prices", fontsize=12, pad=10)
    ax.set_xlabel(f"Price (USD)  —  bins of ${bin_width:.0f}")
    ax.set_ylabel("Number of products")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return fig


def plot_category_comparison(
    df: pd.DataFrame,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Three-panel bar chart: product count, average price, total stock value.

    Panels share the same category order (by total stock value, descending)
    so the eye tracks a category across panels.  Category labels appear on
    every panel's x-axis.  Value labels sit on top of each bar.

    Args:
        df: Cleaned DataFrame from data_loader.clean().
        ax: Optional single Axes.  If None, a new 3-panel figure is created.
            If provided, the chart is drawn as a single panel (product count)
            for compact embedding.

    Returns:
        The matplotlib Figure.
    """
    _apply_style()
    agg = by_category(df)

    # Order by total stock value descending, matching CATEGORY_ORDER intent.
    agg = agg.set_index("Category").reindex(CATEGORY_ORDER).reset_index()

    if ax is None:
        fig, axes = plt.subplots(3, 1, figsize=(8, 9.5), sharex=True)
        axes = list(axes)
    else:
        fig = ax.figure
        axes = [ax]

    panel_specs = [
        ("Product count", "product_count", "count", "{:.0f}"),
        ("Average price (USD)", "avg_price", "avg_price", "${:.2f}"),
        ("Total stock value (USD)", "total_stock_value", "total_value", "${:,.0f}"),
    ]

    for ax_i, (title, col, _key, fmt) in zip(axes, panel_specs):
        colors = [_category_color(cat) for cat in agg["Category"]]
        bars = ax_i.bar(
            agg["Category"], agg[col],
            color=colors,
            edgecolor="white",
            linewidth=0.8,
            width=0.68,
            zorder=3,
        )
        ax_i.set_title(title, fontsize=11, pad=6)
        ax_i.spines[["top", "right"]].set_visible(False)
        ax_i.grid(axis="y", linewidth=0.7, zorder=0)

        vmax = agg[col].max()
        ax_i.set_ylim(0, vmax * 1.18)
        for bar, val in zip(bars, agg[col]):
            ax_i.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                " " + fmt.format(val),
                ha="center",
                va="bottom",
                fontsize=9,
                color="#222222",
            )

        ax_i.set_xticks(range(len(agg)))
        ax_i.set_xticklabels(agg["Category"], rotation=0, fontsize=9)
        ax_i.tick_params(labelbottom=True)

    fig.tight_layout(h_pad=2.5)
    return fig


def plot_value_vs_price(
    df: pd.DataFrame,
    ax: plt.Axes | None = None,
    annotate_top_n: int = 3,
) -> plt.Figure:
    """Scatter of stock value vs. unit price, coloured by category.

    Excludes rows with Price or StockValue <= 0 (fill sentinel).  Y-axis
    uses a log scale because the stock-value spread exceeds 10x.

    Args:
        df: Cleaned DataFrame from data_loader.clean().
        ax: Optional Axes to draw on.  If None, a new figure is created.
        annotate_top_n: Number of top stock-value products to label.

    Returns:
        The matplotlib Figure.
    """
    _apply_style()
    plot_df = _plot_df(df)[["ProductName", "Category", "Price", "StockValue"]]
    if plot_df.empty:
        raise ValueError("No rows with Price > 0 and StockValue > 0 to plot")

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 5))
    else:
        fig = ax.figure

    for category in CATEGORY_ORDER:
        sub = plot_df.loc[plot_df["Category"] == category]
        ax.scatter(
            sub["Price"],
            sub["StockValue"],
            color=_category_color(category),
            s=42,
            alpha=0.72,
            edgecolors="white",
            linewidths=0.5,
            label=category,
            zorder=3,
        )

    # Log y-axis whenever the real spread exceeds 10x.
    use_log = plot_df["StockValue"].min() > 0 and (
        plot_df["StockValue"].max() / plot_df["StockValue"].min() > 10
    )
    if use_log:
        ax.set_yscale("log")
        y_min = plot_df["StockValue"].min() * 0.8
        y_max = plot_df["StockValue"].max() * 1.4
        ax.set_ylim(y_min, y_max)
    else:
        y_min = 0
        y_max = plot_df["StockValue"].max() * 1.18
        ax.set_ylim(y_min, y_max)

    # Annotate top N by stock value.
    top_n = plot_df.nlargest(annotate_top_n, "StockValue")
    for _, row in top_n.iterrows():
        ax.annotate(
            row["ProductName"],
            (row["Price"], row["StockValue"]),
            textcoords="offset points",
            xytext=(6, 2),
            fontsize=8,
            color=PLOT_ACCENT,
            zorder=5,
        )

    ax.set_title("Stock value vs. unit price by category", fontsize=12, pad=10)
    ax.set_xlabel("Price (USD)")
    ax.set_ylabel(
        "Stock value (USD)" + (" (log scale)" if use_log else "")
    )
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(visible=True, which="major", linewidth=0.7, zorder=0)
    if use_log:
        ax.grid(visible=True, which="minor", linewidth=0.35,
                color="#DDDDDD", zorder=0)
    ax.tick_params(axis="x", rotation=0)

    ax.legend(
        title="Category",
        fontsize=9,
        title_fontsize=9,
        frameon=True,
        framealpha=0.9,
        edgecolor="#CCCCCC",
        loc="upper left",
    )

    fig.tight_layout()
    return fig


def plot_top_products(
    df: pd.DataFrame,
    n: int = 10,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Horizontal bar chart of the top N products by stock value.

    Args:
        df: Cleaned DataFrame from data_loader.clean().
        n: Number of products to show.
        ax: Optional Axes to draw on.  If None, a new figure is created.

    Returns:
        The matplotlib Figure.
    """
    _apply_style()
    top = _plot_df(df).nlargest(n, "StockValue").sort_values(
        "StockValue", ascending=True
    )

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4.6))
    else:
        fig = ax.figure

    bars = ax.barh(
        top["ProductName"],
        top["StockValue"],
        color=[PLOT_ACCENT] * len(top),
        edgecolor="white",
        linewidth=0.8,
        height=0.66,
        zorder=3,
    )

    ax.set_title(f"Top {n} products by total stock value", fontsize=12, pad=10)
    ax.set_xlabel("Total stock value (USD)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linewidth=0.7, zorder=0)
    ax.tick_params(axis="y", labelsize=9)

    vmax = top["StockValue"].max()
    for bar, val in zip(bars, top["StockValue"]):
        ax.text(
            bar.get_width() + vmax * 0.012,
            bar.get_y() + bar.get_height() / 2,
            f"${val:,.0f}",
            va="center",
            ha="left",
            fontsize=9,
            color="#222222",
        )

    ax.set_xlim(0, vmax * 1.18)
    fig.tight_layout()
    return fig
