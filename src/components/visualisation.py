"""Charts for the report (Figures 1-6), saved as PNG files.

Every function draws one figure, saves it, closes it to free memory and
returns the file path. Nothing is shown on screen, so the pipeline also
runs in a terminal without a display.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

# Use a file-only back end (no window); must be set before pyplot import.
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

from src.config import FIG_DPI, FIGURES_DIR  # noqa: E402
from src.logger import logging  # noqa: E402

# One consistent visual style for every chart.
sns.set_theme(style="whitegrid", context="notebook")


def _save(fig: plt.Figure, name: str, out_dir: Path) -> Path:
    """Save, close and log a figure; return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.tight_layout()
    fig.savefig(path, dpi=FIG_DPI)
    plt.close(fig)
    logging.info("Saved figure: %s", path)
    return path


def plot_waterfront_boxplots(clean: pd.DataFrame,
                             out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 1: price (log scale) and price per sq ft by waterfront."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sns.boxplot(data=clean, x="waterfront", y="price", ax=axes[0],
                log_scale=True)
    axes[0].set(title="Sale price by waterfront status (log scale)",
                xlabel="Waterfront", ylabel="Price")
    sns.boxplot(data=clean, x="waterfront", y="price_per_sqft", ax=axes[1])
    axes[1].set(title="Price per sq ft of living space",
                xlabel="Waterfront", ylabel="Price per sq ft")
    return _save(fig, "fig1_waterfront_box.png", out_dir)


def plot_view_waterfront(clean: pd.DataFrame,
                         out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 2: median price by view rating and waterfront status."""
    view_price = (clean.groupby(["view", "waterfront"], observed=True)
                  ["price"].median().unstack())
    fig, ax = plt.subplots(figsize=(8, 4.5))
    view_price.plot(kind="bar", ax=ax)
    ax.set(title="Median price by view rating and waterfront status",
           xlabel="View rating (0–4)", ylabel="Median price")
    ax.tick_params(axis="x", rotation=0)
    return _save(fig, "fig2_view_waterfront.png", out_dir)


def plot_floor_space_hist(clean: pd.DataFrame,
                          out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 3: floor space before and after log transformation."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    sns.histplot(clean["sqft_living"], bins=60, ax=axes[0])
    axes[0].set(title="Distribution of living floor space",
                xlabel="sqft_living")
    sns.histplot(clean["log_sqft_living"], bins=60, ax=axes[1])
    axes[1].set(title="After log transformation", xlabel="log(sqft_living)")
    return _save(fig, "fig3_sqft_hist.png", out_dir)


def plot_floor_space_scatter(clean: pd.DataFrame, sample: pd.DataFrame,
                             out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 4: price against floor space on log-log axes."""
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sns.scatterplot(data=sample[~sample["waterfront"]], x="sqft_living",
                    y="price", alpha=0.25, s=12, label="Non-waterfront",
                    ax=ax)
    sns.scatterplot(data=clean[clean["waterfront"]], x="sqft_living",
                    y="price", color="crimson", s=25,
                    label="Waterfront (all 159)", ax=ax)
    ax.set(xscale="log", yscale="log",
           title="Price against living floor space (log–log)",
           xlabel="sqft_living (log scale)", ylabel="Price (log scale)")
    return _save(fig, "fig4_sqft_price_scatter.png", out_dir)


def plot_correlation_heatmap(spearman: pd.DataFrame,
                             out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 5: heatmap of the Spearman correlation matrix."""
    fig, ax = plt.subplots(figsize=(7, 5.5))
    sns.heatmap(spearman, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1,
                vmax=1, ax=ax)
    ax.set_title("Spearman correlation matrix")
    return _save(fig, "fig5_corr_heatmap.png", out_dir)


def plot_built_price(clean: pd.DataFrame, sample: pd.DataFrame,
                     decade: pd.DataFrame,
                     out_dir: Path = FIGURES_DIR) -> Path:
    """Figure 6: price against year built, and medians by decade."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    # Left: scatter with a straight-line fit (shows the weak trend).
    sns.scatterplot(data=sample, x="built", y="price", alpha=0.2, s=10,
                    ax=axes[0])
    sns.regplot(data=clean, x="built", y="price", scatter=False,
                color="crimson", ax=axes[0])
    axes[0].set(yscale="log",
                title="Price against year built (sample, log y-axis)",
                xlabel="Year built", ylabel="Price (log scale)")
    # Right: median price and median price per sq ft per decade.
    axes[1].plot(decade.index, decade["median_price"], marker="o",
                 label="Median price")
    ax2 = axes[1].twinx()
    ax2.plot(decade.index, decade["median_ppsf"], marker="s",
             color="darkorange", label="Median price per sq ft")
    axes[1].set(title="Median price and price per sq ft by decade built",
                xlabel="Decade built", ylabel="Median price")
    ax2.set_ylabel("Median price per sq ft")
    handles_1, labels_1 = axes[1].get_legend_handles_labels()
    handles_2, labels_2 = ax2.get_legend_handles_labels()
    ax2.legend(handles_1 + handles_2, labels_1 + labels_2,
               loc="upper center")
    ax2.grid(False)
    return _save(fig, "fig6_built_price.png", out_dir)


# ------------------------------------------------- general EDA overview
def plot_numeric_distributions(data: pd.DataFrame, cols: list[str],
                               out_dir: Path = FIGURES_DIR) -> Path:
    """Overview: histogram of every numeric variable in a grid."""
    n_cols = 3
    n_rows = -(-len(cols) // n_cols)  # ceiling division
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 3.2 * n_rows))
    for ax, col in zip(axes.flat, cols):
        sns.histplot(data[col].dropna(), bins=50, ax=ax)
        ax.set(title=col, xlabel="", ylabel="Count")
    # Hide unused panels when the grid is larger than the variable list.
    for ax in list(axes.flat)[len(cols):]:
        ax.set_visible(False)
    return _save(fig, "eda_numeric_distributions.png", out_dir)


def plot_categorical_counts(data: pd.DataFrame, cols: list[str],
                            out_dir: Path = FIGURES_DIR) -> Path:
    """Overview: frequency bar chart of each categorical variable."""
    fig, axes = plt.subplots(1, len(cols), figsize=(4 * len(cols), 3.8))
    for ax, col in zip(axes, cols):
        counts = data[col].value_counts().sort_index()
        ax.bar(counts.index.astype(str), counts.values)
        ax.set(title=col, xlabel="", ylabel="Number of properties")
    return _save(fig, "eda_categorical_counts.png", out_dir)


def plot_full_correlation(data: pd.DataFrame,
                          out_dir: Path = FIGURES_DIR) -> Path:
    """Overview: Spearman correlation heatmap of all numeric variables."""
    corr = data.corr(method="spearman")
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1,
                vmax=1, square=True, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title("Spearman correlation – all numeric variables")
    return _save(fig, "eda_full_correlation.png", out_dir)
