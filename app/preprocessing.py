from __future__ import annotations

import numpy as np
import pandas as pd

try:  # scikit-learn is a declared dependency; fallback keeps core tests portable.
    from sklearn.preprocessing import RobustScaler
except ImportError:  # pragma: no cover - exercised only without optional deps
    RobustScaler = None

from .data_loader import NUMERIC_COLUMNS


PERFORMANCE_METRICS = [
    "return_3y",
    "return_5y",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "calmar_ratio",
    "info_ratio",
    "capture_ratio",
]

RISK_METRICS = [
    "expense_ratio",
    "standard_deviation",
    "downside_deviation",
    "max_drawdown",
    "beta",
    "tracking_error",
    "turnover",
]

COMPARISON_METRICS = [
    "return_3y",
    "return_5y",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "beta",
    "calmar_ratio",
    "standard_deviation",
    "downside_deviation",
    "max_drawdown",
    "expense_ratio",
    "capture_ratio",
    "tracking_error",
    "turnover",
]


def impute_fund_metrics(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    present_numeric = [c for c in NUMERIC_COLUMNS if c in result.columns]
    for col in present_numeric:
        result[col] = pd.to_numeric(result[col], errors="coerce")
        group_medians = result.groupby("sub_category")[col].transform("median")
        category_medians = result.groupby("category")[col].transform("median")
        result[col] = result[col].fillna(group_medians).fillna(category_medians).fillna(result[col].median())
    return result


def robust_z_by_group(df: pd.DataFrame, columns: list[str], group_cols: list[str] | None = None) -> pd.DataFrame:
    group_cols = group_cols or ["category", "sub_category"]
    scaled = pd.DataFrame(index=df.index)
    for col in columns:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        grouped = df[group_cols].astype(str).agg("|".join, axis=1)
        if RobustScaler is not None:
            col_scaled = pd.Series(0.0, index=df.index)
            for _, index in grouped.groupby(grouped).groups.items():
                group_values = values.loc[index].fillna(values.median()).to_numpy().reshape(-1, 1)
                if len(group_values) <= 1:
                    col_scaled.loc[index] = 0.0
                else:
                    col_scaled.loc[index] = RobustScaler().fit_transform(group_values).ravel()
            scaled[col] = col_scaled
        else:
            med = values.groupby(grouped).transform("median")
            q1 = values.groupby(grouped).transform(lambda s: s.quantile(0.25))
            q3 = values.groupby(grouped).transform(lambda s: s.quantile(0.75))
            iqr = (q3 - q1).replace(0, np.nan)
            global_iqr = values.quantile(0.75) - values.quantile(0.25)
            denom = iqr.fillna(global_iqr if global_iqr else 1.0).replace(0, 1.0)
            scaled[col] = ((values - med) / denom).replace([np.inf, -np.inf], 0).fillna(0)
    return scaled.clip(-4, 4)


def to_0_100(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan)
    if values.nunique(dropna=True) <= 1:
        return pd.Series(50.0, index=series.index)
    lo = values.quantile(0.05)
    hi = values.quantile(0.95)
    if hi == lo:
        return pd.Series(50.0, index=series.index)
    clipped = values.clip(lo, hi)
    score = (clipped - lo) / (hi - lo) * 100
    if not higher_is_better:
        score = 100 - score
    return score.fillna(50)
