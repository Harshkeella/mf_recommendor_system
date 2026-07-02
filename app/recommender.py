from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .allocation import calculate_allocation
from .clustering import cluster_funds, cosine_similar_funds
from .config import DEFAULT_FUND_CSV, DISCLAIMER
from .data_loader import load_funds
from .explanations import explain_recommendation
from .filtering import filter_funds
from .preprocessing import impute_fund_metrics
from .risk_profile import RISK_SCALE, calculate_risk_profile
from .schemas import CustomerProfile
from .scoring import score_funds


def _fund_slots_for_allocation(allocation: dict[str, float], total_slots: int = 6) -> dict[str, int]:
    positive = {bucket: pct for bucket, pct in allocation.items() if pct > 0}
    if not positive:
        return {}

    slots = {
        bucket: max(1, round(total_slots * pct / 100))
        for bucket, pct in positive.items()
    }
    while sum(slots.values()) > total_slots:
        reducible = [bucket for bucket, count in slots.items() if count > 1]
        if not reducible:
            break
        bucket = min(reducible, key=lambda key: positive[key])
        slots[bucket] -= 1
    while sum(slots.values()) < total_slots:
        bucket = max(slots, key=lambda key: positive[key] / slots[key])
        slots[bucket] += 1
    return slots


def _select_diverse_funds(bucket_funds: pd.DataFrame, slots: int) -> pd.DataFrame:
    if bucket_funds.empty or slots <= 0:
        return bucket_funds.head(0)

    sorted_funds = bucket_funds.sort_values("final_score", ascending=False)
    selected: list[int] = []
    used_sub_categories: set[str] = set()
    used_amcs: set[str] = set()
    used_clusters: set[object] = set()

    passes = [
        ("sub_category", "amc", "dbscan_cluster_id"),
        ("sub_category", "amc"),
        ("sub_category",),
        (),
    ]
    for required_unique in passes:
        for idx, row in sorted_funds.iterrows():
            if idx in selected:
                continue
            if "sub_category" in required_unique and str(row.get("sub_category")) in used_sub_categories:
                continue
            if "amc" in required_unique and str(row.get("amc")) in used_amcs:
                continue
            if "dbscan_cluster_id" in required_unique and row.get("dbscan_cluster_id") in used_clusters:
                continue
            selected.append(idx)
            used_sub_categories.add(str(row.get("sub_category")))
            used_amcs.add(str(row.get("amc")))
            used_clusters.add(row.get("dbscan_cluster_id"))
            if len(selected) >= slots:
                return sorted_funds.loc[selected]

    return sorted_funds.loc[selected].head(slots)


@dataclass
class RecommendationEngine:
    fund_csv_path: str | Path | None = DEFAULT_FUND_CSV

    def load_universe(self) -> pd.DataFrame:
        return impute_fund_metrics(load_funds(self.fund_csv_path or DEFAULT_FUND_CSV))

    def recommend(
        self,
        customer: CustomerProfile,
        top_n_per_bucket: int = 3,
        advisor_context_scores: dict[str, float] | None = None,
    ) -> dict[str, object]:
        funds = self.load_universe()
        risk_profile = calculate_risk_profile(customer)
        allocation_result = calculate_allocation(risk_profile.bucket, customer)
        filter_result = filter_funds(funds, customer, risk_profile.bucket, advisor_context_scores)
        scored = score_funds(filter_result.eligible, customer, risk_profile.bucket, advisor_context_scores)
        clustered, cluster_diagnostics = cluster_funds(scored)
        for column, default in {
            "fund_id": None,
            "mutual_fund_name": None,
            "category": None,
            "sub_category": None,
            "asset_bucket": None,
            "dbscan_cluster_id": None,
            "cluster_id": None,
            "is_outlier": False,
            "cluster_size": 0,
            "cluster_summary": {},
            "pca_x": None,
            "pca_y": None,
            "final_score": None,
        }.items():
            if column not in clustered.columns:
                clustered[column] = default

        recommendations: list[dict[str, object]] = []
        monthly_amount = customer.monthly_investment_amount
        bucket_slots = _fund_slots_for_allocation(
            allocation_result.allocation,
            total_slots=max(5, top_n_per_bucket * 2),
        )
        for bucket, pct in allocation_result.allocation.items():
            if pct <= 0:
                continue
            bucket_funds = clustered[clustered["asset_bucket"] == bucket].sort_values("final_score", ascending=False)
            if bucket_funds.empty:
                continue
            selected = _select_diverse_funds(bucket_funds, bucket_slots.get(bucket, 1))
            amount_per_fund = monthly_amount * pct / 100 / len(selected) if len(selected) else 0
            for _, row in selected.iterrows():
                item = row.to_dict()
                item["allocation_bucket"] = bucket
                item["allocation_pct"] = round(pct / len(selected), 2)
                item["allocation_amount_monthly"] = round(amount_per_fund, 2)
                item["explanation"] = explain_recommendation(row, customer, risk_profile.bucket)
                if bool(row.get("is_outlier", False)):
                    item["warning"] = (
                        "This fund behaves differently from most funds in the dataset. "
                        "Review manually before recommending."
                    )
                item["similar_funds"] = cosine_similar_funds(clustered, row.get("fund_id"), top_n=3)
                recommendations.append(item)

        warnings = []
        warnings.extend(risk_profile.notes)
        warnings.extend(allocation_result.warnings)
        warnings.extend(filter_result.warnings)
        warnings.extend(cluster_diagnostics.get("warnings", []))
        warnings.extend([item["warning"] for item in recommendations if item.get("warning")])

        payload = {
            "customer_risk_bucket": risk_profile.bucket,
            "risk_score": risk_profile.score,
            "raw_risk_score": risk_profile.raw_score,
            "final_risk_score": risk_profile.score,
            "risk_appetite_score": risk_profile.components.get("risk_appetite"),
            "age_score": risk_profile.components.get("age"),
            "timeline_score": risk_profile.components.get("goal_timeline_years"),
            "risk_bucket_before_cap": risk_profile.bucket_before_cap,
            "risk_bucket_after_cap": risk_profile.bucket_after_cap,
            "applied_safety_rules": risk_profile.applied_safety_rules + allocation_result.warnings,
            "risk_scale": RISK_SCALE,
            "risk_components": {k: round(v, 2) for k, v in risk_profile.components.items()},
            "advisor_context_scores": advisor_context_scores or {},
            "recommended_asset_allocation": allocation_result.allocation,
            "asset_allocation": allocation_result.allocation,
            "warnings": sorted(set(warnings)),
            "recommendations": recommendations,
            "rejected_funds": filter_result.rejected.to_dict(orient="records"),
            "cluster_diagnostics": cluster_diagnostics,
            "clustered_funds": clustered[
                [
                    "fund_id",
                    "mutual_fund_name",
                    "category",
                    "sub_category",
                    "asset_bucket",
                    "dbscan_cluster_id",
                    "cluster_id",
                    "is_outlier",
                    "cluster_size",
                    "cluster_summary",
                    "pca_x",
                    "pca_y",
                    "final_score",
                ]
            ].to_dict(orient="records"),
            "disclaimer": DISCLAIMER,
        }
        return _json_safe(payload)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat() if not pd.isna(value) else None
    if pd.isna(value) and not isinstance(value, (str, bytes, list, dict, tuple)):
        return None
    return value
