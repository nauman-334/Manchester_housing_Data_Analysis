"""Run the complete Manchester housing analysis from start to finish.

Usage (from the project folder, with the environment active)::

    python -m src.pipeline.run_pipeline

Outputs are written to the ``artifacts`` folder:
    artifacts/manchester_housing_clean.csv   cleaned dataset
    artifacts/tables/*.csv                   result tables
    artifacts/figures/*.png                  Figures 1-6
and a log of the run to ``logs/<date_time>.log``.
"""
from __future__ import annotations

import sys

import pandas as pd

from src.components.data_ingestion import DataIngestion
from src.components.data_preprocessing import (DataPreprocessor,
                                               audit_quality,
                                               before_after_comparison,
                                               correct_types)
from src.components.eda_analysis import (analyse_built_price,
                                         analyse_floor_space,
                                         analyse_waterfront)
from src.components import visualisation as viz
from src.config import (CLEAN_DATA_PATH, NUMERIC_COLS, POST_CLEAN_COLS,
                        RANDOM_STATE, SCATTER_SAMPLE_SIZE, TABLES_DIR)
from src.exception import CustomException
from src.logger import LOG_FILE_PATH, logging
from src.utils import save_table, summary_table


def run() -> None:
    """Execute ingestion, cleaning, analysis and charting in order."""
    logging.info("===== Pipeline started =====")

    # 1) Load the raw data and correct the data types.
    raw = DataIngestion().load()
    df = correct_types(raw)
    print(f"Loaded {len(df):,} rows x {df.shape[1]} columns")

    # 2) Initial statistics and data-quality audit.
    save_table(summary_table(df, NUMERIC_COLS),
               TABLES_DIR / "01_initial_statistics.csv")
    audit = audit_quality(df)
    save_table(pd.Series(audit, name="count").to_frame(),
               TABLES_DIR / "02_quality_audit.csv")

    # 3) Cleaning, post-cleaning statistics and before/after comparison.
    result = DataPreprocessor().run(df)
    clean = result.clean
    CLEAN_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(CLEAN_DATA_PATH, index=False)
    save_table(pd.Series(result.decision_log, name="decision").to_frame(),
               TABLES_DIR / "03_preprocessing_log.csv", index=False)
    save_table(summary_table(clean, POST_CLEAN_COLS),
               TABLES_DIR / "04_post_clean_statistics.csv")
    comparison = before_after_comparison(df, clean)
    save_table(comparison, TABLES_DIR / "05_before_after.csv")
    print(f"Cleaned data: {len(clean):,} rows -> {CLEAN_DATA_PATH}")

    # 4) Investigation 1: waterfront properties.
    wf = analyse_waterfront(clean)
    save_table(wf.summary, TABLES_DIR / "06_waterfront_summary.csv")
    save_table(wf.premiums, TABLES_DIR / "07_waterfront_premiums.csv")
    print(f"Waterfront: Mann-Whitney p = {wf.mann_whitney_p:.2e}, "
          f"rank-biserial r = {wf.rank_biserial:.3f}")

    # 5) Investigation 2: floor space.
    fs = analyse_floor_space(clean)
    save_table(fs.pearson, TABLES_DIR / "08_pearson_matrix.csv")
    save_table(fs.spearman, TABLES_DIR / "09_spearman_matrix.csv")
    print(f"Floor space: elasticity = {fs.elasticity:.3f}, "
          f"R² = {fs.r_squared:.3f}")

    # 6) Investigation 3: year built versus price.
    bp = analyse_built_price(clean)
    save_table(bp.decade_table, TABLES_DIR / "10_decade_medians.csv")
    save_table(bp.model_table, TABLES_DIR / "11_built_models.csv")
    print(f"Built vs price: Pearson r = {bp.pearson_r:.3f}, "
          f"Spearman rho = {bp.spearman_rho:.3f}")

    # 7) Figures 1-6 (one fixed random sample for both scatter plots).
    sample = clean.sample(SCATTER_SAMPLE_SIZE, random_state=RANDOM_STATE)
    viz.plot_waterfront_boxplots(clean)
    viz.plot_view_waterfront(clean)
    viz.plot_floor_space_hist(clean)
    viz.plot_floor_space_scatter(clean, sample)
    viz.plot_correlation_heatmap(fs.spearman)
    viz.plot_built_price(clean, sample, bp.decade_table)

    logging.info("===== Pipeline finished =====")
    print(f"Done. Tables and figures are in 'artifacts'; log: "
          f"{LOG_FILE_PATH}")


def main() -> int:
    """Command-line entry point; returns 0 on success, 1 on failure."""
    try:
        run()
        return 0
    except CustomException as error:
        print(f"Pipeline failed: {error}")
        return 1
    except Exception as error:  # unexpected error: log with details
        print(f"Pipeline failed: {CustomException(error, sys)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
