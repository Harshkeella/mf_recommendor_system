from __future__ import annotations

import numpy as np
import pandas as pd

from .filtering import classify_asset_bucket, normalize_text
from .preprocessing import PERFORMANCE_METRICS, RISK_METRICS, robust_z_by_group, to_0_100
from .schemas import CustomerProfile


# High-impact fund metrics are risk level and risk-adjusted performance. Medium
# impact metrics refine ranking, while low/very-low impact fields such as AMC,
# AUM, minimum investment, lock-in, and exit load should never dominate the
# recommendation unless they create a hard suitability conflict.
FUND_PERFORMANCE_WEIGHTS = {
    "sharpe_ratio": 12,
    "sortino_ratio": 10,
    "alpha": 8,
    "return_3y": 6,
    "return_5y": 6,
    "calmar_ratio": 5,
    "capture_ratio": 4,
    "info_ratio": 3,
}

FUND_RISK_WEIGHTS = {
    "risk_level_mismatch": 15,
    "standard_deviation": 8,
    "max_drawdown": 8,
    "beta": 5,
    "downside_deviation": 5,
    "expense_ratio": 4,
    "tracking_error": 3,
    "exit_load_period_days": 1,
    "lock_in_years": 1,
    "minimum_investment_mismatch": 1,
    "low_aum": 2,
}

RISK_LEVEL_NUMERIC = {
    "low": 1,
    "low to moderate": 2,
    "moderate": 3,
    "moderately high": 4,
    "high": 4,
    "very high": 5,
}

BUCKET_RISK_NUMERIC = {
    "Very Critical": 1,
    "Critical": 2,
    "Balanced": 3,
    "Aggressive": 4,
    "Very Aggressive": 5,
}


def _risk_level_value(value: str) -> int:
    return RISK_LEVEL_NUMERIC.get(normalize_text(value), 3)


def _category_suitability(row: pd.Series, customer: CustomerProfile, risk_bucket: str) -> float:
    sub_category = normalize_text(row.get("sub_category"))
    category = normalize_text(row.get("category"))
    asset_bucket = row.get("asset_bucket") or classify_asset_bucket(row)

    score = 60
    wants_tax = customer.tax_saving_requirement.lower() == "yes"
    accepts_lock = customer.lock_in_acceptance.lower() == "yes"
    beginner = customer.investment_experience.lower() == "beginner"

    if customer.goal_timeline_years < 3 and asset_bucket == "equity":
        score = 25
    elif wants_tax and accepts_lock and "elss" in sub_category:
        score = 98
    elif beginner and any(term in sub_category for term in ["large cap", "flexi cap", "large & mid cap"]):
        score = 92
    elif customer.goal_timeline_years < 5 and any(term in sub_category for term in ["large cap", "balanced advantage", "equity savings"]):
        score = 80
    elif risk_bucket in {"Very Critical", "Critical"} and asset_bucket == "debt":
        score = 95
    elif risk_bucket == "Balanced" and category in {"Hybrid", "Debt"}:
        score = 85
    elif risk_bucket in {"Aggressive", "Very Aggressive"} and asset_bucket == "equity":
        score = 90
    elif asset_bucket == "gold":
        score = 70

    if beginner and any(
        term in sub_category for term in ["small cap", "sectoral", "thematic"]
    ):
        score -= 30
    if beginner and "mid cap" in sub_category and "large & mid cap" not in sub_category:
        score = min(score, 68)
    if customer.goal_timeline_years > 7 and customer.age <= 35 and asset_bucket == "equity":
        score += 8
    if customer.dependents >= 3 and asset_bucket == "equity":
        score -= 8
    if category == "international":
        score = min(score, 55 if customer.international_exposure_preference.lower() in {"yes", "moderate", "high"} else 25)
    return max(0, min(100, score))


def _timeline_match(row: pd.Series, customer: CustomerProfile) -> float:
    min_horizon = float(row.get("min_horizon_years", 0) or 0)
    if customer.goal_timeline_years >= min_horizon:
        return 100
    if min_horizon <= 0:
        return 70
    return max(0, customer.goal_timeline_years / min_horizon * 100)


def _liquidity_match(row: pd.Series, customer: CustomerProfile) -> float:
    lock_in_years = float(row.get("lock_in_years", 0) or 0)
    exit_load_days = float(row.get("exit_load_period_days", 0) or 0)
    need = customer.need_for_early_withdrawal.lower()
    score = 100
    if need == "high":
        score -= min(exit_load_days / 3, 40)
        score -= min(lock_in_years * 30, 60)
    elif need == "medium":
        score -= min(exit_load_days / 10, 20)
        score -= min(lock_in_years * 15, 35)
    return max(score, 0)


