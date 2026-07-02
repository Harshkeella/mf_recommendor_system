from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_FUND_CSV


REQUIRED_COLUMNS = {
    "mutual_fund_name",
    "amc",
    "category",
    "sub_category",
    "plan_type",
    "benchmark",
    "risk_level",
    "min_horizon_years",
    "expense_ratio",
    "exit_load_period_days",
    "lock_in_years",
    "minimum_investing_amount",
    "aum_cr",
    "nav",
    "return_1y",
    "return_3y",
    "return_5y",
    "return_since_launch",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "beta",
    "calmar_ratio",
    "downside_deviation",
    "standard_deviation",
    "max_drawdown",
    "r_squared",
    "info_ratio",
    "tracking_error",
    "capture_ratio",
    "ttm_yield",
    "monthly_net_expense_ratio",
    "turnover",
    "inception_date",
    "equity_style_box",
    "load",
    "min_sip_investment",
    "min_withdrawal",
    "min_no_of_cheques",
    "min_addl_investment",
    "min_balance",
    "risk_grade",
    "return_grade",
}


NUMERIC_COLUMNS = [
    "fund_id",
    "min_horizon_years",
    "expense_ratio",
    "exit_load_period_days",
    "lock_in_years",
    "minimum_investing_amount",
    "aum_cr",
    "nav",
    "return_1y",
    "return_3y",
    "return_5y",
    "return_since_launch",
    "sharpe_ratio",
    "sortino_ratio",
    "alpha",
    "beta",
    "calmar_ratio",
    "downside_deviation",
    "standard_deviation",
    "max_drawdown",
    "r_squared",
    "info_ratio",
    "tracking_error",
    "capture_ratio",
    "ttm_yield",
    "monthly_net_expense_ratio",
    "turnover",
    "min_sip_investment",
    "min_withdrawal",
    "min_no_of_cheques",
    "min_addl_investment",
    "min_balance",
]


def load_funds(csv_path: str | Path = DEFAULT_FUND_CSV) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Fund CSV not found: {path}")

    df = pd.read_csv(path)
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Fund CSV is missing required columns: {missing}")

    df = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "standard_deviation" not in df.columns and "std_dev" in df.columns:
        df["standard_deviation"] = pd.to_numeric(df["std_dev"], errors="coerce")

    df["inception_date"] = pd.to_datetime(df["inception_date"], errors="coerce", dayfirst=True)
    text_columns = [col for col in df.columns if df[col].dtype == "object"]
    for col in text_columns:
        df[col] = df[col].fillna("").astype(str).str.strip()
    return df
