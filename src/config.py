"""Central configuration: folder paths, file names and analysis settings.

Every other module imports its settings from here, so a path or a constant
is changed in one place only.
"""
from pathlib import Path

# ---------------------------------------------------------------- folders
# Project root = the folder that contains "src" (one level above this file).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Folder for the original, untouched data file.
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
# Folder for everything the pipeline produces.
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
# Sub-folder for charts.
FIGURES_DIR = ARTIFACTS_DIR / "figures"
# Sub-folder for result tables (CSV).
TABLES_DIR = ARTIFACTS_DIR / "tables"

# ------------------------------------------------------------------ files
# File-name pattern of the raw data ("*" also matches renamed copies).
RAW_DATA_PATTERN = "Manchester_house_Dataset*.csv"
# Output path of the cleaned dataset.
CLEAN_DATA_PATH = ARTIFACTS_DIR / "manchester_housing_clean.csv"

# --------------------------------------------------------------- settings
# Fixed seed so that random sampling gives identical results on every run.
RANDOM_STATE = 42
# Number of rows sampled for scatter plots (avoids over-plotting).
SCATTER_SAMPLE_SIZE = 5000
# Resolution (dots per inch) of saved figures.
FIG_DPI = 200
# Bedroom counts above this value are treated as data-entry errors.
MAX_PLAUSIBLE_BEDROOMS = 20
# Multiplier of the inter-quartile range in Tukey's outlier rule.
IQR_MULTIPLIER = 1.5

# ------------------------------------------------------------ variables
# Continuous or count variables summarised with descriptive statistics.
NUMERIC_COLS = ["price", "bedrooms", "bathrooms", "sqft_living",
                "sqft_total", "floors", "built", "renovated",
                "living_area"]
# Ordered rating variables, stored as ordered categoricals.
ORDINAL_COLS = ["view", "condition", "grade"]
# Variables summarised again after cleaning (including derived ones).
POST_CLEAN_COLS = ["price", "log_price", "bedrooms", "bathrooms",
                   "sqft_living", "log_sqft_living", "sqft_total", "built",
                   "renovated_year", "living_area"]
# Variables used in the floor-space correlation analysis.
SPACE_COLS = ["price", "sqft_living", "sqft_total", "living_area", "built"]
