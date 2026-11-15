"""Data ingestion: find the raw CSV file and load it into a DataFrame."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.config import RAW_DATA_DIR, RAW_DATA_PATTERN
from src.exception import CustomException
from src.logger import logging


@dataclass(frozen=True)
class DataIngestionConfig:
    """Where to look for the raw data file."""

    # Folder that contains the raw CSV.
    raw_data_dir: Path = RAW_DATA_DIR
    # File-name pattern of the raw CSV.
    file_pattern: str = RAW_DATA_PATTERN


class DataIngestion:
    """Locate and read the Manchester housing dataset."""

    def __init__(self, config: DataIngestionConfig | None = None) -> None:
        """Store the ingestion settings (defaults come from src.config)."""
        self.config = config or DataIngestionConfig()

    def locate_file(self) -> Path:
        """Return the path of the raw CSV file.

        Raises
        ------
        FileNotFoundError
            If no file matching the pattern is in the raw-data folder.
        """
        # All files in the raw-data folder that match the pattern.
        matches = sorted(self.config.raw_data_dir.glob(
            self.config.file_pattern))
        if not matches:
            raise FileNotFoundError(
                f"No file matching '{self.config.file_pattern}' in "
                f"{self.config.raw_data_dir}. Copy the dataset there.")
        # Use the first match (alphabetical order, so the result is stable).
        return matches[0]

    def load(self) -> pd.DataFrame:
        """Read the raw CSV into a DataFrame.

        Returns
        -------
        pandas.DataFrame
            The raw data exactly as stored in the file.
        """
        try:
            # Find the file first so a missing file gives a clear message.
            path = self.locate_file()
            logging.info("Reading raw data from %s", path)
            # utf-8-sig removes the byte-order mark at the start of the file.
            raw = pd.read_csv(path, encoding="utf-8-sig")
            logging.info("Raw data shape: %s rows x %s columns", *raw.shape)
            return raw
        except Exception as error:
            # Re-raise with the file name and line number of the failure.
            raise CustomException(error, sys) from error
