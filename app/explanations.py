from __future__ import annotations

import pandas as pd

from .schemas import CustomerProfile


def explain_recommendation(row: pd.Series, customer: CustomerProfile, risk_bucket: str) -> str:
    parts = [
        f"Fits the {risk_bucket} profile through {row.get('asset_bucket')} exposure.",
        f"Scores {row.get('final_score', 0):.1f} overall with performance {row.get('performance_score', 0):.1f}, suitability {row.get('suitability_score', 0):.1f}, and risk penalty {row.get('risk_penalty', 0):.1f}.",
    ]
    if float(row.get("min_horizon_years", 0) or 0) <= customer.goal_timeline_years:
        parts.append("Minimum horizon is compatible with the stated goal timeline.")
    if customer.tax_saving_requirement.lower() == "yes" and "elss" in str(row.get("sub_category", "")).lower():
        parts.append("ELSS is included because tax saving is required and lock-in is accepted.")
    if customer.need_for_early_withdrawal.lower() == "high":
        parts.append("Liquidity constraints were checked before ranking this fund.")
    if row.get("asset_bucket") == "debt":
        parts.append("Debt allocation supports capital preservation and liquidity.")
    elif row.get("asset_bucket") == "gold":
        parts.append("Gold allocation provides portfolio diversification.")
    if bool(row.get("is_outlier", False)):
        parts.append("DBSCAN marks this fund as a behavior outlier, so manual review is recommended.")
    elif "dbscan_cluster_id" in row:
        parts.append(f"DBSCAN behavior cluster {int(row.get('dbscan_cluster_id'))} contains similar behaving funds.")
    return " ".join(parts)