def _tax_match(row: pd.Series, customer: CustomerProfile) -> float:
    sub_category = normalize_text(row.get("sub_category"))
    wants_tax = customer.tax_saving_requirement.lower() == "yes"
    accepts_lock = customer.lock_in_acceptance.lower() == "yes"
    if wants_tax and accepts_lock and "elss" in sub_category:
        return 100
    if wants_tax and "elss" not in sub_category:
        return 70
    if not accepts_lock and "elss" in sub_category:
        return 0
    return 85


def _minimum_investment_match(row: pd.Series, customer: CustomerProfile) -> float:
    required = row.get("min_sip_investment", row.get("minimum_investing_amount", 0))
    required = float(required or 0)
    if required <= 0:
        return 85
    if customer.monthly_investment_amount >= required:
        return 100
    # Slight mismatch is low impact: reduce score softly and emit a warning at
    # the orchestration layer instead of rejecting the fund.
    return max(50, customer.monthly_investment_amount / required * 100)


def _weighted_average(frame: pd.DataFrame, weights: dict[str, int]) -> pd.Series:
    present = [col for col in weights if col in frame.columns]
    if not present:
        return pd.Series(50.0, index=frame.index)
    total = sum(weights[col] for col in present)
    return sum(frame[col] * weights[col] for col in present) / total


def _numeric_series(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index)


def _customer_fit_score(result: pd.DataFrame, customer: CustomerProfile, risk_bucket: str) -> pd.Series:
    risk_target = BUCKET_RISK_NUMERIC[risk_bucket]
    risk_match = result["risk_level"].map(lambda value: max(0, 100 - abs(_risk_level_value(value) - risk_target) * 25))
    timeline_match = result.apply(lambda row: _timeline_match(row, customer), axis=1)
    liquidity_match = result.apply(lambda row: _liquidity_match(row, customer), axis=1)
    tax_match = result.apply(lambda row: _tax_match(row, customer), axis=1)
    min_match = result.apply(lambda row: _minimum_investment_match(row, customer), axis=1)
    category_match = result.apply(lambda row: _category_suitability(row, customer, risk_bucket), axis=1)

    # These mirror the customer inputs by importance: timeline/risk behavior and
    # category suitability are high impact; tax, minimum investment, and liquidity
    # preferences are lower impact unless they triggered hard filters.
    return (
        timeline_match * 0.20
        + risk_match * 0.22
        + category_match * 0.24
        + liquidity_match * 0.14
        + tax_match * 0.10
        + min_match * 0.10
    )


def _advisor_context_adjustment(result: pd.DataFrame, advisor_context_scores: dict[str, float] | None) -> pd.Series:
    if not advisor_context_scores:
        return pd.Series(0.0, index=result.index)

    context = {key: float(value) for key, value in advisor_context_scores.items()}
    life_stage = context.get("life_stage_time_horizon", 50)
    stability = context.get("financial_stability", 50)
    goal_feasibility = context.get("goal_feasibility", 50)
    behavior = context.get("behavioral_risk_tolerance", 50)
    liquidity = context.get("liquidity_commitment", 50)
    diversification = context.get("portfolio_diversification", 50)
    tax_docs = context.get("tax_documentation", 50)

    adjustment = pd.Series(0.0, index=result.index)
    sub_category = result["sub_category"].map(normalize_text)
    category = result["category"].map(normalize_text)
    asset_bucket = result["asset_bucket"]
    risk_level_value = result["risk_level"].map(_risk_level_value)
    exit_load = _numeric_series(result, "exit_load_period_days")
    lock_in = _numeric_series(result, "lock_in_years")

    high_volatility = risk_level_value >= 4
    aggressive_satellite = sub_category.map(
        lambda value: any(term in value for term in ["small cap", "mid cap", "sectoral", "thematic", "multi cap"])
    )
    conservative_categories = (asset_bucket == "debt") | sub_category.map(
        lambda value: any(term in value for term in ["liquid", "overnight", "money market", "arbitrage", "short duration"])
    )
    core_equity = sub_category.map(
        lambda value: any(term in value for term in ["large cap", "flexi cap", "large & mid cap", "index fund"])
    )

    risk_comfort = min(life_stage, behavior)
    if risk_comfort < 50:
        adjustment -= np.where((asset_bucket == "equity") & high_volatility, (50 - risk_comfort) * 0.35, 0)
        adjustment -= np.where(aggressive_satellite, (50 - risk_comfort) * 0.40, 0)
        adjustment += np.where(conservative_categories, (50 - risk_comfort) * 0.18, 0)
    else:
        adjustment += np.where((asset_bucket == "equity") & core_equity, (risk_comfort - 50) * 0.08, 0)
        adjustment += np.where(aggressive_satellite, (risk_comfort - 50) * 0.10, 0)

    if stability < 50:
        adjustment -= np.where((asset_bucket == "equity") & high_volatility, (50 - stability) * 0.20, 0)
        adjustment += np.where(conservative_categories, (50 - stability) * 0.12, 0)

    if goal_feasibility < 50:
        adjustment -= np.where(aggressive_satellite, (50 - goal_feasibility) * 0.16, 0)
        adjustment += np.where(core_equity | conservative_categories, (50 - goal_feasibility) * 0.06, 0)

    if liquidity < 50:
        illiquid = (exit_load >= 180) | (lock_in > 0)
        adjustment -= np.where(illiquid, (50 - liquidity) * 0.30, 0)
        adjustment += np.where((asset_bucket == "debt") & ~illiquid, (50 - liquidity) * 0.08, 0)

    if diversification >= 60:
        satellite = sub_category.map(
            lambda value: any(term in value for term in ["balanced advantage", "multi asset", "equity savings", "gold", "silver"])
        )
        adjustment += np.where(satellite, (diversification - 50) * 0.12, 0)
        adjustment += np.where(category == "international", (diversification - 50) * 0.08, 0)

    if tax_docs >= 65:
        adjustment += np.where(sub_category.str.contains("elss", regex=False), (tax_docs - 50) * 0.12, 0)
    elif tax_docs < 45:
        adjustment -= np.where(sub_category.str.contains("elss", regex=False) | (lock_in > 0), (45 - tax_docs) * 0.18, 0)

    return adjustment.clip(-25, 18)


