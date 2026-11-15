"""Small reusable helper functions shared by the pipeline components."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import IQR_MULTIPLIER
from src.logger import logging


def summary_table(data: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return descriptive statistics with skewness, kurtosis and missing.

    Parameters
    ----------
    data : pandas.DataFrame
        Data to summarise.
    cols : list of str
        Names of the numeric columns to include.

    Returns
    -------
    pandas.DataFrame
        One row per variable, one column per statistic.
    """
    # count, mean, std, min, quartiles, max; transposed to one row per var.
    table = data[cols].describe().T
    # Skewness: 0 = symmetric, > 0 = long tail to the right.
    table["skew"] = data[cols].skew()
    # Kurtosis: large values indicate heavy tails / extreme values.
    table["kurtosis"] = data[cols].kurt()
    # Number of missing values per column.
    table["missing"] = data[cols].isna().sum()
    return table


def iqr_outliers(series: pd.Series,
                 multiplier: float = IQR_MULTIPLIER) -> pd.Series:
    """Return a Boolean mask of values outside Tukey's IQR fences.

    Parameters
    ----------
    series : pandas.Series
        Numeric values to check.
    multiplier : float, default 1.5
        Width of the fences in multiples of the inter-quartile range.

    Returns
    -------
    pandas.Series
        True where the value is an outlier.
    """
    # First (25%) and third (75%) quartiles.
    q1, q3 = series.quantile([0.25, 0.75])
    # Inter-quartile range: spread of the middle 50% of values.
    iqr = q3 - q1
    # True where a value lies below the lower or above the upper fence.
    return ((series < q1 - multiplier * iqr)
            | (series > q3 + multiplier * iqr))


def save_table(table: pd.DataFrame, path: Path, index: bool = True) -> Path:
    """Save a result table as CSV, creating the folder if needed.

    Parameters
    ----------
    table : pandas.DataFrame
        Table to save.
    path : pathlib.Path
        Destination file.
    index : bool, default True
        Whether to write the row index.

    Returns
    -------
    pathlib.Path
        The path that was written.
    """
    # Make sure the destination folder exists.
    path.parent.mkdir(parents=True, exist_ok=True)
    # Write the table to disk.
    table.to_csv(path, index=index)
    # Record the output in the log file.
    logging.info("Saved table: %s", path)
    return path
