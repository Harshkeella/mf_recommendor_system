from __future__ import annotations

from dataclasses import dataclass

from .schemas import CustomerProfile


BASE_ALLOCATIONS: dict[str, dict[str, float]] = {
    "Very Aggressive": {"equity": 90.0, "debt": 10.0, "gold": 0.0},
    "Aggressive": {"equity": 70.0, "debt": 20.0, "gold": 10.0},
    "Balanced": {"equity": 50.0, "debt": 45.0, "gold": 5.0},
    "Critical": {"equity": 20.0, "debt": 75.0, "gold": 5.0},
    "Very Critical": {"equity": 5.0, "debt": 90.0, "gold": 5.0},
}


@dataclass(frozen=True)
class AllocationResult:
    allocation: dict[str, float]
    warnings: list[str]


def _cap_equity(allocation: dict[str, float], cap: float, reason: str, warnings: list[str]) -> None:
    if allocation["equity"] <= cap:
        return
    reduction = allocation["equity"] - cap
    allocation["equity"] = cap
    allocation["debt"] += reduction
    warnings.append(reason)


def _force_allocation(
    allocation: dict[str, float],
    equity: float,
    debt: float,
    gold: float,
    reason: str,
    warnings: list[str],
) -> None:
    if allocation["equity"] == equity and allocation["debt"] == debt and allocation["gold"] == gold:
        return
    allocation["equity"] = equity
    allocation["debt"] = debt
    allocation["gold"] = gold
    warnings.append(reason)


def calculate_allocation(bucket: str, customer: CustomerProfile) -> AllocationResult:
    allocation = BASE_ALLOCATIONS[bucket].copy()
    warnings: list[str] = []

    if customer.goal_timeline_years < 3:
        _cap_equity(
            allocation,
            20.0,
            "Goal timeline is below 3 years, so equity exposure is capped at 20%.",
            warnings,
        )

    if customer.emergency_fund_months <= 0:
        _cap_equity(
            allocation,
            20.0,
            "No emergency fund recorded; equity allocation is capped until liquidity is built.",
            warnings,
        )
    elif customer.emergency_fund_months < 3:
        _cap_equity(
            allocation,
            50.0,
            "Emergency fund is below 3 months; equity allocation is capped at the Balanced risk-scale level.",
            warnings,
        )

    if customer.emi_burden_ratio > 0.40:
        _cap_equity(
            allocation,
            50.0,
            "EMI burden exceeds 40% of monthly income; equity allocation is capped at the Balanced risk-scale level.",
            warnings,
        )

    if customer.age >= 50 and customer.risk_appetite in {"Very Critical", "Critical"}:
        _force_allocation(
            allocation,
            20.0,
            75.0,
            5.0,
            "Age 50+ with conservative risk appetite forces Critical allocation at maximum.",
            warnings,
        )

    if customer.need_for_early_withdrawal.lower() == "high":
        _cap_equity(
            allocation,
            20.0,
            "High early-withdrawal need caps equity allocation at 20%.",
            warnings,
        )

    if customer.risk_appetite == "Very Critical":
        _force_allocation(
            allocation,
            5.0,
            90.0,
            5.0,
            "Very Critical risk appetite forces preservation-first allocation.",
            warnings,
        )

    if customer.preferred_equity_exposure is not None:
        preferred = float(customer.preferred_equity_exposure)
        if preferred + 15 < allocation["equity"]:
            warnings.append(
                "Preferred equity exposure is materially below model allocation; advisor should validate consent."
            )
        elif preferred - 20 > allocation["equity"]:
            warnings.append(
                "Customer prefers more equity than objective capacity supports; model allocation remains conservative."
            )

    total = sum(allocation.values())
    if total != 100:
        allocation = {key: round(value / total * 100, 2) for key, value in allocation.items()}
    else:
        allocation = {key: round(value, 2) for key, value in allocation.items()}
    return AllocationResult(allocation=allocation, warnings=warnings)