def score_funds(
    df: pd.DataFrame,
    customer: CustomerProfile,
    risk_bucket: str,
    advisor_context_scores: dict[str, float] | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    result = df.copy()
    if "asset_bucket" not in result.columns:
        result["asset_bucket"] = result.apply(classify_asset_bucket, axis=1)

    performance_scaled = robust_z_by_group(result, [m for m in PERFORMANCE_METRICS if m in FUND_PERFORMANCE_WEIGHTS])
    risk_scaled = robust_z_by_group(result, [m for m in RISK_METRICS if m in result.columns])

    performance_raw = _weighted_average(performance_scaled, FUND_PERFORMANCE_WEIGHTS)
    risk_raw = risk_scaled.copy()
    if "max_drawdown" in risk_raw.columns:
        risk_raw["max_drawdown"] = risk_raw["max_drawdown"].abs()
    if "tracking_error" in risk_raw.columns:
        passive_multiplier = result["category"].map(lambda value: 2.0 if normalize_text(value) == "passive" else 0.65)
        risk_raw["tracking_error"] = risk_raw["tracking_error"] * passive_multiplier

    risk_target = BUCKET_RISK_NUMERIC[risk_bucket]
    risk_raw["risk_level_mismatch"] = result["risk_level"].map(lambda value: abs(_risk_level_value(value) - risk_target))
    risk_raw["exit_load_period_days"] = to_0_100(_numeric_series(result, "exit_load_period_days"), higher_is_better=True) / 100
    risk_raw["lock_in_years"] = to_0_100(_numeric_series(result, "lock_in_years"), higher_is_better=True) / 100
    min_required = _numeric_series(result, "min_sip_investment")
    if "min_sip_investment" not in result.columns:
        min_required = _numeric_series(result, "minimum_investing_amount")
    risk_raw["minimum_investment_mismatch"] = np.where(
        min_required > customer.monthly_investment_amount,
        (min_required - customer.monthly_investment_amount) / min_required.replace(0, np.nan),
        0,
    )
    aum = _numeric_series(result, "aum_cr")
    risk_raw["low_aum"] = to_0_100(-aum, higher_is_better=True) / 100
    risk_penalty_raw = _weighted_average(risk_raw, FUND_RISK_WEIGHTS)

    result["performance_score"] = to_0_100(performance_raw, higher_is_better=True)
    result["risk_penalty"] = to_0_100(risk_penalty_raw, higher_is_better=True)
    result["customer_fit_score"] = _customer_fit_score(result, customer, risk_bucket)
    result["suitability_score"] = result["customer_fit_score"]
    result["advisor_context_adjustment"] = _advisor_context_adjustment(result, advisor_context_scores)

    result["final_score"] = (
        0.40 * result["customer_fit_score"]
        + 0.45 * result["performance_score"]
        - 0.15 * result["risk_penalty"]
        + result["advisor_context_adjustment"]
    )
    # International funds can be useful satellites, but the brief says they
    # should not become the main allocation for the Rahul-style profile.
    result.loc[result["category"].map(normalize_text) == "international", "final_score"] -= 12
    if customer.investment_experience.lower() == "beginner" and customer.goal_timeline_years >= 7:
        core_equity = result["sub_category"].map(
            lambda value: any(
                term in normalize_text(value)
                for term in ["large cap", "flexi cap", "large & mid cap", "elss"]
            )
        )
        satellite_equity = result["sub_category"].map(
            lambda value: any(
                term in normalize_text(value)
                for term in ["dividend yield", "value", "contra", "balanced advantage", "multi asset"]
            )
        )
        result.loc[core_equity, "final_score"] += 8
        result.loc[satellite_equity, "final_score"] -= 4
    return result.sort_values("final_score", ascending=False)
