"""Data preprocessing: type correction, quality audit and cleaning.

The steps follow a principle of minimal, justified intervention: every
change fixes a measured problem, and outliers are flagged, not removed,
because most waterfront properties are legitimate high-price outliers.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.config import MAX_PLAUSIBLE_BEDROOMS, ORDINAL_COLS
from src.exception import CustomException
from src.logger import logging
from src.utils import iqr_outliers


@dataclass
class PreprocessingResult:
    """Output of the cleaning step."""

    # Cleaned dataset with derived variables.
    clean: pd.DataFrame
    # Human-readable description of every cleaning decision.
    decision_log: list[str] = field(default_factory=list)


def correct_types(raw: pd.DataFrame) -> pd.DataFrame:
    """Give each column the data type that matches its meaning.

    Parameters
    ----------
    raw : pandas.DataFrame
        Data as read from the CSV file.

    Returns
    -------
    pandas.DataFrame
        A corrected copy; the input is not modified.
    """
    # Work on a copy so the raw data stay untouched.
    df = raw.copy()
    # The exported row index carries no information.
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")
    # The property id is a label, not a quantity.
    df["id"] = df["id"].astype(str)
    # waterfront is a yes/no flag.
    df["waterfront"] = df["waterfront"].astype(bool)
    # Ratings are ordered categories (e.g. grade 7 < grade 8).
    for col in ORDINAL_COLS:
        levels = sorted(df[col].unique())
        df[col] = pd.Categorical(df[col], categories=levels, ordered=True)
    logging.info("Data types corrected")
    return df


def audit_quality(df: pd.DataFrame) -> dict[str, int]:
    """Measure the data-quality problems that pre-processing must solve.

    Parameters
    ----------
    df : pandas.DataFrame
        Type-corrected data.

    Returns
    -------
    dict
        Name of each check and the number of affected records.
    """
    # Price outliers according to Tukey's IQR rule.
    price_out = iqr_outliers(df["price"])
    audit = {
        "missing_bedrooms": int(df["bedrooms"].isna().sum()),
        "missing_bathrooms": int(df["bathrooms"].isna().sum()),
        "exact_duplicates": int(df.duplicated().sum()),
        "repeated_ids": int(df["id"].duplicated().sum()),
        "implausible_bedrooms": int(
            (df["bedrooms"] > MAX_PLAUSIBLE_BEDROOMS).sum()),
        "living_gt_plot": int((df["sqft_living"] > df["sqft_total"]).sum()),
        "never_renovated": int((df["renovated"] == 0).sum()),
        "price_outliers": int(price_out.sum()),
        "waterfront_price_outliers": int(
            (price_out & df["waterfront"]).sum()),
        "waterfront_total": int(df["waterfront"].sum()),
    }
    # Record every check in the log file.
    for name, value in audit.items():
        logging.info("Audit %s: %s", name, value)
    return audit


class DataPreprocessor:
    """Clean the type-corrected data and add derived variables."""

    def run(self, df: pd.DataFrame) -> PreprocessingResult:
        """Apply every cleaning step in order.

        Parameters
        ----------
        df : pandas.DataFrame
            Type-corrected data (output of ``correct_types``).

        Returns
        -------
        PreprocessingResult
            The cleaned data and the decision log.
        """
        try:
            clean = df.copy()
            log: list[str] = []
            clean = self._remove_duplicates(clean, log)
            clean = self._fix_implausible_bedrooms(clean, log)
            clean = self._impute_room_counts(clean, log)
            clean = self._split_renovated(clean, log)
            clean = self._add_derived_columns(clean, log)
            for entry in log:
                logging.info("Pre-processing: %s", entry)
            logging.info("Clean data shape: %s rows x %s columns",
                         *clean.shape)
            return PreprocessingResult(clean=clean, decision_log=log)
        except Exception as error:
            raise CustomException(error, sys) from error

    @staticmethod
    def _remove_duplicates(df: pd.DataFrame,
                           log: list[str]) -> pd.DataFrame:
        """Drop exact duplicate rows; keep repeat sales (different price)."""
        n_before = len(df)
        df = df.drop_duplicates()
        log.append(f"Exact duplicates removed: {n_before - len(df)}")
        return df

    @staticmethod
    def _fix_implausible_bedrooms(df: pd.DataFrame,
                                  log: list[str]) -> pd.DataFrame:
        """Set impossible bedroom counts to missing so they are imputed."""
        bad = df["bedrooms"] > MAX_PLAUSIBLE_BEDROOMS
        df.loc[bad, "bedrooms"] = np.nan
        log.append(f"Implausible bedroom values set to missing: {bad.sum()}")
        return df

    @staticmethod
    def _impute_room_counts(df: pd.DataFrame,
                            log: list[str]) -> pd.DataFrame:
        """Fill missing room counts with the median of the same grade."""
        for col in ["bedrooms", "bathrooms"]:
            n_missing = int(df[col].isna().sum())
            # Median of each grade group, aligned to every row.
            grade_median = (df.groupby("grade", observed=True)[col]
                            .transform("median"))
            df[col] = df[col].fillna(grade_median)
            # Fallback: overall median if a grade group had no values.
            df[col] = df[col].fillna(df[col].median())
            log.append(f"{col}: {n_missing} missing values imputed "
                       "(grade-group median)")
        # Bedrooms are whole numbers.
        df["bedrooms"] = df["bedrooms"].round().astype(int)
        return df

    @staticmethod
    def _split_renovated(df: pd.DataFrame, log: list[str]) -> pd.DataFrame:
        """Replace the 0-coded 'renovated' column by a flag and a year."""
        df["is_renovated"] = df["renovated"] > 0
        df["renovated_year"] = df["renovated"].where(df["is_renovated"])
        df = df.drop(columns=["renovated"])
        log.append("renovated split into is_renovated (bool) and "
                   "renovated_year (NaN if never)")
        return df

    @staticmethod
    def _add_derived_columns(df: pd.DataFrame,
                             log: list[str]) -> pd.DataFrame:
        """Add log transforms, price per sq ft, decade and outlier flag."""
        df["log_price"] = np.log(df["price"])
        df["log_sqft_living"] = np.log(df["sqft_living"])
        df["price_per_sqft"] = df["price"] / df["sqft_living"]
        df["decade_built"] = (df["built"] // 10) * 10
        # Outliers are flagged for transparency, NOT removed.
        df["price_outlier"] = iqr_outliers(df["price"])
        log.append("Added log_price, log_sqft_living, price_per_sqft, "
                   "decade_built, price_outlier flag")
        return df


def before_after_comparison(df: pd.DataFrame,
                            clean: pd.DataFrame) -> pd.DataFrame:
    """Return key quality statistics before and after cleaning."""
    before = [len(df), int(df.isna().sum().sum()),
              int(df.duplicated().sum()), df["bedrooms"].max(),
              round(df["renovated"].mean(), 1),
              round(df["price"].skew(), 2),
              round(df["sqft_living"].skew(), 2)]
    after = [len(clean),
             int(clean[["bedrooms", "bathrooms"]].isna().sum().sum()),
             int(clean.drop(columns=["renovated_year"]).duplicated().sum()),
             clean["bedrooms"].max(),
             round(clean["renovated_year"].mean(), 1),
             round(clean["log_price"].skew(), 2),
             round(clean["log_sqft_living"].skew(), 2)]
    labels = ["Rows", "Missing values (bedrooms/bathrooms)",
              "Exact duplicates", "Maximum bedrooms",
              "Mean renovation year", "Skew of price (after: log_price)",
              "Skew of sqft_living (after: log)"]
    return pd.DataFrame({"Before": before, "After": after}, index=labels)
