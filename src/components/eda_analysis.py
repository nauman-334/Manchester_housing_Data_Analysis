"""Statistical analysis of the three questions in the brief.

1. How do waterfront properties differ from the rest of the market?
2. How is floor space related to price?
3. Is the year a property was built (``built``) correlated with price?
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from src.config import SPACE_COLS
from src.logger import logging


def _regression_data(clean: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with grade and view as integers for C() dummies."""
    return clean.assign(grade=clean["grade"].astype(int),
                        view=clean["view"].astype(int))


def _percent(coef: float) -> float:
    """Convert a log-price coefficient into a percentage difference."""
    return float(np.exp(coef) - 1)


@dataclass
class WaterfrontResult:
    """Results of the waterfront investigation."""

    summary: pd.DataFrame
    mann_whitney_u: float
    mann_whitney_p: float
    rank_biserial: float
    ppsf_u: float
    ppsf_p: float
    view_crosstab: pd.DataFrame
    premiums: pd.DataFrame


def analyse_waterfront(clean: pd.DataFrame) -> WaterfrontResult:
    """Compare waterfront and non-waterfront properties.

    Uses medians (price is skewed), a Mann-Whitney U test (no normality
    assumption), the rank-biserial effect size, and log-price regressions
    with HC3 robust standard errors to estimate the controlled premium.
    """
    # Group summary: medians are preferred because price is skewed.
    summary = clean.groupby("waterfront").agg(
        n=("price", "size"),
        median_price=("price", "median"),
        mean_price=("price", "mean"),
        median_sqft_living=("sqft_living", "median"),
        median_price_per_sqft=("price_per_sqft", "median"),
        median_grade=("grade", lambda s: s.astype(int).median()),
    )

    # Prices of the two groups.
    wf = clean.loc[clean["waterfront"], "price"]
    non_wf = clean.loc[~clean["waterfront"], "price"]
    # Two-sided Mann-Whitney U test.
    u_stat, p_value = stats.mannwhitneyu(wf, non_wf,
                                         alternative="two-sided")
    # Rank-biserial r: +1 means waterfront is always more expensive.
    rank_biserial = 2 * u_stat / (len(wf) * len(non_wf)) - 1

    # Same test on price per square foot (partly removes the size effect).
    u_ppsf, p_ppsf = stats.mannwhitneyu(
        clean.loc[clean["waterfront"], "price_per_sqft"],
        clean.loc[~clean["waterfront"], "price_per_sqft"])

    # How view ratings are distributed in each group.
    crosstab = pd.crosstab(clean["waterfront"], clean["view"])

    # Premium after holding size, grade, age (and view) constant.
    reg_data = _regression_data(clean)
    formulas = {
        "controls: built, size, grade":
            "log_price ~ waterfront + built + log_sqft_living + C(grade)",
        "+ view rating":
            "log_price ~ waterfront + built + log_sqft_living + C(grade)"
            " + C(view)",
    }
    rows = []
    for label, formula in formulas.items():
        model = smf.ols(formula, data=reg_data).fit(cov_type="HC3")
        coef = model.params["waterfront[T.True]"]
        low, high = model.conf_int().loc["waterfront[T.True]"]
        rows.append({"Model": label, "premium": _percent(coef),
                     "ci_low": _percent(low), "ci_high": _percent(high)})
    premiums = pd.DataFrame(rows).set_index("Model")

    logging.info("Waterfront: U=%.0f p=%.2e r=%.3f", u_stat, p_value,
                 rank_biserial)
    return WaterfrontResult(summary, float(u_stat), float(p_value),
                            float(rank_biserial), float(u_ppsf),
                            float(p_ppsf), crosstab, premiums)


@dataclass
class FloorSpaceResult:
    """Results of the floor-space investigation."""

    pearson: pd.DataFrame
    spearman: pd.DataFrame
    elasticity: float
    r_squared: float


def analyse_floor_space(clean: pd.DataFrame) -> FloorSpaceResult:
    """Correlate floor-space variables with price and estimate elasticity.

    Pearson measures linear association; Spearman measures monotonic
    association on ranks and is robust to outliers. The slope of a log-log
    regression is the price elasticity of floor space.
    """
    pearson = clean[SPACE_COLS].corr(method="pearson")
    spearman = clean[SPACE_COLS].corr(method="spearman")
    model = smf.ols("log_price ~ log_sqft_living", data=clean).fit()
    elasticity = float(model.params["log_sqft_living"])
    logging.info("Floor space: elasticity=%.3f R2=%.3f", elasticity,
                 model.rsquared)
    return FloorSpaceResult(pearson, spearman, elasticity,
                            float(model.rsquared))


@dataclass
class BuiltPriceResult:
    """Results of the year-built versus price investigation."""

    pearson_r: float
    pearson_p: float
    spearman_rho: float
    spearman_p: float
    decade_table: pd.DataFrame
    model_table: pd.DataFrame


def analyse_built_price(clean: pd.DataFrame) -> BuiltPriceResult:
    """Test whether construction year is correlated with price.

    Reports the direct correlations, medians by decade (to reveal a
    non-linear pattern) and three regressions that add size and quality
    controls step by step.
    """
    r_p, p_p = stats.pearsonr(clean["built"], clean["price"])
    r_s, p_s = stats.spearmanr(clean["built"], clean["price"])

    # Medians by decade of construction.
    decade = clean.groupby("decade_built").agg(
        n=("price", "size"),
        median_price=("price", "median"),
        median_sqft=("sqft_living", "median"),
        median_ppsf=("price_per_sqft", "median"),
    )

    # Regressions with progressively more controls.
    reg_data = _regression_data(clean)
    formulas = {
        "M1: built only": "log_price ~ built",
        "M2: + floor space": "log_price ~ built + log_sqft_living",
        "M3: + grade, waterfront":
            "log_price ~ built + log_sqft_living + C(grade) + waterfront",
    }
    rows = []
    for name, formula in formulas.items():
        model = smf.ols(formula, data=reg_data).fit(cov_type="HC3")
        coef = model.params["built"]
        low, high = model.conf_int().loc["built"]
        rows.append({"Model": name, "built coef": coef,
                     "% per decade": (np.exp(10 * coef) - 1) * 100,
                     "95% CI low": low, "95% CI high": high,
                     "R²": model.rsquared})
    model_table = pd.DataFrame(rows).set_index("Model")

    logging.info("Built vs price: r=%.3f rho=%.3f", r_p, r_s)
    return BuiltPriceResult(float(r_p), float(p_p), float(r_s), float(p_s),
                            decade, model_table)
