"""Unit tests for the helper functions and the cleaning step.

Run from the project folder with:  python -m pytest
"""
import sys

import numpy as np
import pandas as pd
import pytest

from src.components.data_preprocessing import DataPreprocessor, correct_types
from src.exception import CustomException
from src.utils import iqr_outliers


def make_raw() -> pd.DataFrame:
    """Small synthetic dataset with one duplicate and one bad value."""
    return pd.DataFrame({
        "Unnamed: 0": [0, 1, 2, 3, 4],
        "id": [1, 2, 3, 3, 4],
        "price": [100_000, 200_000, 300_000, 300_000, 400_000],
        "bedrooms": [2.0, np.nan, 33.0, 33.0, 4.0],
        "bathrooms": [1.0, 2.0, np.nan, np.nan, 3.0],
        "sqft_living": [800, 1200, 1600, 1600, 2000],
        "sqft_total": [5000, 5000, 6000, 6000, 7000],
        "floors": [1.0, 1.0, 2.0, 2.0, 2.0],
        "waterfront": [0, 0, 1, 1, 0],
        "view": [0, 0, 4, 4, 1],
        "condition": [3, 3, 4, 4, 5],
        "grade": [7, 7, 8, 8, 8],
        "built": [1950, 1960, 2000, 2000, 2010],
        "renovated": [0, 1990, 0, 0, 0],
        "living_area": [900, 1100, 1500, 1500, 1900],
    })


def test_iqr_outliers_flags_extreme_value():
    """A value far above the rest is flagged; normal values are not."""
    series = pd.Series([1, 2, 3, 4, 5, 100])
    assert iqr_outliers(series).tolist() == [False] * 5 + [True]


def test_correct_types_sets_expected_dtypes():
    """id becomes text, waterfront Boolean, grade an ordered category."""
    df = correct_types(make_raw())
    assert "Unnamed: 0" not in df.columns
    assert df["waterfront"].dtype == bool
    assert isinstance(df["grade"].dtype, pd.CategoricalDtype)
    assert df["grade"].cat.ordered


def test_preprocessor_cleans_data():
    """Duplicates removed, no missing values, implausible value fixed."""
    clean = DataPreprocessor().run(correct_types(make_raw())).clean
    assert len(clean) == 4
    assert clean[["bedrooms", "bathrooms"]].isna().sum().sum() == 0
    assert clean["bedrooms"].max() <= 20
    assert {"log_price", "price_per_sqft", "is_renovated"} <= set(clean)


def test_custom_exception_reports_line():
    """The message names the file and the line where the error occurred."""
    with pytest.raises(CustomException) as caught:
        try:
            _ = 1 / 0
        except ZeroDivisionError as error:
            raise CustomException(error, sys) from error
    assert "line" in str(caught.value)
    assert "division by zero" in str(caught.value)
