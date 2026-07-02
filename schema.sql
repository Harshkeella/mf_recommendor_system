-- Mutual Fund Recommender MVP Schema
-- SQLite-friendly types; PostgreSQL can use the same logical design with
-- SERIAL/IDENTITY and JSONB where desired.

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_profiles (
    customer_id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    name TEXT,
    age INTEGER NOT NULL,
    occupation TEXT,
    annual_income REAL,
    monthly_income REAL,
    number_of_dependents INTEGER,
    existing_investments REAL,
    existing_loans_or_emis REAL,
    emergency_fund_months REAL,
    goal_type TEXT,
    goal_amount REAL,
    goal_timeline_years REAL,
    investment_amount REAL,
    risk_appetite TEXT,
    investment_experience TEXT,
    reaction_to_market_volatility TEXT,
    need_for_early_withdrawal TEXT,
    lock_in_acceptance TEXT,
    tax_slab INTEGER,
    tax_saving_required TEXT,
    preferred_equity_exposure REAL,
    international_exposure_preference TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutual_funds (
    fund_id INTEGER PRIMARY KEY,
    mutual_fund_name TEXT NOT NULL,
    amc TEXT,
    category TEXT,
    sub_category TEXT,
    plan_type TEXT,
    benchmark TEXT,
    risk_level TEXT,
    min_horizon_years REAL,
    lock_in_years REAL,
    exit_load_period_days REAL,
    minimum_investing_amount REAL,
    min_sip_investment REAL,
    inception_date TEXT
);

CREATE TABLE IF NOT EXISTS fund_metrics (
    metric_id INTEGER PRIMARY KEY,
    fund_id INTEGER NOT NULL REFERENCES mutual_funds(fund_id),
    as_of_date TEXT NOT NULL,
    nav REAL,
    aum_cr REAL,
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
    risk_grade TEXT,
    return_grade TEXT,
    UNIQUE (fund_id, as_of_date)
);

CREATE TABLE IF NOT EXISTS asset_allocation_rules (
    risk_bucket TEXT PRIMARY KEY,
    equity_pct REAL NOT NULL,
    debt_pct REAL NOT NULL,
    gold_pct REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fund_clusters (
    cluster_id INTEGER PRIMARY KEY,
    fund_id INTEGER NOT NULL REFERENCES mutual_funds(fund_id),
    dbscan_cluster_label INTEGER NOT NULL,
    is_outlier INTEGER NOT NULL DEFAULT 0,
    cluster_size INTEGER NOT NULL,
    cluster_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customer_profiles(customer_id),
    risk_score REAL NOT NULL,
    risk_bucket TEXT NOT NULL,
    equity_allocation REAL NOT NULL,
    debt_allocation REAL NOT NULL,
    gold_allocation REAL NOT NULL,
    total_investment_amount REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_items (
    item_id INTEGER PRIMARY KEY,
    recommendation_id INTEGER NOT NULL REFERENCES recommendations(recommendation_id),
    fund_id INTEGER NOT NULL REFERENCES mutual_funds(fund_id),
    asset_class TEXT,
    allocation_percent REAL,
    allocation_amount REAL,
    customer_fit_score REAL,
    fund_performance_score REAL,
    risk_penalty REAL,
    final_score REAL,
    dbscan_cluster_label INTEGER,
    is_outlier INTEGER DEFAULT 0,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS rejected_funds (
    rejected_id INTEGER PRIMARY KEY,
    recommendation_id INTEGER REFERENCES recommendations(recommendation_id),
    fund_id INTEGER,
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recommendation_warnings (
    warning_id INTEGER PRIMARY KEY,
    recommendation_id INTEGER REFERENCES recommendations(recommendation_id),
    warning TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS advisor_context_reports (
    context_report_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customer_profiles(customer_id),
    recommendation_id INTEGER REFERENCES recommendations(recommendation_id),
    life_stage_time_horizon_score REAL,
    financial_stability_score REAL,
    goal_feasibility_score REAL,
    behavioral_risk_tolerance_score REAL,
    liquidity_commitment_score REAL,
    portfolio_diversification_score REAL,
    tax_documentation_score REAL,
    overall_summary TEXT,
    positive_signals_json TEXT,
    red_flags_json TEXT,
    advisor_questions_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
