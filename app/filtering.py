from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .schemas import CustomerProfile


@dataclass(frozen=True)
class FilterResult:
    eligible: pd.DataFrame
    rejected: pd.DataFrame
    warnings: list[str]


def normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def classify_asset_bucket(row: pd.Series) -> str:
    category = normalize_text(row.get("category"))
    sub_category = normalize_text(row.get("sub_category"))
    benchmark = normalize_text(row.get("benchmark"))

    if "gold" in sub_category or "silver" in sub_category or category == "commodity":
        return "gold"
    if category == "debt" or "debt" in sub_category or "bond" in sub_category or "gilt" in sub_category:
        return "debt"
    if "overnight" in sub_category or "liquid" in sub_category or "money market" in sub_category:
        return "debt"
    if category == "passive" and ("debt" in sub_category or "debt" in benchmark):
        return "debt"
    if "conservative hybrid" in sub_category or "arbitrage" in sub_category:
        return "debt"
    return "equity"


def _add_rejection(reasons: dict[int, list[str]], index: int, reason: str) -> None:
    reasons.setdefault(index, []).append(reason)


def filter_funds(
    df: pd.DataFrame,
    customer: CustomerProfile,
    risk_bucket: str | None = None,
    advisor_context_scores: dict[str, float] | None = None,
) -> FilterResult:
    reasons: dict[int, list[str]] = {}
    warnings: list[str] = []
    context = advisor_context_scores or {}
    life_stage_score = float(context.get("life_stage_time_horizon", 100))
    stability_score = float(context.get("financial_stability", 100))
    behavior_score = float(context.get("behavioral_risk_tolerance", 100))
    liquidity_score = float(context.get("liquidity_commitment", 100))

    for idx, row in df.iterrows():
        sub_category = normalize_text(row.get("sub_category"))
        category = normalize_text(row.get("category"))
        risk_level = normalize_text(row.get("risk_level"))
        asset_bucket = classify_asset_bucket(row)
        lock_in_years = float(row.get("lock_in_years", 0) or 0)
        exit_load_days = float(row.get("exit_load_period_days", 0) or 0)
        min_horizon = float(row.get("min_horizon_years", 0) or 0)
        min_investment = float(row.get("min_sip_investment", row.get("minimum_investing_amount", 0)) or 0)

        horizon_gap = min_horizon - customer.goal_timeline_years
        if horizon_gap >= max(2.0, min_horizon * 0.50):
            _add_rejection(
                reasons,
                idx,
                f"Goal timeline {customer.goal_timeline_years:g}y is far below fund horizon {min_horizon:g}y.",
            )

        if customer.goal_timeline_years < 7 and "small cap" in sub_category:
            _add_rejection(reasons, idx, "Small cap removed for goals below 7 years.")

        if customer.goal_timeline_years < 3:
            if any(term in sub_category for term in ["mid cap", "sectoral", "thematic"]):
                _add_rejection(reasons, idx, "Volatile equity category removed for goals below 3 years.")
            if risk_level in {"high", "very high"} and asset_bucket == "equity":
                _add_rejection(reasons, idx, "High-risk equity fund removed for goals below 3 years.")

        if customer.need_for_early_withdrawal.lower() == "high" and lock_in_years > 0:
            _add_rejection(reasons, idx, "Early withdrawal need is high; lock-in fund removed.")

        if risk_bucket == "Very Critical" and risk_level == "very high":
            _add_rejection(reasons, idx, "Very Critical customer cannot be matched to Very High risk fund.")

        if customer.lock_in_acceptance.lower() != "yes":
            if lock_in_years > 0:
                _add_rejection(reasons, idx, "Lock-in not accepted; lock-in fund removed.")

        if min_investment > 0 and customer.monthly_investment_amount < min_investment * 0.50:
            _add_rejection(
                reasons,
                idx,
                "Investment amount is less than 50% of required minimum investment.",
            )

        if customer.international_exposure_preference.lower() == "none" and category == "international":
            _add_rejection(reasons, idx, "International exposure preference is None.")

        if advisor_context_scores:
            volatile_equity = asset_bucket == "equity" and (
                risk_level in {"high", "very high"}
                or any(term in sub_category for term in ["small cap", "mid cap", "sectoral", "thematic"])
            )
            if min(life_stage_score, behavior_score) < 35 and volatile_equity:
                _add_rejection(
                    reasons,
                    idx,
                    "Advisor context slider indicates low time horizon or behavior score; volatile equity fund removed.",
                )
            elif min(life_stage_score, behavior_score) < 50 and any(
                term in sub_category for term in ["small cap", "sectoral", "thematic"]
            ):
                _add_rejection(
                    reasons,
                    idx,
                    "Advisor context slider reduced aggressive satellite categories.",
                )

            if stability_score < 35 and asset_bucket == "equity" and risk_level in {"high", "very high"}:
                _add_rejection(
                    reasons,
                    idx,
                    "Advisor context slider indicates weak financial stability; high-risk equity fund removed.",
                )

            if liquidity_score < 40 and (lock_in_years > 0 or exit_load_days >= 180):
                _add_rejection(
                    reasons,
                    idx,
                    "Advisor context slider indicates low liquidity comfort; lock-in or high exit-load fund removed.",
                )

    if customer.emergency_fund_months < 3:
        warnings.append("Emergency fund below 3 months; recommendations should prioritize liquidity first.")
    if customer.emi_burden_ratio > 0.40:
        warnings.append("EMI burden is above 40% of monthly income; equity-heavy choices are constrained.")
    if (
        customer.tax_saving_requirement.lower() == "yes"
        and customer.lock_in_acceptance.lower() == "yes"
    ):
        warnings.append("Tax saving required and lock-in accepted; ELSS is allowed as a candidate category.")
    if customer.monthly_investment_amount > 0:
        slight_minimum_mismatch = df[
            (pd.to_numeric(df.get("min_sip_investment", df.get("minimum_investing_amount", 0)), errors="coerce") > customer.monthly_investment_amount)
            & (pd.to_numeric(df.get("min_sip_investment", df.get("minimum_investing_amount", 0)), errors="coerce") <= customer.monthly_investment_amount * 2)
        ]
        if not slight_minimum_mismatch.empty:
            warnings.append(
                "Some funds have a minimum investment slightly above the planned SIP; advisor may suggest increasing SIP or choosing alternatives."
            )
    if advisor_context_scores:
        warnings.append("Advisor insight sliders are active; eligible funds and ranking are adjusted from the current slider values.")

    rejected_rows = []
    for idx, row_reasons in reasons.items():
        rejected_rows.append(
            {
                "fund_id": df.loc[idx].get("fund_id"),
                "mutual_fund_name": df.loc[idx].get("mutual_fund_name"),
                "category": df.loc[idx].get("category"),
                "sub_category": df.loc[idx].get("sub_category"),
                "reasons": "; ".join(sorted(set(row_reasons))),
            }
        )

    eligible = df.drop(index=list(reasons.keys()), errors="ignore").copy()
    eligible["asset_bucket"] = eligible.apply(classify_asset_bucket, axis=1)
    rejected = pd.DataFrame(rejected_rows)
    return FilterResult(eligible=eligible, rejected=rejected, warnings=warnings)
