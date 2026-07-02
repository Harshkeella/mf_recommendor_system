from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import DEFAULT_DATABASE_URL, DEFAULT_FUND_CSV
from .data_loader import load_funds
from .models import Base


def _require_sqlalchemy():
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise RuntimeError(
            "SQLAlchemy is required for database persistence. Install requirements.txt first."
        ) from exc
    return create_engine, text


def get_engine(database_url: str = DEFAULT_DATABASE_URL):
    create_engine, _ = _require_sqlalchemy()
    return create_engine(database_url, future=True)


def create_schema(database_url: str = DEFAULT_DATABASE_URL) -> None:
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)


def initialize_database(database_url: str = DEFAULT_DATABASE_URL, fund_csv_path: str | Path = DEFAULT_FUND_CSV) -> int:
    _, text = _require_sqlalchemy()
    engine = get_engine(database_url)
    funds = load_funds(fund_csv_path)
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS mutual_funds_raw (
                    fund_id INTEGER PRIMARY KEY,
                    mutual_fund_name TEXT NOT NULL,
                    amc TEXT,
                    category TEXT,
                    sub_category TEXT,
                    plan_type TEXT,
                    benchmark TEXT,
                    risk_level TEXT,
                    min_horizon_years REAL,
                    expense_ratio REAL,
                    exit_load_period_days REAL,
                    lock_in_years REAL,
                    minimum_investing_amount REAL,
                    aum_cr REAL,
                    nav REAL,
                    return_1y REAL,
                    return_3y REAL,
                    return_5y REAL,
                    return_since_launch REAL,
                    sharpe_ratio REAL,
                    sortino_ratio REAL,
                    alpha REAL,
                    beta REAL,
                    calmar_ratio REAL,
                    downside_deviation REAL,
                    standard_deviation REAL,
                    max_drawdown REAL,
                    r_squared REAL,
                    info_ratio REAL,
                    tracking_error REAL,
                    capture_ratio REAL,
                    ttm_yield REAL,
                    monthly_net_expense_ratio REAL,
                    turnover REAL,
                    inception_date TEXT,
                    equity_style_box TEXT,
                    load TEXT,
                    min_sip_investment REAL,
                    min_withdrawal REAL,
                    min_no_of_cheques REAL,
                    min_addl_investment REAL,
                    min_balance REAL,
                    risk_grade TEXT,
                    return_grade TEXT,
                    data_quality TEXT
                )
                """
            )
        )
        funds.to_sql("mutual_funds_raw", conn, if_exists="replace", index=False)
    return len(funds)


def read_funds_from_database(database_url: str = DEFAULT_DATABASE_URL) -> pd.DataFrame:
    engine = get_engine(database_url)
    return pd.read_sql_table("mutual_funds_raw", engine)
