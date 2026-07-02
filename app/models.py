from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), default="Customer")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.current_timestamp())


class CustomerProfileORM(Base):
    __tablename__ = "customer_profiles"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), default="Customer")
    age: Mapped[int] = mapped_column(Integer)
    occupation: Mapped[str | None] = mapped_column(String(80), nullable=True)
    annual_income: Mapped[float] = mapped_column(Float, default=0)
    monthly_income: Mapped[float] = mapped_column(Float, default=0)
    number_of_dependents: Mapped[int] = mapped_column(Integer, default=0)
    existing_investments: Mapped[float] = mapped_column(Float, default=0)
    existing_loans_or_emis: Mapped[float] = mapped_column(Float, default=0)
    emergency_fund_months: Mapped[float] = mapped_column(Float, default=0)
    goal_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    goal_amount: Mapped[float] = mapped_column(Float, default=0)
    goal_timeline_years: Mapped[float] = mapped_column(Float, default=0)
    investment_amount: Mapped[float] = mapped_column(Float, default=0)
    risk_appetite: Mapped[str | None] = mapped_column(String(40), nullable=True)
    investment_experience: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reaction_to_market_volatility: Mapped[str | None] = mapped_column(String(120), nullable=True)
    need_for_early_withdrawal: Mapped[str | None] = mapped_column(String(40), nullable=True)
    lock_in_acceptance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tax_slab: Mapped[int] = mapped_column(Integer, default=0)
    tax_saving_required: Mapped[str | None] = mapped_column(String(10), nullable=True)
    preferred_equity_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    international_exposure_preference: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.current_timestamp())


class MutualFund(Base):
    __tablename__ = "mutual_funds"

    fund_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mutual_fund_name: Mapped[str] = mapped_column(Text)
    amc: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    sub_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    plan_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    benchmark: Mapped[str | None] = mapped_column(String(120), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(40), nullable=True)
    min_horizon_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    lock_in_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    exit_load_period_days: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_investing_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_sip_investment: Mapped[float | None] = mapped_column(Float, nullable=True)
    inception_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    metrics: Mapped[list["FundMetric"]] = relationship(back_populates="fund")


class FundMetric(Base):
    __tablename__ = "fund_metrics"

    metric_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_funds.fund_id"))
    as_of_date: Mapped[str] = mapped_column(String(40), default="synthetic")
    nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    aum_cr: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_1y: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_3y: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_5y: Mapped[float | None] = mapped_column(Float, nullable=True)
    return_since_launch: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    sortino_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    alpha: Mapped[float | None] = mapped_column(Float, nullable=True)
    beta: Mapped[float | None] = mapped_column(Float, nullable=True)
    calmar_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    downside_deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    standard_deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[float | None] = mapped_column(Float, nullable=True)
    r_squared: Mapped[float | None] = mapped_column(Float, nullable=True)
    info_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    tracking_error: Mapped[float | None] = mapped_column(Float, nullable=True)
    capture_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    ttm_yield: Mapped[float | None] = mapped_column(Float, nullable=True)
    monthly_net_expense_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    turnover: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    return_grade: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fund: Mapped[MutualFund] = relationship(back_populates="metrics")


class AssetAllocationRule(Base):
    __tablename__ = "asset_allocation_rules"

    risk_bucket: Mapped[str] = mapped_column(String(40), primary_key=True)
    equity_pct: Mapped[float] = mapped_column(Float)
    debt_pct: Mapped[float] = mapped_column(Float)
    gold_pct: Mapped[float] = mapped_column(Float)


class FundCluster(Base):
    __tablename__ = "fund_clusters"

    cluster_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_funds.fund_id"))
    dbscan_cluster_label: Mapped[int] = mapped_column(Integer)
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    cluster_size: Mapped[int] = mapped_column(Integer, default=0)
    cluster_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.current_timestamp())


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customer_profiles.customer_id"), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_bucket: Mapped[str] = mapped_column(String(40))
    equity_allocation: Mapped[float] = mapped_column(Float)
    debt_allocation: Mapped[float] = mapped_column(Float)
    gold_allocation: Mapped[float] = mapped_column(Float)
    total_investment_amount: Mapped[float] = mapped_column(Float)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.current_timestamp())


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.recommendation_id"))
    fund_id: Mapped[int] = mapped_column(ForeignKey("mutual_funds.fund_id"))
    asset_class: Mapped[str] = mapped_column(String(40))
    allocation_percent: Mapped[float] = mapped_column(Float)
    allocation_amount: Mapped[float] = mapped_column(Float)
    customer_fit_score: Mapped[float] = mapped_column(Float)
    fund_performance_score: Mapped[float] = mapped_column(Float)
    risk_penalty: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)
    dbscan_cluster_label: Mapped[int] = mapped_column(Integer)
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class RejectedFund(Base):
    __tablename__ = "rejected_funds"

    rejected_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.recommendation_id"), nullable=True)
    fund_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str] = mapped_column(Text)


class RecommendationWarning(Base):
    __tablename__ = "recommendation_warnings"

    warning_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.recommendation_id"), nullable=True)
    warning: Mapped[str] = mapped_column(Text)


class AdvisorContextReport(Base):
    __tablename__ = "advisor_context_reports"

    context_report_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customer_profiles.customer_id"), nullable=True)
    recommendation_id: Mapped[int | None] = mapped_column(ForeignKey("recommendations.recommendation_id"), nullable=True)
    life_stage_time_horizon_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    financial_stability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal_feasibility_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    behavioral_risk_tolerance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_commitment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    portfolio_diversification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_documentation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    positive_signals_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    red_flags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    advisor_questions_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.current_timestamp())
